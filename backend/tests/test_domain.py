"""Independent arithmetic and safety invariants for the pure water-domain module."""

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.domain import analyze, analyze_preview


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


def test_hand_computed_reserve_empty_deadline_and_physical_shortage():
    config = {**SITE, "capacity_l": 10000, "reserve_l": 1000, "lead_hours": 1, "buffer_hours": 0}
    rows = [reading(NOW - timedelta(hours=1), 4000), reading(NOW, 3000)]
    result = analyze(config, rows, [], NOW)
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
    assert result["action_margin_hours"] == 6.4375
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
    assert result["projection"][1]["volume_l"] == 27000


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
    assert result["projection"][1]["volume_l"] == 50000
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
    rows = constant_history()[:-3]
    start = rows[-1]["volume_l"]
    for offset in range(1, 4):
        rows.append(reading(NOW - timedelta(hours=3 - offset), start - 2400 * offset))
    result = analyze(SITE, rows, [], NOW)
    assert result["anomaly"]["active"] is True
    assert result["anomaly"]["evidence_count"] == 3
    assert result["anomaly"]["ratio"] == 2.5
    assert result["status"] == "ACT_NOW"
    repaired_at = NOW + timedelta(hours=3)
    base = rows[-1]["volume_l"]
    refill = supply(NOW + timedelta(hours=1), 18000, arrived=True)
    for hour in range(1, 4):
        rows.append(reading(NOW + timedelta(hours=hour), base + 18000 - 960 * hour))
    repaired = analyze(SITE, rows, [refill], repaired_at)
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
                          "uncertainty_label", "history", "projection", "shortage_hours", "unmet_demand_l", "overflow_l"}


def test_future_demand_preview_preserves_observed_history_anomaly_and_anchor():
    rows = constant_history()
    before = analyze(SITE, rows, [], NOW)
    increased = analyze_preview(SITE, rows, [], NOW, 100)
    decreased = analyze_preview(SITE, rows, [], NOW, -50)
    assert increased["history"] == decreased["history"] == before["history"]
    assert increased["anomaly"] == decreased["anomaly"] == before["anomaly"]
    assert increased["current_rate_lph"] == 1920
    assert decreased["current_rate_lph"] == 480
    assert increased["anomaly"]["observed_rate_lph"] == 960
    assert increased["projection"][0]["volume_l"] == 32000
    assert increased["projection"][1]["volume_l"] == 30080
    assert decreased["projection"][1]["volume_l"] == 31520
    assert increased["hours_to_reserve"] == 14.0625
    assert decreased["hours_to_reserve"] is None  # 56.25 h exceeds the explicit horizon.
    assert increased["method"] == "last_interval_rate_sensitivity"
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
    assert next_hour["conservative_l"] == 22200


def test_forecast_shortage_does_not_count_unobserved_hours_before_origin():
    anchor = NOW - timedelta(hours=1)
    rows = [reading(anchor - timedelta(hours=1), 1200), reading(anchor, 200)]
    result = analyze(SITE, rows, [], NOW)
    assert result["shortage_hours"] == 48
    assert result["unmet_demand_l"] == 48000
