"""Evaluation arithmetic, chronology, provenance and packaged-artifact invariants."""

from copy import deepcopy
from datetime import datetime
import json
import math

import pytest

from backend.app.domain import RATE_WINDOW_INTERVALS, analyze
from scripts.evaluate import ROOT, build_report, canonical, choose_window, generate, history_at, metrics, predict, split_origins


def test_metric_arithmetic_is_independently_hand_calculated():
    result = metrics([1, 3], [2, 5])
    assert result["samples"] == 2
    assert result["mae_l"] == 1.5
    assert result["rmse_l"] == pytest.approx(math.sqrt(2.5), abs=1e-6)
    assert result["bias_l"] == -1.5
    with pytest.raises(ValueError):
        metrics([], [])


def test_window_selection_uses_validation_and_shorter_tie_break():
    assert choose_window({1: {"mae_l": 8}, 3: {"mae_l": 4}, 6: {"mae_l": 4}}) == 3


def test_generation_is_reproducible_and_features_exclude_truth_and_future():
    dataset = generate()
    assert canonical(dataset) == canonical(generate())
    rows, arrivals, at = history_at(dataset, 200)
    assert len(rows) == 201
    assert all(datetime.fromisoformat(row["observed_at"]) <= at for row in rows)
    assert all(datetime.fromisoformat(row["received_at"]) <= at for row in rows)
    assert all(datetime.fromisoformat(row["arrived_at"]) <= at for row in arrivals)
    assert all("consumption_l" not in row and "abnormal" not in row for row in rows)
    before = predict(rows, arrivals, at, "recent_mean", RATE_WINDOW_INTERVALS)
    changed = deepcopy(dataset)
    changed["readings"][201]["volume_l"] = 1
    changed["truth"][201]["consumption_l"] = 999999
    changed_rows, changed_arrivals, changed_at = history_at(changed, 200)
    assert predict(changed_rows, changed_arrivals, changed_at, "recent_mean", RATE_WINDOW_INTERVALS) == before


def test_split_targets_are_disjoint_and_have_explicit_counts():
    splits = split_origins()
    assert len(splits["validation"]) == len(splits["test"]) == 166
    assert max(splits["train"]) + 1 < min(splits["validation"])
    assert max(splits["validation"]) + 1 < min(splits["test"])
    assert all(first + 1 == second for origins in splits.values() for first, second in zip(origins, origins[1:]))


def test_operational_rate_matches_evaluated_method_on_refill_history():
    dataset = generate()
    rows, arrivals, at = history_at(dataset, 200)
    result = analyze({"capacity_l": 50000, "reserve_l": 5000, "lead_hours": 14, "buffer_hours": 3, "freshness_minutes": 90}, rows, arrivals, at)
    assert result["current_rate_lph"] == pytest.approx(predict(rows, arrivals, at, "recent_mean", RATE_WINDOW_INTERVALS), abs=0.00051)


def test_generated_artifacts_reproduce_and_packaged_bytes_match():
    first = (ROOT / "artifacts" / "evaluation.json").read_bytes()
    second = (ROOT / "backend" / "app" / "data" / "evaluation.json").read_bytes()
    assert first == second
    saved = json.loads(first)
    regenerated = build_report()
    assert regenerated == saved
    assert saved["data_kind"] == "SIMULATED"
    assert saved["selection"]["matches_operational_method"] is True
    assert saved["reserve_timing"]["status"] == "not_evaluated"
    assert saved["final_test"]["recent_mean_selected"]["samples"] == 166
