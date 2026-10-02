"""Independent first-passage, censoring, selection and chronology assertions."""
from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from backend.app import domain
from scripts.backtest_reserve import (
    EXPECTED_METHOD, FIXED_PROFILE_CONFIG, choose_config, history_at, legacy_forecast,
    operational_forecast, reserve_splits, reserve_truth, summarize,
)
from scripts.evaluate import SITE, generate


def test_fractional_reserve_truth_ignores_future_refill_and_labels_normal_whole_window():
    data = {"readings": [{"volume_l": 1000}], "truth": [
        {"consumption_l": None, "abnormal": False},
        {"consumption_l": 200, "abnormal": False},
        {"consumption_l": 400, "abnormal": False},
        {"consumption_l": 200, "abnormal": False}],
        "deliveries": [{"amount_l": 5000}]}
    result = reserve_truth(data, 0, 300, horizon=3)
    assert result["breach_hours"] == 2.5
    assert result["volumes_l"] == [800, 400, 200]
    data["deliveries"] = []
    assert reserve_truth(data, 0, 300, horizon=3) == result
    data["truth"][2]["abnormal"] = True
    assert reserve_truth(data, 0, 300, horizon=3)["normal_window"] is False
    with pytest.raises(ValueError, match="complete future horizon"):
        reserve_truth(data, 0, 300)


def test_right_censoring_is_not_invented_breach_time():
    data = {"readings": [{"volume_l": 1000}],
            "truth": [{"consumption_l": None, "abnormal": False}] + [{"consumption_l": 10, "abnormal": False}] * 3}
    assert reserve_truth(data, 0, 300, horizon=3)["breach_hours"] is None


def test_frozen_legacy_rate_plus20_percent_is_hand_calculated():
    at = datetime(2026, 10, 2, tzinfo=UTC)
    rows = [{"observed_at": (at - timedelta(hours=1)).isoformat(), "volume_l": 1200},
            {"observed_at": at.isoformat(), "volume_l": 1000}]
    result = legacy_forecast(rows, [], at, {"capacity_l": 5000, "reserve_l": 300})
    assert result["breach_hours"] == pytest.approx(700 / 240)
    assert result["volumes_l"][:2] == [760, 520]
    rows[1]["volume_l"] = 1300
    assert legacy_forecast(rows, [], at, {"capacity_l": 5000, "reserve_l": 300})["state"] == "UNKNOWN"


def test_complete48h_split_targets_never_cross_next_split_origin():
    splits = reserve_splits()
    assert len(splits["validation"]) == 119
    assert len(splits["test"]) == 120
    assert max(splits["train"]) + 48 < min(splits["validation"])
    assert max(splits["validation"]) + 48 < min(splits["test"])
    assert max(splits["test"]) + 48 == 504


def test_validation_choice_does_not_use_final_test_or_reward_missing_forecasts():
    def candidate(multiplier, late, early, unknown=0):
        return {"config": {"conservative_multiplier": multiplier},
                "validation": {"all_windows": {"windows": 10, "late_event_predictions": late,
                    "missed_horizon_events": 0, "unknown_windows": unknown, "mean_earliness_hours": early}},
                "holdout": {"late_event_predictions": 999 if multiplier == 1.1 else 0}}
    candidates = [candidate(1.0, 1, 0), candidate(1.1, 0, 3), candidate(1.2, 0, 4)]
    assert choose_config(candidates) == {"conservative_multiplier": 1.1}
    candidates[0] = candidate(1.0, 0, 0, unknown=1)
    assert choose_config(candidates) == {"conservative_multiplier": 1.1}


def test_method_or_effective_config_drift_is_rejected(monkeypatch):
    config = {**FIXED_PROFILE_CONFIG, "conservative_multiplier": 1.0}
    result = {"status": "SAFE", "method": "last_interval_rate", "forecast_config": config}
    monkeypatch.setattr(domain, "analyze", lambda *args: result)
    with pytest.raises(ValueError, match="differs from operational contract"):
        operational_forecast([], [], datetime.now(UTC), SITE, None)
    result["method"] = EXPECTED_METHOD
    result["forecast_config"] = {**config, "conservative_multiplier": 9}
    with pytest.raises(ValueError, match="differs from operational contract"):
        operational_forecast([], [], datetime.now(UTC), SITE, None)


def test_new_forecast_features_do_not_use_future_readings_truth_or_refill_decisions():
    original = generate()
    site = {**SITE, "measurement_error_l": 180, "timezone": "Asia/Kolkata"}
    before = operational_forecast(*history_at(original, 200), site, None)
    changed = deepcopy(original)
    changed["readings"][201]["volume_l"] = 0
    changed["truth"][201]["consumption_l"] = 1e8
    changed["deliveries"] = [row for row in changed["deliveries"] if row["arrived_at"] <= changed["readings"][200]["observed_at"]]
    after = operational_forecast(*history_at(changed, 200), site, None)
    assert before == after


def test_summary_keeps_unknown_and_censored_windows_out_of_exact_timing_errors():
    def row(truth, predicted, state="AVAILABLE"):
        return {"normal_window": True, "truth_breach_hours": truth, "predicted_breach_hours": predicted,
                "truth_right_censored": truth is None, "prediction_state": state,
                "timing_error_hours": predicted - truth if predicted is not None and truth is not None else None,
                "covered_hourly_points": 48 if state == "AVAILABLE" else None,
                "true_deadline_margin_hours": truth - 17 if truth is not None else None,
                "predicted_deadline_margin_hours": predicted - 17 if predicted is not None else None}
    result = summarize([row(4, 6), row(4, 3), row(7, None, "UNKNOWN"), row(None, 5)])
    assert result["windows"] == 4
    assert result["truth_reserve_events"] == 3
    assert result["truth_right_censored_windows"] == 1
    assert result["paired_evaluable_event_windows"] == 2
    assert result["unknown_windows"] == result["missed_horizon_events"] == 1
    assert result["late_event_predictions"] == 1
    assert result["mean_lateness_hours"] == 2
    assert result["mean_earliness_hours"] == 1
    assert result["unsafe_or_unavailable_event_windows"] == 2
    assert result["censored_windows_with_predicted_breach"] == 1
