"""Independent 48-hour counterfactual reserve evaluator; no cloud or real data.

Future demand truth is used only to score forecasts. Future simulator refill
decisions are deliberately excluded from both origin inputs and scoring truth.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
import random
from statistics import mean

from backend.app import domain

HORIZON = 48
FROZEN_ORIGINAL_DATA_SHA256 = "688ad1143797468282f2e051acd7bc9a870f5272633a6ce9164143393f4e23c0"
EXPECTED_METHOD = "time_of_day_empirical_envelope"
FIXED_PROFILE_CONFIG = {"lookback_hours": 168, "upper_quantile": 0.9, "minimum_bucket_hours": 2}
MULTIPLIER_CANDIDATES = (1.0, 1.1, 1.2)
STRESS_SEEDS = (73, 101, 211)
STRESS_PATTERNS = ("daily_peaks", "upward_trend", "noisy_low_usage", "refill_shifts")
START = datetime(2026, 9, 11, tzinfo=UTC)


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def dataset_hash(dataset: dict) -> str:
    return hashlib.sha256(canonical(dataset).encode()).hexdigest()


def reserve_splits() -> dict[str, list[int]]:
    """Every full target ends before the next split begins; no partial futures."""
    return {"train": list(range(72, 120)), "validation": list(range(169, 288)), "test": list(range(337, 457))}


def history_at(dataset: dict, origin: int) -> tuple[list[dict], list[dict], datetime]:
    at = datetime.fromisoformat(dataset["readings"][origin]["observed_at"])
    rows = dataset["readings"][:origin + 1]
    deliveries = [row for row in dataset["deliveries"]
                  if datetime.fromisoformat(row["arrived_at"]) <= at
                  and datetime.fromisoformat(row["received_at"]) <= at]
    return rows, deliveries, at


def reserve_truth(dataset: dict, origin: int, reserve_l: float, horizon: int = HORIZON) -> dict:
    """Fractional first passage from the same observed anchor as both methods.

    Hourly latent demand is spread uniformly over its hour. This intentionally
    scores a no-future-refill counterfactual, not actual refill-managed storage.
    """
    if origin + horizon >= len(dataset["truth"]):
        raise ValueError("A complete future horizon is required")
    anchor = dataset["readings"][origin]["volume_l"]
    remaining = anchor
    crossing = 0.0 if anchor <= reserve_l else None
    points = []
    for step in range(1, horizon + 1):
        demand = dataset["truth"][origin + step]["consumption_l"]
        if demand is None or not math.isfinite(demand) or demand < 0:
            raise ValueError("Evaluator truth must contain finite nonnegative demand")
        if crossing is None and demand > 0 and remaining > reserve_l >= remaining - demand:
            crossing = step - 1 + (remaining - reserve_l) / demand
        remaining = max(0.0, remaining - demand)
        points.append(remaining)
    return {"breach_hours": crossing, "volumes_l": points,
            "normal_window": not any(dataset["truth"][h]["abnormal"] for h in range(origin, origin + horizon + 1))}


def legacy_forecast(rows: list[dict], arrivals: list[dict], at: datetime, site: dict) -> dict:
    """Frozen pre-repair last measured interval ×1.2; no profile or retuning."""
    previous, latest = rows[-2:]
    earlier = datetime.fromisoformat(previous["observed_at"])
    hours = (at - earlier).total_seconds() / 3600
    inflow = sum(row["amount_l"] for row in arrivals if earlier < datetime.fromisoformat(row["arrived_at"]) <= at)
    depleted = previous["volume_l"] + inflow - latest["volume_l"]
    usable = hours > 0 and depleted >= 0 and previous["volume_l"] + inflow <= site["capacity_l"]
    if not usable:
        return {"method": "last_interval_plus_20_percent", "state": "UNKNOWN", "breach_hours": None, "volumes_l": None}
    rate = depleted / hours * 1.2
    anchor = latest["volume_l"]
    crossing = 0.0 if anchor <= site["reserve_l"] else ((anchor - site["reserve_l"]) / rate if rate > 0 else None)
    if crossing is not None and crossing > HORIZON:
        crossing = None
    return {"method": "last_interval_plus_20_percent", "state": "AVAILABLE", "breach_hours": crossing,
            "volumes_l": [max(0.0, anchor - rate * step) for step in range(1, HORIZON + 1)]}


def interpolate_projection(points: list[dict], at: datetime) -> float:
    times = [datetime.fromisoformat(point["at"]) for point in points]
    for index in range(1, len(points)):
        if times[index - 1] <= at <= times[index]:
            fraction = (at - times[index - 1]).total_seconds() / (times[index] - times[index - 1]).total_seconds()
            return points[index - 1]["conservative_l"] + fraction * (points[index]["conservative_l"] - points[index - 1]["conservative_l"])
    raise ValueError("Projection must cover the complete scoring horizon")


def operational_forecast(rows: list[dict], arrivals: list[dict], at: datetime, site: dict, config: dict | None) -> dict:
    result = domain.analyze(site, rows, arrivals, at) if config is None else domain.analyze_with_config(site, rows, arrivals, at, config)
    effective = result.get("forecast_config")
    if result["status"] != "UNKNOWN" and (result.get("method") != EXPECTED_METHOD or effective != (config or domain.FORECAST_CONFIG)):
        raise ValueError(f"Evaluated method/config differs from operational contract: {result.get('method')}, {effective}")
    crossing = result.get("conservative_breach_at")
    return {"method": result.get("method"), "forecast_config": effective,
            "state": "UNKNOWN" if result["status"] == "UNKNOWN" else "AVAILABLE",
            "breach_hours": (datetime.fromisoformat(crossing) - at).total_seconds() / 3600 if crossing else None,
            "volumes_l": [interpolate_projection(result["projection"], at + timedelta(hours=step)) for step in range(1, HORIZON + 1)]
                         if result["status"] != "UNKNOWN" else None}


def score_origins(dataset: dict, origins: list[int], site: dict, method: str, config: dict | None = None) -> list[dict]:
    records = []
    for origin in origins:
        rows, arrivals, at = history_at(dataset, origin)
        truth = reserve_truth(dataset, origin, site["reserve_l"])
        forecast = legacy_forecast(rows, arrivals, at, site) if method == "legacy" else operational_forecast(rows, arrivals, at, site, config)
        predicted, actual = forecast["breach_hours"], truth["breach_hours"]
        error = predicted - actual if predicted is not None and actual is not None else None
        covered_points = sum(predicted_l <= truth_l + 0.001 for predicted_l, truth_l in zip(forecast["volumes_l"], truth["volumes_l"])) if forecast["volumes_l"] is not None else None
        records.append({"origin": origin, "origin_at": at.isoformat(), "normal_window": truth["normal_window"],
                        "truth_breach_hours": actual, "predicted_breach_hours": predicted, "prediction_state": forecast["state"],
                        "timing_error_hours": error, "truth_right_censored": actual is None,
                        "covered_hourly_points": covered_points, "hourly_points": HORIZON,
                        "true_deadline_margin_hours": actual - site["lead_hours"] - site["buffer_hours"] if actual is not None else None,
                        "predicted_deadline_margin_hours": predicted - site["lead_hours"] - site["buffer_hours"] if predicted is not None else None})
    return records


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * quantile
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def summarize(records: list[dict]) -> dict:
    matched = [row for row in records if row["timing_error_hours"] is not None]
    late = [row["timing_error_hours"] for row in matched if row["timing_error_hours"] > 1 / 3600]
    early = [-row["timing_error_hours"] for row in matched if row["timing_error_hours"] < -1 / 3600]
    events = [row for row in records if not row["truth_right_censored"]]
    available = [row for row in records if row["prediction_state"] == "AVAILABLE"]
    misses = sum(row["predicted_breach_hours"] is None for row in events)
    unsafe = sum(row["predicted_breach_hours"] is None or (row["timing_error_hours"] is not None and row["timing_error_hours"] > 1 / 3600) for row in events)
    covered = sum(row["covered_hourly_points"] or 0 for row in available)
    def rounded(value):
        return round(value, 6) if value is not None else None
    return {"windows": len(records), "normal_windows": sum(row["normal_window"] for row in records),
            "truth_reserve_events": len(events), "truth_right_censored_windows": len(records) - len(events),
            "prediction_available_windows": len(available), "unknown_windows": len(records) - len(available),
            "paired_evaluable_event_windows": len(matched), "missed_horizon_events": misses,
            "unsafe_or_unavailable_event_windows": unsafe,
            "unsafe_or_unavailable_event_fraction": rounded(unsafe / len(events)) if events else None,
            "late_event_predictions": len(late), "late_fraction_of_paired_events": rounded(len(late) / len(matched)) if matched else None,
            "mean_lateness_hours": rounded(mean(late)) if late else 0.0, "max_lateness_hours": rounded(max(late)) if late else 0.0,
            "early_event_predictions": len(early), "mean_earliness_hours": rounded(mean(early)) if early else 0.0,
            "p90_earliness_hours": rounded(percentile(early, 0.9)) if early else 0.0,
            "max_earliness_hours": rounded(max(early)) if early else 0.0,
            "timing_mae_hours": rounded(mean(abs(row["timing_error_hours"]) for row in matched)) if matched else None,
            "timing_bias_hours": rounded(mean(row["timing_error_hours"] for row in matched)) if matched else None,
            "prediction_availability_fraction": rounded(len(available) / len(records)) if records else None,
            "hourly_envelope_coverage_fraction": rounded(covered / (HORIZON * len(available))) if available else None,
            "all_48_points_covered_windows": sum(row["covered_hourly_points"] == HORIZON for row in available),
            "already_passed_predicted_deadlines": sum(row["predicted_deadline_margin_hours"] is not None and row["predicted_deadline_margin_hours"] <= 0 for row in records),
            "already_passed_true_deadlines": sum(row["true_deadline_margin_hours"] is not None and row["true_deadline_margin_hours"] <= 0 for row in records),
            "mean_predicted_deadline_margin_hours": rounded(mean(row["predicted_deadline_margin_hours"] for row in records if row["predicted_deadline_margin_hours"] is not None)) if matched else None,
            "mean_true_deadline_margin_hours": rounded(mean(row["true_deadline_margin_hours"] for row in events)) if events else None,
            "censored_windows_with_predicted_breach": sum(row["truth_right_censored"] and row["predicted_breach_hours"] is not None for row in records)}


def summaries(records: list[dict]) -> dict:
    return {"all_windows": summarize(records), "normal_windows": summarize([row for row in records if row["normal_window"]])}


def selection_key(candidate: dict) -> tuple:
    result = candidate["validation"]["all_windows"]
    failures = result["late_event_predictions"] + result["missed_horizon_events"] + result["unknown_windows"]
    # Unknown event windows may be counted in misses too; this explicit penalty
    # cannot make missing predictions look safer than a delivered forecast.
    return failures / max(1, result["windows"]), result["mean_earliness_hours"], candidate["config"]["conservative_multiplier"]


def choose_config(candidates: list[dict]) -> dict:
    if not candidates:
        raise ValueError("Validation candidates are required")
    return deepcopy(min(candidates, key=selection_key)["config"])


def generate_stress(pattern: str, seed: int, total_hours: int = 504) -> dict:
    """Additional predeclared synthetic stresses; original generator untouched."""
    if pattern not in STRESS_PATTERNS:
        raise ValueError("Unknown stress pattern")
    rng = random.Random(seed)
    volume = 40000.0
    bound = 300 if pattern == "noisy_low_usage" else 180
    readings, deliveries, truth = [], [], [{"consumption_l": None, "abnormal": False}]
    def reading(hour):
        at = START + timedelta(hours=hour)
        readings.append({"reading_id": f"stress-{pattern}-{seed}-{hour}", "observed_at": at.isoformat(), "received_at": at.isoformat(),
                         "volume_l": round(volume + rng.uniform(-bound, bound), 6), "source": "synthetic_stress", "simulated": True})
    reading(0)
    for hour in range(1, total_hours + 1):
        at = START + timedelta(hours=hour)
        local = (at.hour + 5.5) % 24
        baseline = 960 + 320 * math.sin(2 * math.pi * (local - 5) / 24)
        if pattern == "daily_peaks":
            baseline = 500 + 1500 * math.exp(-((local - 8) / 1.8) ** 2) + 1100 * math.exp(-((local - 19) / 2.0) ** 2)
        elif pattern == "upward_trend":
            baseline *= 1 + 0.002 * hour
        elif pattern == "noisy_low_usage":
            baseline = 230 + 170 * math.sin(2 * math.pi * (local - 5) / 24)
        abnormal = hour // 24 in {2, 9, 16} and 8 <= hour % 24 < 15
        usage = max(1.0, baseline * (2.5 if abnormal else 1) + rng.uniform(-40, 40))
        volume -= usage
        threshold = (7000, 12000, 18000)[hour // 24 % 3] if pattern == "refill_shifts" else 10000
        if volume < threshold:
            amount = (18000, 22000)[hour // 24 % 2] if pattern == "refill_shifts" else 20000
            volume += amount
            deliveries.append({"id": f"stress-inflow-{pattern}-{seed}-{hour}", "scheduled_at": at.isoformat(), "arrived_at": at.isoformat(),
                               "amount_l": amount, "status": "ARRIVED", "received_at": at.isoformat()})
        reading(hour)
        truth.append({"consumption_l": usage, "abnormal": abnormal})
    return {"readings": readings, "deliveries": deliveries, "truth": truth,
            "stress_metadata": {"pattern": pattern, "seed": seed, "measurement_error_l": bound, "data_kind": "SIMULATED_STRESS"}}


def build_reserve_report(dataset: dict, site: dict) -> dict:
    if dataset_hash(dataset) != FROZEN_ORIGINAL_DATA_SHA256:
        raise ValueError("Original seed42 generator changed; baseline comparability is invalid")
    site = {**site, "measurement_error_l": 180, "timezone": "Asia/Kolkata"}
    split = reserve_splits()
    candidates = []
    for multiplier in MULTIPLIER_CANDIDATES:
        config = {**FIXED_PROFILE_CONFIG, "conservative_multiplier": multiplier}
        records = score_origins(dataset, split["validation"], site, "operational", config)
        candidates.append({"config": config, "validation": summaries(records)})
    selected = choose_config(candidates)
    operational_config = dict(domain.FORECAST_CONFIG)
    method_matches = domain.FORECAST_METHOD == EXPECTED_METHOD and operational_config == selected
    if not method_matches:
        raise ValueError(f"Frozen operational method/config does not match validation selection: selected={selected}; operational={operational_config}")
    legacy = score_origins(dataset, split["test"], site, "legacy")
    upgraded = score_origins(dataset, split["test"], site, "operational")
    stress = []
    stress_old_records, stress_new_records = [], []
    for pattern in STRESS_PATTERNS:
        for seed in STRESS_SEEDS:
            data = generate_stress(pattern, seed)
            stress_site = {**site, "measurement_error_l": data["stress_metadata"]["measurement_error_l"]}
            old = score_origins(data, split["test"], stress_site, "legacy")
            new = score_origins(data, split["test"], stress_site, "operational")
            stress_old_records.extend(old)
            stress_new_records.extend(new)
            stress.append({"pattern": pattern, "seed": seed, "data_kind": "SIMULATED_STRESS", "data_sha256": dataset_hash(data),
                           "measurement_error_l": stress_site["measurement_error_l"], "legacy": summaries(old), "upgraded": summaries(new),
                           "upgraded_late_examples": [row for row in new if row["timing_error_hours"] is not None and row["timing_error_hours"] > 1 / 3600][:5],
                           "upgraded_missed_examples": [row for row in new if row["truth_breach_hours"] is not None and row["predicted_breach_hours"] is None][:5]})
    return {"status": "evaluated", "horizon_hours": HORIZON, "target": "First reserve crossing under observed-anchor, future-demand, no-future-refill counterfactual",
            "original_generator_preserved_sha256": dataset_hash(dataset), "site": site,
            "splits": {name: {"origins": len(indices), "first_origin_index": min(indices), "last_origin_index": max(indices),
                               "last_future_index": max(indices) + HORIZON} for name, indices in split.items()},
            "purging": "Full 48-hour targets end before the next split starts. Overlapping origins within a split are correlated; counts are not independent samples.",
            "selection": {"candidates": candidates, "selected_config": selected, "operational_config": operational_config,
                          "expected_method": EXPECTED_METHOD, "operational_method": domain.FORECAST_METHOD, "matches_operational_method": method_matches,
                          "criterion": "Validation only: minimize (late + missed-horizon + unknown penalties)/all windows, then positive mean earliness, then smaller multiplier. Unknown misses may receive both penalties."},
            "holdout": {"legacy": summaries(legacy), "upgraded": summaries(upgraded), "legacy_records": legacy, "upgraded_records": upgraded},
            "stress": {"label": "Additional independent-seed synthetic stress; not real-world validation", "seeds": list(STRESS_SEEDS),
                       "patterns": list(STRESS_PATTERNS), "selected_on_stress": False, "cases": stress,
                       "aggregate": {"legacy": summaries(stress_old_records), "upgraded": summaries(stress_new_records)}},
            "definitions": {"normal_window": "Origin and all next 48 truth intervals have no labeled excess-demand episode.",
                            "timing_error": "Predicted minus true reserve time; positive is late. One-second numerical tolerance.",
                            "coverage": "Conservative simulated level <= no-refill truth at each of 48 future hourly points, among available forecasts; not a probability interval.",
                            "censored": "Truth does not reach reserve within48h; exact timing error is not inferred. Forecasted breach in such windows is separately counted.",
                            "deadline_margin": "Reserve time minus supply lead14h and buffer3h; positive permits time to act. Both predicted and true margins are retained.",
            "anchor": "Truth and frozen legacy start at observed level. Upgraded conservative storage starts at observed level minus the declared per-reading error bound (180L original,300L noisy stress), so the comparison includes this explicit storage safeguard as well as the profile upgrade.",
                            "refills": "Past arrived/received inflows reconcile measured depletion. All future refill decisions are unavailable and uncredited."}}
