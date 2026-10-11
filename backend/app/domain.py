"""Deterministic, measurement-anchored water analysis; no scenario truth or I/O."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
import math
from statistics import median
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


HORIZON_HOURS = 48
# Frozen from synthetic validation only; the three-interval anomaly gate is separate.
RATE_WINDOW_INTERVALS = 1
FORECAST_METHOD = "time_of_day_empirical_envelope"
FORECAST_CONFIG = {"lookback_hours": 168, "upper_quantile": 0.9,
                   "minimum_bucket_hours": 2, "conservative_multiplier": 1.0}
SENSITIVITY_LABEL = "Observed-history planning envelope and lower-demand sensitivity; not calibrated probability"


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


def _intervals(rows: list[dict], supplies: list[dict], capacity: float, max_gap: float,
               measurement_error: float = 0) -> list[dict]:
    result: list[dict] = []
    for previous, current in zip(rows, rows[1:]):
        hours = (current["at"] - previous["at"]).total_seconds() / 3600
        inflow = sum(item["amount_l"] for item in supplies
                     if item["arrived_at"] is not None and previous["at"] < item["arrived_at"] <= current["at"])
        depleted = previous["volume_l"] + inflow - current["volume_l"]
        # If overflow may have occurred, level changes cannot distinguish spill from consumption.
        # Each reading may differ from storage by +/- the declared error. Thus
        # interval consumption is bounded by depleted +/- twice that error.
        # A larger apparent rise remains unexplained inflow, never free water.
        identifiable = (0 < hours <= max_gap and math.isfinite(depleted) and math.isfinite(2 * measurement_error)
                        and depleted >= -2 * measurement_error
                        and (inflow == 0 or previous["volume_l"] + inflow + measurement_error <= capacity))
        if identifiable and not math.isfinite(max(0.0, depleted + 2 * measurement_error) / hours):
            identifiable = False
        result.append({"start": previous["at"], "at": current["at"], "hours": hours,
                       "rate": max(0.0, depleted) / hours if identifiable else None,
                       "rate_lower": max(0.0, depleted - 2 * measurement_error) / hours if identifiable else None,
                       "rate_upper": max(0.0, depleted + 2 * measurement_error) / hours if identifiable else None})
    return result


def _site_timezone(name: str):
    # The prototype supports these fixed-offset zones without an unbundled
    # OS timezone database (Windows has none). India has no seasonal offset.
    if name in {"Asia/Kolkata", "Asia/Calcutta"}:
        return timezone(timedelta(hours=5, minutes=30), "Asia/Kolkata")
    if name in {"UTC", "Etc/UTC"}:
        return UTC
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Timezone unavailable; Asia/Kolkata and UTC need no timezone database") from error


def _next_local_hour(at: datetime, local_zone) -> datetime:
    local = at.astimezone(local_zone)
    return (local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).astimezone(UTC)


def _weighted_quantile(samples: list[tuple[float, float]], quantile: float) -> float:
    ordered = sorted(samples)
    threshold = sum(weight for _, weight in ordered) * quantile
    cumulative = 0.0
    for index, (value, weight) in enumerate(ordered):
        cumulative += weight
        if cumulative >= threshold:
            if quantile == 0.5 and math.isclose(cumulative, threshold) and index + 1 < len(ordered):
                return (value + ordered[index + 1][0]) / 2
            return value
    return ordered[-1][0]


def _forecast_config(overrides: dict | None) -> dict:
    config = {**FORECAST_CONFIG, **(overrides or {})}
    if set(config) != set(FORECAST_CONFIG):
        raise ValueError("Unsupported forecast configuration")
    config = {key: _number(value) for key, value in config.items()}
    if (not 24 <= config["lookback_hours"] <= 720 or not 0.5 <= config["upper_quantile"] <= 1
            or not 0 < config["minimum_bucket_hours"] <= 24
            or not 1 <= config["conservative_multiplier"] <= 2):
        raise ValueError("Invalid forecast configuration")
    return config


def _demand_profile(intervals: list[dict], now: datetime, local_zone, config: dict,
                    recent_rate: float, recent_upper: float) -> list[dict]:
    cutoff = now - timedelta(hours=4)
    start = now - timedelta(hours=config["lookback_hours"])
    eligible = [row for row in intervals if row["rate"] is not None and row["at"] <= cutoff and row["at"] > start]
    central_samples: list[list[tuple[float, float]]] = [[] for _ in range(24)]
    upper_samples: list[list[tuple[float, float]]] = [[] for _ in range(24)]
    all_central: list[tuple[float, float]] = []
    all_upper: list[tuple[float, float]] = []
    for row in eligible:
        previous = max(start, row["start"])
        while previous < row["at"]:
            at = min(row["at"], _next_local_hour(previous, local_zone))
            weight = (at - previous).total_seconds() / 3600
            hour = previous.astimezone(local_zone).hour
            central_samples[hour].append((row["rate"], weight))
            upper_samples[hour].append((row["rate_upper"], weight))
            all_central.append((row["rate"], weight))
            all_upper.append((row["rate_upper"], weight))
            previous = at
    fallback = _weighted_quantile(all_central, 0.5) if all_central else recent_rate
    fallback_upper = _weighted_quantile(all_upper, config["upper_quantile"]) if all_upper else recent_upper
    profile = []
    for hour in range(24):
        hours = sum(weight for _, weight in central_samples[hour])
        supported = hours >= config["minimum_bucket_hours"]
        rate = _weighted_quantile(central_samples[hour], 0.5) if supported else fallback
        upper = _weighted_quantile(upper_samples[hour], config["upper_quantile"]) if supported else fallback_upper
        profile.append({"local_hour": hour, "rate_lph": rate, "upper_rate_lph": max(rate, upper),
                        "observed_hours": round(hours, 6), "supported": supported})
    return profile


def _project(anchor: datetime, volume: float, rate: float | Callable[[datetime], float], reserve: float, capacity: float,
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
        segment_rate = (observed_rate if origin is not None and at <= origin and observed_rate is not None
                        else rate(previous) if callable(rate) else rate)
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
             baseline: float | None = None, *, config: dict | None = None,
             measurement_error: float = 0) -> dict:
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
        "forecast_description": "Demand projection unavailable until the observation and inflow evidence is usable.",
        "forecast_assumptions": ["Missing or ambiguous evidence cannot support an operational safety conclusion."],
        "forecast_config": config or _forecast_config(None), "demand_profile": [],
        "sufficient_forecast_history": False,
        "measurement_bounds": {"per_reading_l": measurement_error, "latest_rate_lower_lph": None,
                               "latest_rate_upper_lph": None, "latest_storage_lower_l": None,
                               "latest_storage_upper_l": None},
    }


def _analyze(site: dict, readings: list[dict], deliveries: list[dict], now: datetime,
             *, projection_multiplier: float = 1.0, forecast_config: dict | None = None) -> dict:
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
    measurement_error = _number(site.get("measurement_error_l", 0))
    zone_name = str(site.get("timezone", "Asia/Kolkata"))
    local_zone = _site_timezone(zone_name)
    config = _forecast_config(forecast_config)
    if (capacity <= 0 or not 0 <= reserve < capacity or min(lead, buffer, freshness, max_gap, measurement_error) < 0
            or max_gap == 0 or measurement_error > capacity):
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
    intervals = _intervals(rows, arrived, capacity, max_gap, measurement_error)
    rates = {interval["at"]: interval["rate"] for interval in intervals}
    history = [{"at": _iso(row["at"]), "volume_l": row["volume_l"], "rate_lph": rates.get(row["at"])}
               for row in rows if row["at"] >= now - timedelta(hours=48)]
    historical_rates = [interval["rate"] for interval in intervals
                        if interval["at"] <= now - timedelta(hours=4) and interval["rate"] is not None]
    baseline = float(median(historical_rates)) if historical_rates else None
    requires_declaration = site.get("require_measurement_error_declaration") is True
    error_basis = site.get("measurement_error_basis")
    declaration_complete = (measurement_error > 0 and isinstance(error_basis, str)
                            and bool(error_basis.replace("\ufeff", "").strip()))
    calibration_note = (f"Declared per-reading error: ±{measurement_error:g} L. Operator-entered basis: {error_basis}. "
                        "Declaration is not calibration; an understated bound can produce late warnings. "
                        "A tank-level log alone cannot establish a reliable sensor-error bound.")
    def unknown(reason: str) -> dict:
        result = _unknown(reason, history, supply_at, supply_status, baseline,
                          config=config, measurement_error=measurement_error)
        if requires_declaration and declaration_complete:
            result["facts"].append(calibration_note)
            result["forecast_assumptions"].append(calibration_note)
        return result
    if requires_declaration and not declaration_complete:
        result = unknown("Declare a positive per-reading error bound in litres and its basis in Data & settings. Older saved defaults are not an explicit declaration; existing records are retained.")
        result["recommendation"].update(type="CONFIGURE_SITE", title="Declare the reading-error bound")
        return result
    if bad_supply or bad_reading:
        return unknown("Invalid or conflicting reading/inflow ledger.")
    if not rows:
        return unknown("No reading is available at this analysis time.")
    latest = rows[-1]
    age = (now - latest["at"]).total_seconds() / 60
    if age > freshness:
        return unknown(f"Latest observation is {age:.0f} minutes old; freshness limit is {freshness:g} minutes.")
    if not intervals or intervals[-1]["rate"] is None:
        return unknown("Recent demand is insufficient or ambiguous (gap, unknown inflow, or possible overflow).")
    recent = intervals[-3:]
    valid = [interval for interval in intervals[-RATE_WINDOW_INTERVALS:] if interval["rate"] is not None]
    rate = sum(item["rate"] * item["hours"] for item in valid) / sum(item["hours"] for item in valid)
    rate_lower = sum(item["rate_lower"] * item["hours"] for item in valid) / sum(item["hours"] for item in valid)
    rate_upper = sum(item["rate_upper"] * item["hours"] for item in valid) / sum(item["hours"] for item in valid)
    high = [item for item in recent if item["rate"] is not None and baseline is not None and item["rate"] > baseline * 1.5]
    active = baseline is not None and len(recent) == 3 and len(high) == 3
    ratio = rate / baseline if baseline is not None and baseline > 0 else None
    if active:
        anomaly_reason = "Three consecutive observed intervals exceed 1.5× the earlier median. This is abnormal depletion, not a confirmed leak."
    elif baseline is None:
        anomaly_reason = "Earlier baseline history is insufficient; no sustained-anomaly conclusion."
    else:
        anomaly_reason = f"{len(high)} of the last three intervals exceed 1.5× the earlier median; three consecutive intervals are required."

    profile = _demand_profile(intervals, now, local_zone, config, rate, rate_upper)
    sufficient_history = all(row["supported"] for row in profile)
    local_hour = now.astimezone(local_zone).hour
    expected_now = profile[local_hour]["rate_lph"]
    # Confirmed persistence affects the central projection; a single noisy
    # interval still raises the planning floor but does not rewrite history.
    excess_factor = max(1.0, rate / expected_now) if active and expected_now > 0 else 1.0
    def central_rate(at: datetime) -> float:
        center = profile[at.astimezone(local_zone).hour]["rate_lph"] * excess_factor
        if active:
            center = max(center, rate)
        return center * projection_multiplier
    def upper_rate(at: datetime) -> float:
        upper = profile[at.astimezone(local_zone).hour]["upper_rate_lph"] * excess_factor
        return max(upper, rate_upper, central_rate(at) / projection_multiplier) * config["conservative_multiplier"] * projection_multiplier
    def lower_rate(at: datetime) -> float:
        return central_rate(at) * 0.8
    if any(not math.isfinite(upper_rate(now + timedelta(hours=hour))) for hour in range(24)):
        return unknown("Demand projection exceeds finite numerical limits.")

    anchor = latest["at"]
    end = now + timedelta(hours=HORIZON_HOURS)
    actual_inflows = [(item["arrived_at"], item["amount_l"]) for item in arrived if anchor < item["arrived_at"] <= end]
    conditional = [(item["scheduled_at"], item["amount_l"]) for item in pending if anchor < item["scheduled_at"] <= end]
    grid = {anchor, now, end}
    grid.update(now + timedelta(hours=hour) for hour in range(1, HORIZON_HOURS + 1))
    grid.update(at for at, _ in actual_inflows + conditional)
    boundary = _next_local_hour(anchor, local_zone)
    while boundary < end:
        grid.add(boundary)
        boundary = _next_local_hour(boundary, local_zone)
    times = sorted(at for at in grid if at >= anchor)
    future_rate = rate * projection_multiplier
    central = _project(anchor, latest["volume_l"], central_rate, reserve, capacity, times, actual_inflows + conditional,
                       origin=now, observed_rate=rate)
    conservative = _project(anchor, max(0.0, latest["volume_l"] - measurement_error), upper_rate, reserve, capacity, times, actual_inflows,
                            origin=now, observed_rate=rate_upper)
    optimistic = _project(anchor, latest["volume_l"], lower_rate, reserve, capacity, times, actual_inflows + conditional,
                          origin=now, observed_rate=rate)
    deadline = conservative["breach"] - timedelta(hours=lead + buffer) if conservative["breach"] is not None else None
    margin = (deadline - now).total_seconds() / 3600 if deadline is not None else None
    status = "ACT_NOW" if active or (margin is not None and margin <= 0) else ("WATCH" if margin is not None and margin <= 4 else "SAFE")
    kind = "INSPECT_USAGE" if active and (margin is None or margin > 0) else ("REQUEST_SUPPLY" if status in {"WATCH", "ACT_NOW"} else "MONITOR")
    title = {"INSPECT_USAGE": "Inspect sustained abnormal depletion", "REQUEST_SUPPLY": "Review an additional supply request", "MONITOR": "Monitor tank and planned supply"}[kind]
    if kind == "INSPECT_USAGE":
        body = "Inspect site-level usage and inlet/outlet records. Abnormal depletion does not confirm or locate a physical leak; keep readings fresh and review the stated demand assumptions."
    elif margin is not None and margin <= 0:
        body = "The planning deadline under the stated demand envelope has passed; review supply and inspect site usage now. The forecast depends on observed demand and declared settings."
    elif kind == "REQUEST_SUPPLY":
        body = "Review available supply against the observed-demand planning envelope. Planned delivery is conditional; a local notice is not a tanker booking or repair."
    else:
        body = "Keep readings fresh and confirm planned supply. The planning envelope depends on observed demand and declared settings; a notification is not a booking or repair."
    facts = [f"Latest measured storage is {latest['volume_l']:g} L; reserve is {reserve:g} L.",
             f"Recent inferred demand is {rate:.1f} L/h; arrived inflow is reconciled once.",
             f"Source is {latest['source']}; observation age is {age:.0f} minutes; {'simulated' if latest['simulated'] else 'manual/observed'} provenance.",
             "Central demand follows observed local-hour medians; the planning path excludes unarrived supply and uses an empirical upper demand envelope.",
             "Consumption assumes the arrived-inflow ledger is complete; aggregate tank data cannot locate a leak."]
    if not sufficient_history:
        facts.append("Daily-profile history is limited: unsupported hours use an earlier historical median, or the latest interval when none exists. Long-horizon accuracy is unvalidated.")
    if measurement_error:
        facts.append(f"Declared per-reading error is ±{measurement_error:g} L; recent interval demand is bounded from {rate_lower:.1f} to {rate_upper:.1f} L/h. This bound is an operator assumption, not calibration.")
    if requires_declaration:
        facts.append(calibration_note)
    if central["breach"] is None:
        facts.append("No central reserve breach within the 48-hour modeled horizon; this is not an unlimited guarantee.")
    if supply_status == "OVERDUE":
        facts.append("Planned supply is overdue and was not added as arrived water.")
    if projection_multiplier != 1:
        facts.append(f"Preview assumption only: future hourly demand changes by {(projection_multiplier - 1) * 100:+g}%; scaled recent-rate reference is {future_rate:.1f} L/h. Observed history and anomaly evidence are unchanged.")
    projection = [{"at": point["at"], "volume_l": point["volume_l"],
                   "conservative_l": conservative["points"][index]["volume_l"],
                   "optimistic_l": optimistic["points"][index]["volume_l"]}
                  for index, point in enumerate(central["points"])]
    return {
        "status": status, "current_rate_lph": round(rate, 3), "baseline_rate_lph": round(baseline, 3) if baseline is not None else None,
        "reserve_breach_at": _iso(central["breach"]), "empty_at": _iso(central["empty"]),
        "conservative_breach_at": _iso(conservative["breach"]), "latest_action_at": _iso(deadline),
        "hours_to_reserve": round((central["breach"] - now).total_seconds() / 3600, 6) if central["breach"] is not None else None,
        "action_margin_hours": round(margin, 6) if margin is not None else None,
        "next_supply_at": _iso(supply_at), "supply_status": supply_status,
        "anomaly": {"active": active, "observed_rate_lph": round(rate, 3), "expected_rate_lph": round(baseline, 3) if baseline is not None else None,
                    "ratio": round(ratio, 3) if ratio is not None else None, "evidence_count": len(high), "reason": anomaly_reason},
        "recommendation": {"type": kind, "title": title, "body": body, "deadline": _iso(deadline)},
        "facts": facts, "method": FORECAST_METHOD if projection_multiplier == 1 else FORECAST_METHOD + "_sensitivity", "uncertainty_label": SENSITIVITY_LABEL,
        "history": history, "projection": projection, "shortage_hours": round(central["shortage"], 6),
        "unmet_demand_l": round(central["unmet"], 3), "overflow_l": round(central["overflow"], 3),
        "forecast_description": "Hourly local-time demand profile from prior observed intervals, with a historical upper planning envelope and recent demand floor. This is a deterministic model, not a safety guarantee.",
        "forecast_config": config, "demand_profile": profile, "sufficient_forecast_history": sufficient_history,
        "forecast_assumptions": [
            f"Profile timezone is {zone_name}; lookback is {config['lookback_hours']:g} hours and the most recent four hours are excluded.",
            f"Supported local-hour bins use a duration-weighted median and observed {config['upper_quantile'] * 100:g}th-percentile demand bound; each needs {config['minimum_bucket_hours']:g} observed hours.",
            f"Upper planning demand is at least the latest interval's upper bound, multiplied by {config['conservative_multiplier']:g}; future demand can exceed observed history.",
            "Conservative storage starts at measured volume minus the declared reading error; planned arrivals are excluded.",
            "Central supply arrivals are conditional; the lower-demand path assumes 20% below the central profile and is sensitivity only.",
            "Demand patterns may change; neither profile nor envelope provides calibrated probability or guaranteed reserve protection.",
            "A sustained three-interval anomaly scales central demand until new observations change the measured evidence.",
            *([calibration_note] if requires_declaration else []),
        ],
        "measurement_bounds": {"per_reading_l": measurement_error, "latest_rate_lower_lph": round(rate_lower, 3),
                               "latest_rate_upper_lph": round(rate_upper, 3),
                               "latest_storage_lower_l": max(0.0, latest["volume_l"] - measurement_error),
                               "latest_storage_upper_l": min(capacity, latest["volume_l"] + measurement_error)},
    }


def analyze(site: dict, readings: list[dict], deliveries: list[dict], now: datetime) -> dict:
    """Analyze unchanged observed evidence using the API v1 interface."""
    return _analyze(site, readings, deliveries, now)


def analyze_with_config(site: dict, readings: list[dict], deliveries: list[dict], now: datetime,
                        config: dict) -> dict:
    """Evaluate predeclared validation candidates without mutating the frozen default."""
    return _analyze(site, readings, deliveries, now, forecast_config=config)


def analyze_preview(site: dict, readings: list[dict], deliveries: list[dict], now: datetime,
                    demand_change_percent: float = 0) -> dict:
    """Preview bounded future demand without fabricating historical readings.

    Supply changes are represented by the caller's separate copied delivery list.
    Historical baseline and anomaly evidence remain observed facts. In the
    returned preview, current_rate_lph remains the actual observed interval
    rate. Future rates alone change; the assumption appears in facts and the
    method label, while historical measurements and anomaly evidence stay fixed.
    """
    percent = _number(demand_change_percent)
    if not -50 <= percent <= 100:
        raise ValueError("Demand preview must be between -50% and +100%")
    return _analyze(site, readings, deliveries, now, projection_multiplier=1 + percent / 100)
