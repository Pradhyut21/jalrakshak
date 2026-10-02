"""Independent arithmetic and safety invariants for the pure water-domain module."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from backend.app.domain import FORECAST_CONFIG, FORECAST_METHOD, analyze, analyze_preview, analyze_with_config


NOW = datetime(2026, 10, 1, 18, 0, tzinfo=UTC)
SITE = {"capacity_l": 50000, "reserve_l": 5000, "lead_hours": 14,
        "buffer_hours": 3, "freshness_minutes": 90}


def reading(at, volume, identity=None, **extra):
    return {"reading_id": identity or at.isoformat(), "observed_at": at.isoformat(),
            "volume_l": volume, "source": "synthetic_demo", "simulated": True, **extra}


def constant_history(rate=960, volume=32000):
    # Refill-free 12-hour fixture, defined from independent constant demand arithmetic.
    return [reading(NOW - timedelta(hours=hour), volume + rate * hour) for hour in range(12, -1, -1)]


def supply(at, amount, arrived=False, identity="supply-1"):
    return {"id": identity, "scheduled_at": at.isoformat(), "arrived_at": at.isoformat() if arrived else None,
            "amount_l": amount, "status": "ARRIVED" if arrived else "PLANNED"}


def point_at(result, at):
    return next(point for point in result["projection"] if point["at"] == at.isoformat())


def test_hand_computed_reserve_empty_deadline_and_physical_shortage():
    config = {**SITE, "capacity_l": 10000, "reserve_l": 1000, "lead_hours": 1, "buffer_hours": 0}
    rows = [reading(NOW - timedelta(hours=1), 4000), reading(NOW, 3000)]
    result = analyze_with_config(config, rows, [], NOW, {"conservative_multiplier": 1.2})
    assert result["reserve_breach_at"] == (NOW + timedelta(hours=2)).isoformat()
    assert result["empty_at"] == (NOW + timedelta(hours=3)).isoformat()
    assert result["conservative_breach_at"] == (NOW + timedelta(hours=5 / 3)).isoformat()
    assert result["latest_action_at"] == (NOW + timedelta(hours=2 / 3)).isoformat()
    assert result["unmet_demand_l"] == 45000
    assert result["shortage_hours"] == 45
    assert all(0 <= point["volume_l"] <= 10000 for point in result["projection"])


def test_default_healthy_conditional_supply_and_conservative_margin():
    result = analyze(SITE, constant_history(), [supply(NOW + timedelta(hours=18), 18000)], NOW)
    assert result["status"] == "SAFE"
    assert result["current_rate_lph"] == 960
    assert result["baseline_rate_lph"] == 960
    assert result["hours_to_reserve"] == 46.875
    assert result["action_margin_hours"] == 11.125
    assert result["anomaly"]["active"] is False
    assert result["shortage_hours"] == 0
    assert "not calibrated probability" in result["uncertainty_label"]


def test_unknown_inputs_are_not_fabricated_zeroes():
    result = analyze(SITE, [], [], NOW)
    assert result["status"] == "UNKNOWN"
    assert result["current_rate_lph"] is None
    assert result["unmet_demand_l"] is None
    assert result["projection"] == []
    stale = analyze(SITE, [reading(NOW - timedelta(hours=3), 34000), reading(NOW - timedelta(hours=2), 33000)], [], NOW)
    assert stale["status"] == "UNKNOWN"
    assert stale["latest_action_at"] is None


def test_out_of_order_duplicate_and_future_arrivals_preserve_latest_anchor():
    rows = constant_history()
    expected = analyze(SITE, rows, [], NOW)
    shuffled = list(reversed(rows)) + [rows[-1], reading(NOW + timedelta(hours=1), 49000)]
    shuffled.append(reading(NOW - timedelta(minutes=30), 49500, received_at=(NOW + timedelta(hours=1)).isoformat()))
    assert analyze(SITE, shuffled, [], NOW) == expected


def test_arrived_delivery_is_reconciled_in_interval_and_not_added_twice():
    rows = [reading(NOW - timedelta(hours=2), 20000), reading(NOW - timedelta(hours=1), 19000), reading(NOW, 28000)]
    delivery = supply(NOW, 10000, arrived=True)
    result = analyze(SITE, rows, [delivery, delivery], NOW)
    assert result["current_rate_lph"] == 1000
    assert result["projection"][0]["volume_l"] == 28000
    assert point_at(result, NOW + timedelta(hours=1))["volume_l"] == 27000


def test_arrival_after_measurement_is_added_once_and_consumption_still_runs():
    anchor = NOW - timedelta(hours=1)
    rows = [reading(anchor - timedelta(hours=1), 21000), reading(anchor, 20000)]
    result = analyze(SITE, rows, [supply(NOW - timedelta(minutes=30), 5000, arrived=True)], NOW)
    at_now = next(point for point in result["projection"] if point["at"] == NOW.isoformat())
    assert at_now["volume_l"] == 24000
    assert at_now["conservative_l"] == 24000


def test_planned_supply_can_overflow_but_never_exceeds_capacity():
    result = analyze(SITE, constant_history(), [supply(NOW + timedelta(hours=1), 30000)], NOW)
    # 32,000 - 960 + 30,000 = 61,040; cap 50,000; overflow 11,040.
    assert result["overflow_l"] == 11040
    assert point_at(result, NOW + timedelta(hours=1))["volume_l"] == 50000
    assert max(point["volume_l"] for point in result["projection"]) == 50000


def test_breached_reserve_is_urgent_and_zero_demand_does_not_invent_shortage():
    zero = analyze(SITE, [reading(NOW - timedelta(hours=1), 32000), reading(NOW, 32000)], [], NOW)
    assert zero["reserve_breach_at"] is None
    assert zero["empty_at"] is None
    assert zero["shortage_hours"] == 0
    assert zero["status"] == "SAFE"
    breached = analyze(SITE, [reading(NOW - timedelta(hours=1), 4500), reading(NOW, 4000)], [], NOW)
    assert breached["reserve_breach_at"] == NOW.isoformat()
    assert breached["action_margin_hours"] == -17
    assert breached["status"] == "ACT_NOW"


def test_sustained_abnormal_depletion_needs_three_intervals_and_repair_readings_clear_it():
    config = {**SITE, "capacity_l": 150000}
    rows = [reading(NOW - timedelta(hours=hour), 32000 + 960 * hour) for hour in range(72, 2, -1)]
    start = rows[-1]["volume_l"]
    for offset in range(1, 4):
        rows.append(reading(NOW - timedelta(hours=3 - offset), start - 2400 * offset))
    result = analyze(config, rows, [], NOW)
    assert result["anomaly"]["active"] is True
    assert result["anomaly"]["evidence_count"] == 3
    assert result["anomaly"]["ratio"] == 2.5
    assert result["status"] == "ACT_NOW"
    repaired_at = NOW + timedelta(hours=3)
    base = rows[-1]["volume_l"]
    refill = supply(NOW + timedelta(hours=1), 18000, arrived=True)
    for hour in range(1, 4):
        rows.append(reading(NOW + timedelta(hours=hour), base + 18000 - 960 * hour))
    repaired = analyze(config, rows, [refill], repaired_at)
    assert repaired["anomaly"]["active"] is False
    assert repaired["current_rate_lph"] == 960
    assert repaired["status"] == "SAFE"


def test_single_spike_and_gap_are_not_sustained_anomaly():
    rows = constant_history()
    rows[-1] = reading(NOW, rows[-2]["volume_l"] - 2400)
    assert analyze(SITE, rows, [], NOW)["anomaly"]["active"] is False
    gap = [reading(NOW - timedelta(hours=5), 35000), reading(NOW, 30000)]
    assert analyze(SITE, gap, [], NOW)["status"] == "UNKNOWN"


def test_unrecorded_inflow_and_possible_overflow_are_unknown():
    rows = [reading(NOW - timedelta(hours=1), 20000), reading(NOW, 30000)]
    assert analyze(SITE, rows, [], NOW)["status"] == "UNKNOWN"
    possible_spill = [reading(NOW - timedelta(hours=1), 49000), reading(NOW, 49000)]
    assert analyze(SITE, possible_spill, [supply(NOW, 5000, arrived=True)], NOW)["status"] == "UNKNOWN"


def test_cross_midnight_and_timezone_conversion_keep_elapsed_hours():
    late = datetime.fromisoformat("2026-10-02T00:30:00+05:30")
    earlier = datetime.fromisoformat("2026-10-01T23:30:00+05:30")
    result = analyze(SITE, [reading(earlier, 33000), reading(late, 32000)], [], late)
    assert result["current_rate_lph"] == 1000
    assert result["reserve_breach_at"] == (late.astimezone(UTC) + timedelta(hours=27)).isoformat()


def test_overdue_supply_does_not_materialize_and_delay_keeps_conservative_deadline():
    rows = constant_history()
    baseline = analyze(SITE, rows, [supply(NOW + timedelta(hours=18), 18000)], NOW)
    delayed = analyze(SITE, rows, [supply(NOW + timedelta(hours=24), 18000)], NOW)
    assert delayed["latest_action_at"] == baseline["latest_action_at"]
    overdue = analyze(SITE, rows, [supply(NOW - timedelta(hours=1), 18000)], NOW)
    assert overdue["supply_status"] == "OVERDUE"
    assert overdue["hours_to_reserve"] == 28.125


def test_conflicting_ids_invalid_numbers_and_naive_clock_fail_closed():
    rows = constant_history()
    conflict = {**rows[-1], "volume_l": 31000}
    assert analyze(SITE, rows + [conflict], [], NOW)["status"] == "UNKNOWN"
    invalid = {**rows[-1], "volume_l": float("nan")}
    assert analyze(SITE, rows[:-1] + [invalid], [], NOW)["status"] == "UNKNOWN"
    with pytest.raises(ValueError):
        analyze(SITE, rows, [], NOW.replace(tzinfo=None))


def test_analysis_exact_shape_and_pure_inputs():
    rows = constant_history()
    original = [dict(row) for row in rows]
    result = analyze(SITE, rows, [], NOW)
    assert rows == original
    assert set(result) == {"status", "current_rate_lph", "baseline_rate_lph", "reserve_breach_at", "empty_at",
                          "conservative_breach_at", "latest_action_at", "hours_to_reserve", "action_margin_hours",
                          "next_supply_at", "supply_status", "anomaly", "recommendation", "facts", "method",
                          "uncertainty_label", "history", "projection", "shortage_hours", "unmet_demand_l", "overflow_l",
                          "forecast_description", "forecast_assumptions", "forecast_config", "demand_profile",
                          "sufficient_forecast_history", "measurement_bounds"}


def test_future_demand_preview_preserves_observed_history_anomaly_and_anchor():
    rows = constant_history()
    before = analyze(SITE, rows, [], NOW)
    increased = analyze_preview(SITE, rows, [], NOW, 100)
    decreased = analyze_preview(SITE, rows, [], NOW, -50)
    assert increased["history"] == decreased["history"] == before["history"]
    assert increased["anomaly"] == decreased["anomaly"] == before["anomaly"]
    assert increased["current_rate_lph"] == decreased["current_rate_lph"] == 960
    assert increased["anomaly"]["observed_rate_lph"] == 960
    assert increased["projection"][0]["volume_l"] == 32000
    assert point_at(increased, NOW + timedelta(hours=1))["volume_l"] == 30080
    assert point_at(decreased, NOW + timedelta(hours=1))["volume_l"] == 31520
    assert increased["hours_to_reserve"] == 14.0625
    assert decreased["hours_to_reserve"] is None  # 56.25 h exceeds the explicit horizon.
    assert increased["method"] == FORECAST_METHOD + "_sensitivity"
    assert any("Observed history and anomaly evidence are unchanged" in fact for fact in increased["facts"])
    with pytest.raises(ValueError):
        analyze_preview(SITE, rows, [], NOW, 101)


def test_preview_does_not_rewrite_gap_since_last_observation():
    anchor = NOW - timedelta(hours=1)
    rows = [reading(anchor - timedelta(hours=1), 21000), reading(anchor, 20000)]
    inflow = supply(NOW - timedelta(minutes=30), 5000, arrived=True)
    result = analyze_preview(SITE, rows, [inflow], NOW, 50)
    at_now = next(point for point in result["projection"] if point["at"] == NOW.isoformat())
    next_hour = next(point for point in result["projection"] if point["at"] == (NOW + timedelta(hours=1)).isoformat())
    assert at_now["volume_l"] == at_now["conservative_l"] == 24000
    assert next_hour["volume_l"] == 22500
    assert next_hour["conservative_l"] == 22500


def test_forecast_shortage_does_not_count_unobserved_hours_before_origin():
    anchor = NOW - timedelta(hours=1)
    rows = [reading(anchor - timedelta(hours=1), 1200), reading(anchor, 200)]
    result = analyze(SITE, rows, [], NOW)
    assert result["shortage_hours"] == 48
    assert result["unmet_demand_l"] == 48000


def profiled_history(now, hourly_rate, *, local_zone=UTC, step_minutes=60, volume=10000):
    """Independent backward integration for an exactly repeating observed day."""
    rows = [reading(now, volume)]
    for step in range(1, 72 * 60 // step_minutes + 1):
        at = now - timedelta(minutes=step * step_minutes)
        volume += hourly_rate(at.astimezone(local_zone).hour) * step_minutes / 60
        rows.append(reading(at, volume))
    return list(reversed(rows))


def test_time_of_day_history_anticipates_next_morning_peak_instead_of_extending_night_rate():
    rows = profiled_history(NOW, lambda hour: 2000 if 6 <= hour < 9 else 200)
    config = {**SITE, "timezone": "UTC", "lead_hours": 1, "buffer_hours": 0}
    result = analyze(config, rows, [], NOW)
    # Twelve quiet hours consume 2,400 L, then 2,600 L takes 1.3 peak hours.
    assert result["current_rate_lph"] == 200
    assert result["reserve_breach_at"] == (NOW + timedelta(hours=13.3)).isoformat()
    assert result["conservative_breach_at"] == result["reserve_breach_at"]
    assert result["hours_to_reserve"] < 5000 / (200 * 1.2)  # Old +20% constant warning was late.
    assert result["demand_profile"][6]["rate_lph"] == 2000
    assert result["demand_profile"][18]["rate_lph"] == 200
    assert result["sufficient_forecast_history"] is True
    assert result["forecast_config"] == FORECAST_CONFIG
    assert result["method"] == FORECAST_METHOD
    assert all(row["upper_rate_lph"] >= row["rate_lph"] for row in result["demand_profile"])


def test_india_profile_splits_at_half_hour_utc_boundary_and_interpolates_consumption():
    india = timezone(timedelta(hours=5, minutes=30))
    rows = profiled_history(NOW, lambda hour: 2100 if hour == 0 else 100,
                            local_zone=india, step_minutes=30)
    result = analyze({**SITE, "reserve_l": 1000}, rows, [], NOW)
    midnight = NOW + timedelta(minutes=30)  # 00:00 Asia/Kolkata, 18:30 UTC.
    assert point_at(result, midnight)["volume_l"] == 9950
    assert point_at(result, NOW + timedelta(hours=1))["volume_l"] == 8900
    assert result["demand_profile"][0]["rate_lph"] == 2100
    assert result["demand_profile"][23]["rate_lph"] == 100


def test_declared_measurement_error_tolerates_only_bounded_rise_and_keeps_positive_upper_risk():
    config = {**SITE, "capacity_l": 10000, "reserve_l": 2000, "lead_hours": 0,
              "buffer_hours": 0, "measurement_error_l": 100}
    rows = [reading(NOW - timedelta(hours=1), 2200), reading(NOW, 2300)]
    result = analyze(config, rows, [], NOW)
    # Apparent consumption -100 +/- 200 L permits [0,100], never unlimited inflow.
    assert result["current_rate_lph"] == 0
    assert result["measurement_bounds"]["latest_rate_lower_lph"] == 0
    assert result["measurement_bounds"]["latest_rate_upper_lph"] == 100
    assert result["measurement_bounds"]["latest_storage_lower_l"] == 2200
    assert result["conservative_breach_at"] == (NOW + timedelta(hours=2)).isoformat()
    assert result["status"] == "WATCH"
    assert result["sufficient_forecast_history"] is False
    assert any("operator assumption" in fact for fact in result["facts"])
    assert analyze(config, [rows[0], reading(NOW, 2401)], [], NOW)["status"] == "UNKNOWN"
    assert analyze({**config, "measurement_error_l": 0}, rows, [], NOW)["status"] == "UNKNOWN"


def test_measurement_error_bounds_both_rate_and_conservative_start_volume():
    config = {**SITE, "capacity_l": 20000, "reserve_l": 1000, "measurement_error_l": 100}
    rows = [reading(NOW - timedelta(hours=1), 10000), reading(NOW, 9000)]
    result = analyze(config, rows, [], NOW)
    assert result["measurement_bounds"]["latest_rate_lower_lph"] == 800
    assert result["measurement_bounds"]["latest_rate_upper_lph"] == 1200
    assert result["projection"][0]["conservative_l"] == 8900
    assert result["conservative_breach_at"] == (NOW + timedelta(hours=7900 / 1200)).isoformat()
    assert result["history"][-1]["volume_l"] == 9000


def test_conservative_measurement_error_also_applies_to_unobserved_gap_without_preview_rewriting_it():
    config = {**SITE, "capacity_l": 20000, "reserve_l": 1000, "measurement_error_l": 100}
    anchor = NOW - timedelta(hours=1)
    rows = [reading(anchor - timedelta(hours=1), 10000), reading(anchor, 9000)]
    before = analyze(config, rows, [], NOW)
    preview = analyze_preview(config, rows, [], NOW, 100)
    current = point_at(before, NOW)
    assert current["volume_l"] == 8000
    assert current["conservative_l"] == 7700  # 9,000 - 100 storage error - 1,200 upper demand.
    assert point_at(preview, NOW) == current
    assert point_at(preview, NOW + timedelta(hours=1))["conservative_l"] == 5300


def test_supported_daily_profile_and_preview_never_consume_unavailable_future_evidence():
    rows = profiled_history(NOW, lambda hour: 1400 if 6 <= hour < 9 else 300)
    config = {**SITE, "timezone": "UTC"}
    before = analyze(config, rows, [], NOW)
    future = reading(NOW + timedelta(hours=1), 100, "unavailable-future")
    late_receipt = reading(NOW - timedelta(minutes=30), 20000, "unavailable-late-receipt",
                           received_at=(NOW + timedelta(hours=1)).isoformat())
    future_delivery = {**supply(NOW, 30000, arrived=True), "received_at": (NOW + timedelta(hours=1)).isoformat()}
    assert analyze(config, rows + [future, late_receipt], [future_delivery], NOW) == before
    increased = analyze_preview(config, rows, [], NOW, 50)
    assert increased["history"] == before["history"]
    assert increased["anomaly"] == before["anomaly"]
    assert increased["demand_profile"] == before["demand_profile"]
    for point in increased["projection"]:
        assert all(0 <= point[key] <= config["capacity_l"]
                   for key in ("volume_l", "conservative_l", "optimistic_l"))


def test_invalid_profile_settings_or_error_bounds_are_rejected_and_sparse_history_declared():
    rows = constant_history()
    result = analyze(SITE, rows, [], NOW)
    assert result["sufficient_forecast_history"] is False
    assert any("Daily-profile history is limited" in fact for fact in result["facts"])
    for config in ({"upper_quantile": 1.1}, {"conservative_multiplier": 0.9},
                   {"lookback_hours": float("nan")}, {"surprise": True}):
        with pytest.raises(ValueError):
            analyze_with_config(SITE, rows, [], NOW, config)
    for extra in ({"measurement_error_l": -1}, {"timezone": "unknown/timezone"}):
        with pytest.raises(ValueError):
            analyze({**SITE, **extra}, rows, [], NOW)


def test_inspection_recommendation_explains_usage_review_instead_of_supply_boilerplate():
    rows = constant_history()[:-3]
    volume = rows[-1]["volume_l"]
    for number in range(1, 4):
        rows.append(reading(NOW - timedelta(hours=3 - number), volume - 2400 * number))
    result = analyze({**SITE, "lead_hours": 0, "buffer_hours": 0}, rows, [], NOW)
    assert result["recommendation"]["type"] == "INSPECT_USAGE"
    body = result["recommendation"]["body"]
    assert "site-level usage" in body
    assert "inlet/outlet records" in body
    assert "does not confirm or locate a physical leak" in body
    assert "assumptions" in body
