"""Deterministic, measurement-anchored water analysis; no scenario truth or I/O."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import math
from statistics import median
from typing import Any


HORIZON_HOURS = 48
# Frozen from synthetic validation only; the three-interval anomaly gate is separate.
RATE_WINDOW_INTERVALS = 1
SENSITIVITY_LABEL = "Sensitivity envelope: demand ±20%; not calibrated probability"


def _time(value: Any) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamps must include a timezone")
    return result.astimezone(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


def _number(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("A boolean is not a water quantity")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Water quantities must be finite")
    return result


def _supplies(deliveries: list[dict], now: datetime) -> tuple[list[dict], bool]:
    """Consume each stable delivery ID once; conflicting ledger rows fail closed."""
    seen: dict[str, dict] = {}
    invalid = False
    for row in deliveries:
        try:
            amount = _number(row["amount_l"])
            if amount < 0:
                raise ValueError("Negative inflow")
            arrived = _time(row["arrived_at"]) if row.get("arrived_at") else None
            scheduled = _time(row["scheduled_at"]) if row.get("scheduled_at") else None
            known_at = _time(row["received_at"]) if row.get("received_at") else None
            if known_at is not None and known_at > now:
                continue
            item = {"id": str(row["id"]), "amount_l": amount, "arrived_at": arrived,
                    "scheduled_at": scheduled, "status": str(row.get("status", "PLANNED")).upper()}
            if not item["id"]:
                raise ValueError("Missing delivery ID")
            if item["id"] in seen and seen[item["id"]] != item:
                invalid = True
            else:
                seen[item["id"]] = item
        except (KeyError, ValueError, TypeError, OverflowError):
            invalid = True
    return list(seen.values()), invalid


def _observations(readings: list[dict], now: datetime, capacity: float) -> tuple[list[dict], bool]:
    seen: dict[str, dict] = {}
    invalid = False
    for row in readings:
        try:
            at = _time(row["observed_at"])
            received = _time(row.get("received_at") or row["observed_at"])
            if at > now or received > now:
                continue  # Information unavailable at this origin never enters features.
            volume = _number(row["volume_l"])
            if not 0 <= volume <= capacity:
                raise ValueError("Reading outside capacity")
            item = {"id": str(row["reading_id"]), "at": at, "volume_l": volume,
                    "source": str(row.get("source", "unknown")), "simulated": bool(row.get("simulated", False))}
            if not item["id"]:
                raise ValueError("Missing reading ID")
            if item["id"] in seen and seen[item["id"]] != item:
                invalid = True
            else:
                seen[item["id"]] = item
        except (KeyError, ValueError, TypeError, OverflowError):
            invalid = True
    ordered = sorted(seen.values(), key=lambda row: (row["at"], row["id"]))
    unique: list[dict] = []
    for row in ordered:
        if unique and row["at"] == unique[-1]["at"]:
            if row["volume_l"] != unique[-1]["volume_l"]:
                invalid = True
            continue
        unique.append(row)
    return unique, invalid


def _intervals(rows: list[dict], supplies: list[dict], capacity: float, max_gap: float) -> list[dict]:
    result: list[dict] = []
    for previous, current in zip(rows, rows[1:]):
        hours = (current["at"] - previous["at"]).total_seconds() / 3600
        inflow = sum(item["amount_l"] for item in supplies
                     if item["arrived_at"] is not None and previous["at"] < item["arrived_at"] <= current["at"])
        depleted = previous["volume_l"] + inflow - current["volume_l"]
        # If overflow may have occurred, level changes cannot distinguish spill from consumption.
        identifiable = 0 < hours <= max_gap and depleted >= 0 and previous["volume_l"] + inflow <= capacity
        result.append({"start": previous["at"], "at": current["at"], "hours": hours,
                       "rate": depleted / hours if identifiable else None})
    return result


def _project(anchor: datetime, volume: float, rate: float, reserve: float, capacity: float,
             times: list[datetime], inflows: list[tuple[datetime, float]], *,
             origin: datetime | None = None, observed_rate: float | None = None) -> dict:
    by_time: dict[datetime, float] = {}
    for at, amount in inflows:
        by_time[at] = by_time.get(at, 0.0) + amount
    breach = anchor if volume <= reserve else None
    empty = anchor if volume == 0 else None
    unmet = overflow = shortage = 0.0
    points = [{"at": _iso(anchor), "volume_l": volume}]
    previous = anchor
    for at in times[1:]:
        duration = (at - previous).total_seconds() / 3600
        # ``origin`` is present in the grid: preview assumptions affect future
        # demand only, not the inferred gap from the last measurement to now.
        segment_rate = observed_rate if origin is not None and at <= origin and observed_rate is not None else rate
        if segment_rate > 0:
            if breach is None and volume > reserve and (volume - reserve) / segment_rate <= duration:
                breach = previous + timedelta(hours=(volume - reserve) / segment_rate)
            if empty is None and volume > 0 and volume / segment_rate <= duration:
                empty = previous + timedelta(hours=volume / segment_rate)
            deficit = max(0.0, segment_rate * duration - volume)
            if origin is None or previous >= origin:
                unmet += deficit
                shortage += deficit / segment_rate
            volume = max(0.0, volume - segment_rate * duration)
        inflow = by_time.get(at, 0.0)
        if origin is None or at > origin:
            overflow += max(0.0, volume + inflow - capacity)
        volume = min(capacity, volume + inflow)
        points.append({"at": _iso(at), "volume_l": round(volume, 3)})
        previous = at
    return {"points": points, "breach": breach, "empty": empty,
            "shortage": shortage, "unmet": unmet, "overflow": overflow}


def _unknown(reason: str, history: list[dict], supply_at: datetime | None, supply_status: str,
             baseline: float | None = None) -> dict:
    return {
        "status": "UNKNOWN", "current_rate_lph": None, "baseline_rate_lph": baseline,
        "reserve_breach_at": None, "empty_at": None, "conservative_breach_at": None,
        "latest_action_at": None, "hours_to_reserve": None, "action_margin_hours": None,
        "next_supply_at": _iso(supply_at), "supply_status": supply_status,
        "anomaly": {"active": False, "observed_rate_lph": None, "expected_rate_lph": baseline,
                    "ratio": None, "evidence_count": 0, "reason": "Depletion cannot be verified: " + reason},
        "recommendation": {"type": "REFRESH_READING", "title": "Verify the tank reading",
                           "body": reason + " Risk is unknown; missing data is not safe.", "deadline": None},
        "facts": [reason, "No operational safety conclusion is available."], "method": "unavailable",
        "uncertainty_label": SENSITIVITY_LABEL, "history": history, "projection": [],
        "shortage_hours": None, "unmet_demand_l": None, "overflow_l": None,
    }


def _analyze(site: dict, readings: list[dict], deliveries: list[dict], now: datetime,
             *, projection_multiplier: float = 1.0) -> dict:
    """Return the API v1 analysis object using only observations available at ``now``.

    Arrivals in (previous observation, current observation] inform past consumption.
    Forecast inflows start strictly after the latest measurement, preventing refill
    double counting. Planned supply is conditional in the central/optimistic paths;
    the conservative path excludes it. Forecast metrics refer to the central path.
    """
    now = _time(now)
    capacity = _number(site["capacity_l"])
    reserve = _number(site["reserve_l"])
    lead = _number(site.get("lead_hours", 0))
    buffer = _number(site.get("buffer_hours", 0))
    freshness = _number(site.get("freshness_minutes", 90))
    max_gap = _number(site.get("max_interval_hours", 3))
    if capacity <= 0 or not 0 <= reserve < capacity or min(lead, buffer, freshness, max_gap) < 0 or max_gap == 0:
        raise ValueError("Invalid capacity, reserve, lead time, freshness or interval setting")
    supplies, bad_supply = _supplies(deliveries, now)
    rows, bad_reading = _observations(readings, now, capacity)
    future = sorted((item for item in supplies if item["arrived_at"] is None
                     and item["scheduled_at"] is not None and item["status"] in {"PLANNED", "CONFIRMED", "DELAYED"}),
                    key=lambda item: item["scheduled_at"])
    pending = [item for item in future if item["scheduled_at"] >= now]
    next_item = pending[0] if pending else (future[-1] if future else None)
    supply_at = next_item["scheduled_at"] if next_item else None
    arrived = [item for item in supplies if item["arrived_at"] is not None and item["arrived_at"] <= now]
    supply_status = ("OVERDUE" if supply_at is not None and supply_at < now else "PLANNED") if next_item else ("ARRIVED" if arrived else "ABSENT")
    intervals = _intervals(rows, arrived, capacity, max_gap)
    rates = {interval["at"]: interval["rate"] for interval in intervals}
    history = [{"at": _iso(row["at"]), "volume_l": row["volume_l"], "rate_lph": rates.get(row["at"])}
               for row in rows if row["at"] >= now - timedelta(hours=48)]
    historical_rates = [interval["rate"] for interval in intervals
                        if interval["at"] <= now - timedelta(hours=4) and interval["rate"] is not None]
    baseline = float(median(historical_rates)) if historical_rates else None
    if bad_supply or bad_reading:
        return _unknown("Invalid or conflicting reading/inflow ledger.", history, supply_at, supply_status, baseline)
    if not rows:
        return _unknown("No reading is available at this analysis time.", history, supply_at, supply_status, baseline)
    latest = rows[-1]
    age = (now - latest["at"]).total_seconds() / 60
    if age > freshness:
        return _unknown(f"Latest observation is {age:.0f} minutes old; freshness limit is {freshness:g} minutes.", history, supply_at, supply_status, baseline)
    if not intervals or intervals[-1]["rate"] is None:
        return _unknown("Recent demand is insufficient or ambiguous (gap, unknown inflow, or possible overflow).", history, supply_at, supply_status, baseline)
    recent = intervals[-3:]
    valid = [interval for interval in intervals[-RATE_WINDOW_INTERVALS:] if interval["rate"] is not None]
    rate = sum(item["rate"] * item["hours"] for item in valid) / sum(item["hours"] for item in valid)
    high = [item for item in recent if item["rate"] is not None and baseline is not None and item["rate"] > baseline * 1.5]
    active = baseline is not None and len(recent) == 3 and len(high) == 3
    ratio = rate / baseline if baseline is not None and baseline > 0 else None
    if active:
        anomaly_reason = "Three consecutive observed intervals exceed 1.5× the earlier median. This is abnormal depletion, not a confirmed leak."
    elif baseline is None:
        anomaly_reason = "Earlier baseline history is insufficient; no sustained-anomaly conclusion."
    else:
        anomaly_reason = f"{len(high)} of the last three intervals exceed 1.5× the earlier median; three consecutive intervals are required."

    anchor = latest["at"]
    end = now + timedelta(hours=HORIZON_HOURS)
    actual_inflows = [(item["arrived_at"], item["amount_l"]) for item in arrived if anchor < item["arrived_at"] <= end]
    conditional = [(item["scheduled_at"], item["amount_l"]) for item in pending if anchor < item["scheduled_at"] <= end]
    grid = {anchor, now, end}
    grid.update(now + timedelta(hours=hour) for hour in range(1, HORIZON_HOURS + 1))
    grid.update(at for at, _ in actual_inflows + conditional)
    times = sorted(at for at in grid if at >= anchor)
    future_rate = rate * projection_multiplier
    central = _project(anchor, latest["volume_l"], future_rate, reserve, capacity, times, actual_inflows + conditional,
                       origin=now, observed_rate=rate)
    conservative = _project(anchor, latest["volume_l"], future_rate * 1.2, reserve, capacity, times, actual_inflows,
                            origin=now, observed_rate=rate)
    optimistic = _project(anchor, latest["volume_l"], future_rate * 0.8, reserve, capacity, times, actual_inflows + conditional,
                          origin=now, observed_rate=rate)
    deadline = conservative["breach"] - timedelta(hours=lead + buffer) if conservative["breach"] is not None else None
    margin = (deadline - now).total_seconds() / 3600 if deadline is not None else None
    status = "ACT_NOW" if active or (margin is not None and margin <= 0) else ("WATCH" if margin is not None and margin <= 4 else "SAFE")
    kind = "INSPECT_USAGE" if active and (margin is None or margin > 0) else ("REQUEST_SUPPLY" if status in {"WATCH", "ACT_NOW"} else "MONITOR")
    title = {"INSPECT_USAGE": "Inspect sustained abnormal depletion", "REQUEST_SUPPLY": "Review an additional supply request", "MONITOR": "Monitor tank and planned supply"}[kind]
    body = ("The conservative supply deadline has passed; review supply and inspect usage now." if margin is not None and margin <= 0
            else "The next supply is conditional. Confirm availability and keep readings current; a notification is not a booking or repair.")
    facts = [f"Latest measured storage is {latest['volume_l']:g} L; reserve is {reserve:g} L.",
             f"Recent inferred demand is {rate:.1f} L/h; arrived inflow is reconciled once.",
             f"Source is {latest['source']}; observation age is {age:.0f} minutes; {'simulated' if latest['simulated'] else 'manual/observed'} provenance.",
             "Central projection includes conditional planned supply; conservative projection excludes it and assumes 20% higher demand.",
             "Consumption assumes the arrived-inflow ledger is complete; aggregate tank data cannot locate a leak."]
    if central["breach"] is None:
        facts.append("No central reserve breach within the 48-hour modeled horizon; this is not an unlimited guarantee.")
    if supply_status == "OVERDUE":
        facts.append("Planned supply is overdue and was not added as arrived water.")
    if projection_multiplier != 1:
        facts.append(f"Preview assumption only: future demand changes by {(projection_multiplier - 1) * 100:+g}% to {future_rate:.1f} L/h. Observed history and anomaly evidence are unchanged.")
    projection = [{"at": point["at"], "volume_l": point["volume_l"],
                   "conservative_l": conservative["points"][index]["volume_l"],
                   "optimistic_l": optimistic["points"][index]["volume_l"]}
                  for index, point in enumerate(central["points"])]
    return {
        "status": status, "current_rate_lph": round(future_rate, 3), "baseline_rate_lph": round(baseline, 3) if baseline is not None else None,
        "reserve_breach_at": _iso(central["breach"]), "empty_at": _iso(central["empty"]),
        "conservative_breach_at": _iso(conservative["breach"]), "latest_action_at": _iso(deadline),
        "hours_to_reserve": round((central["breach"] - now).total_seconds() / 3600, 6) if central["breach"] is not None else None,
        "action_margin_hours": round(margin, 6) if margin is not None else None,
        "next_supply_at": _iso(supply_at), "supply_status": supply_status,
        "anomaly": {"active": active, "observed_rate_lph": round(rate, 3), "expected_rate_lph": round(baseline, 3) if baseline is not None else None,
                    "ratio": round(ratio, 3) if ratio is not None else None, "evidence_count": len(high), "reason": anomaly_reason},
        "recommendation": {"type": kind, "title": title, "body": body, "deadline": _iso(deadline)},
        "facts": facts, "method": "last_interval_rate" if projection_multiplier == 1 else "last_interval_rate_sensitivity", "uncertainty_label": SENSITIVITY_LABEL,
        "history": history, "projection": projection, "shortage_hours": round(central["shortage"], 6),
        "unmet_demand_l": round(central["unmet"], 3), "overflow_l": round(central["overflow"], 3),
    }


def analyze(site: dict, readings: list[dict], deliveries: list[dict], now: datetime) -> dict:
    """Analyze unchanged observed evidence using the API v1 interface."""
    return _analyze(site, readings, deliveries, now)


def analyze_preview(site: dict, readings: list[dict], deliveries: list[dict], now: datetime,
                    demand_change_percent: float = 0) -> dict:
    """Preview bounded future demand without fabricating historical readings.

    Supply changes are represented by the caller's separate copied delivery list.
    Historical baseline and anomaly evidence remain observed facts. In the
    returned preview, current_rate_lph is the assumed scenario rate; the actual
    inferred rate remains in anomaly.observed_rate_lph and the fact list. The
    extra assumption appears in facts and the method label.
    """
    percent = _number(demand_change_percent)
    if not -50 <= percent <= 100:
        raise ValueError("Demand preview must be between -50% and +100%")
    return _analyze(site, readings, deliveries, now, projection_multiplier=1 + percent / 100)
