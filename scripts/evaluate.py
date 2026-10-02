"""Reproducible synthetic one-hour demand evaluation; stdlib only, no cloud calls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import median
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.domain import RATE_WINDOW_INTERVALS, analyze  # noqa: E402


SEED = 42
TOTAL_HOURS = 504
START = datetime(2026, 9, 11, 0, 0, tzinfo=UTC)
SITE = {"capacity_l": 50000, "reserve_l": 5000, "lead_hours": 14, "buffer_hours": 3, "freshness_minutes": 90}
WINDOWS = (1, 3, 6)


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def generate(seed: int = SEED, total_hours: int = TOTAL_HOURS) -> dict:
    """Generate in order; model inputs and evaluator-only demand truth stay separate.

    All physical quantities/labels here are assumptions, not measured campus data.
    An automatic simulated refill policy keeps levels measurable; its future
    decisions are never exposed to a forecast origin as known arrivals.
    """
    rng = random.Random(seed)
    volume = 40000.0
    readings = [{"reading_id": "eval-0", "observed_at": START.isoformat(), "received_at": START.isoformat(),
                 "volume_l": volume + rng.uniform(-180, 180), "source": "synthetic_evaluation", "simulated": True}]
    deliveries: list[dict] = []
    truth = [{"consumption_l": None, "abnormal": False}]
    for hour in range(1, total_hours + 1):
        at = START + timedelta(hours=hour)
        local_hour = (at.hour + 5.5) % 24
        baseline = 960 + 320 * math.sin(2 * math.pi * (local_hour - 5) / 24)
        abnormal = hour // 24 in {2, 9, 16} and 8 <= hour % 24 < 15
        usage = baseline * (2.5 if abnormal else 1) + rng.uniform(-40, 40)
        volume -= usage
        if volume < 10000:
            amount = 20000.0
            volume += amount
            deliveries.append({"id": f"eval-inflow-{hour}", "scheduled_at": at.isoformat(), "arrived_at": at.isoformat(),
                               "amount_l": amount, "status": "ARRIVED", "received_at": at.isoformat()})
        readings.append({"reading_id": f"eval-{hour}", "observed_at": at.isoformat(), "received_at": at.isoformat(),
                         "volume_l": round(volume + rng.uniform(-180, 180), 6), "source": "synthetic_evaluation", "simulated": True})
        truth.append({"consumption_l": usage, "abnormal": abnormal})
    return {"readings": readings, "deliveries": deliveries, "truth": truth}


def split_origins() -> dict[str, list[int]]:
    """One-hour targets; drop boundary-adjacent origins rather than overlap splits."""
    return {"train": list(range(72, 167)), "validation": list(range(169, 335)), "test": list(range(337, 503))}


def history_at(dataset: dict, origin: int) -> tuple[list[dict], list[dict], datetime]:
    at = datetime.fromisoformat(dataset["readings"][origin]["observed_at"])
    rows = dataset["readings"][:origin + 1]
    arrivals = [row for row in dataset["deliveries"] if datetime.fromisoformat(row["arrived_at"]) <= at
                and datetime.fromisoformat(row["received_at"]) <= at]
    return rows, arrivals, at


def infer_rates(rows: list[dict], deliveries: list[dict]) -> list[tuple[datetime, float]]:
    rates = []
    for earlier, later in zip(rows, rows[1:]):
        start = datetime.fromisoformat(earlier["observed_at"])
        end = datetime.fromisoformat(later["observed_at"])
        hours = (end - start).total_seconds() / 3600
        inflow = sum(row["amount_l"] for row in deliveries if start < datetime.fromisoformat(row["arrived_at"]) <= end)
        rates.append((end, (earlier["volume_l"] + inflow - later["volume_l"]) / hours))
    return rates


def predict(rows: list[dict], arrivals: list[dict], at: datetime, method: str, window: int = 3) -> float:
    """No future observations, labels, demand truth or scenario metadata accepted."""
    rates = infer_rates(rows, arrivals)
    if method == "recent_mean":
        chosen = [value for _, value in rates[-window:]]
        return sum(chosen) / len(chosen)
    if method == "last_rate":
        return rates[-1][1]
    if method == "earlier_median":
        return float(median(value for time, value in rates if time <= at - timedelta(hours=4)))
    raise ValueError("Unknown evaluation method")


def metrics(predictions: list[float], targets: list[float]) -> dict:
    if not predictions or len(predictions) != len(targets):
        raise ValueError("Prediction and target counts must be equal and nonzero")
    errors = [prediction - target for prediction, target in zip(predictions, targets)]
    return {"samples": len(errors), "mae_l": round(sum(abs(value) for value in errors) / len(errors), 6),
            "rmse_l": round(math.sqrt(sum(value * value for value in errors) / len(errors)), 6),
            "bias_l": round(sum(errors) / len(errors), 6)}


def choose_window(validation: dict[int, dict]) -> int:
    return min(validation, key=lambda window: (validation[window]["mae_l"], window))


def evaluate_method(dataset: dict, origins: list[int], method: str, window: int = 3) -> dict:
    predictions = []
    targets = []
    for origin in origins:
        rows, arrivals, at = history_at(dataset, origin)
        predictions.append(predict(rows, arrivals, at, method, window))
        targets.append(dataset["truth"][origin + 1]["consumption_l"])
    return metrics(predictions, targets)


def evaluate_anomaly(dataset: dict, origins: list[int]) -> dict:
    outcomes: dict[int, bool] = {}
    for origin in origins:
        rows, arrivals, at = history_at(dataset, origin)
        outcomes[origin] = analyze(SITE, rows, arrivals, at)["anomaly"]["active"]
    normal_hours = sum(not dataset["truth"][origin]["abnormal"] for origin in origins)
    false_alerts = sum(outcomes[origin] and not dataset["truth"][origin]["abnormal"]
                       and not outcomes.get(origin - 1, False) for origin in origins)
    episodes = []
    for origin in origins:
        if dataset["truth"][origin]["abnormal"] and not dataset["truth"][origin - 1]["abnormal"]:
            end = origin
            while end + 1 < len(dataset["truth"]) and dataset["truth"][end + 1]["abnormal"]:
                end += 1
            detections = [time for time in range(origin, end + 1) if outcomes.get(time)]
            episodes.append({"onset_at": dataset["readings"][origin]["observed_at"], "duration_hours": end - origin + 1,
                             "detected": bool(detections), "delay_hours": detections[0] - origin if detections else None})
    return {"monitored_site_hours": len(origins), "normal_site_hours": normal_hours, "false_alert_events": false_alerts,
            "false_alerts_per_site_hour": round(false_alerts / normal_hours, 8) if normal_hours else None,
            "labeled_episodes": len(episodes), "missed_episodes": sum(not row["detected"] for row in episodes), "episodes": episodes,
            "definition": "A false alert is a new active transition during a labeled-normal monitored hour; continuing alerts count once."}


def build_report() -> dict:
    dataset = generate()
    origins = split_origins()
    validation = {window: evaluate_method(dataset, origins["validation"], "recent_mean", window) for window in WINDOWS}
    selected = choose_window(validation)
    test = {"recent_mean_selected": evaluate_method(dataset, origins["test"], "recent_mean", selected),
            "last_rate": evaluate_method(dataset, origins["test"], "last_rate"),
            "earlier_median": evaluate_method(dataset, origins["test"], "earlier_median")}
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in ("scripts/evaluate.py", "backend/app/domain.py")}
    split_details = {name: {"samples": len(indices), "first_origin": dataset["readings"][indices[0]]["observed_at"],
                            "last_origin": dataset["readings"][indices[-1]]["observed_at"],
                            "last_target_end": dataset["readings"][indices[-1] + 1]["observed_at"]}
                     for name, indices in origins.items()}
    mae = test["recent_mean_selected"]["mae_l"]
    return {
        "data_kind": "SIMULATED", "status": "complete", "evaluated_on": "2026-10-02", "seed": SEED,
        "summary": f"Synthetic holdout: recent-mean ({selected} intervals) next-hour demand MAE {mae:.1f} L across {len(origins['test'])} origins. No real sensor data or calibrated probability.",
        "target": {"name": "next_hour_consumption", "unit": "litres", "horizon_hours": 1},
        "generator": {"total_hours": TOTAL_HOURS, "baseline_lph": 960, "diurnal_amplitude_lph": 320,
                      "demand_jitter_lph": 40, "reading_error_l": 180, "excess_multiplier": 2.5,
                      "refill_policy": "Simulated 20,000 L arrival when physical storage drops below 10,000 L; future arrivals unavailable at origin."},
        "data_sha256": hashlib.sha256(canonical(dataset).encode("utf-8")).hexdigest(), "source_sha256": source_hashes,
        "splits": split_details, "purging": "One-hour target windows are disjoint; one boundary origin is omitted on each side. Features may use earlier observed history.",
        "selection": {"method": "recent_mean", "candidate_windows": list(WINDOWS), "selected_window_intervals": selected,
                      "interpretation": "A one-interval recent mean is exactly the last-rate baseline; no complexity advantage is claimed.",
                      "criterion": "Lowest validation MAE; shorter window breaks ties", "validation": {str(window): value for window, value in validation.items()},
                      "operational_window_intervals": RATE_WINDOW_INTERVALS,
                      "operational_method_label": "last_interval_rate",
                      "matches_operational_method": selected == RATE_WINDOW_INTERVALS},
        "final_test": test, "anomaly_final_test": evaluate_anomaly(dataset, origins["test"]),
        "reserve_timing": {"status": "not_evaluated", "reason": "Next-hour demand metrics do not validate 48-hour reserve timing under uncertain future supply. Arithmetic behavior is covered separately by domain tests."},
        "limitations": ["Synthetic assumptions and a single fixed seed; no field validation or real campus readings.",
                        "Final test is reporting only; selection uses validation, never holdout results.",
                        "Reading and demand error bounds are simulator assumptions, not calibrated confidence intervals.",
                        "No measured water savings, physical leak localization, supplier response or health effect is established.",
                        "Detector threshold 1.5× and persistence three intervals are fixed rules; not fitted or calibrated on this holdout.",
                        "The baseline comparison reports unfavorable results if a simpler method wins."],
    }


def markdown(report: dict) -> str:
    lines = ["# Synthetic evaluation", "", "Generated on 2 October 2026. No real sensor or campus data was used.", "", report["summary"], "",
             "Run from the extracted project root:", "", "```powershell", ".\\.venv\\Scripts\\python.exe scripts/evaluate.py", "```", "",
             "The authoritative artifact is `artifacts/evaluation.json`; the same bytes are copied to `backend/app/data/evaluation.json` for packaged Lambda/API use.", "",
             "Chronological generation separates evaluator-only demand truth from operational readings. At each origin, inputs contain only readings and arrivals already observed/received. The forecast target is next-hour consumption in litres, not a claim of 48-hour forecast accuracy.", "",
             "Window selection uses validation MAE only. One-hour target windows do not overlap splits; boundary origins are purged. Earlier observed history remains available to later origins, as it would in use.", "",
             report["selection"]["interpretation"], "",
             "| Final-test method | Origins | MAE (L) | RMSE (L) | Bias (L) |", "|---|---:|---:|---:|---:|"]
    for name, result in report["final_test"].items():
        lines.append(f"| {name} | {result['samples']} | {result['mae_l']:.3f} | {result['rmse_l']:.3f} | {result['bias_l']:.3f} |")
    anomaly = report["anomaly_final_test"]
    lines += ["", f"Detector: {anomaly['labeled_episodes']} labeled holdout episode(s), {anomaly['missed_episodes']} missed, {anomaly['false_alert_events']} new false-alert event(s) across {anomaly['normal_site_hours']} labeled-normal site-hours.", "",
              "Delay is measured from the first observed abnormal interval. A continued alert counts once; the three-interval persistence rule intentionally delays activation. See artifact episode records and denominator definitions.", "",
              "## Practical limits", ""]
    lines += ["- " + text for text in report["limitations"]]
    lines += ["", report["reserve_timing"]["reason"], "", "Data/source hashes, split boundaries, candidate validation results, and method match are stored in the JSON. The generator was not retuned after seeing the holdout.", ""]
    return "\n".join(lines)


def main() -> None:
    report = build_report()
    encoded = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    for relative in ("artifacts/evaluation.json", "backend/app/data/evaluation.json"):
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
    (ROOT / "docs" / "EVALUATION.md").write_text(markdown(report), encoding="utf-8")
    print(report["summary"])
    print(f"Selected window: {report['selection']['selected_window_intervals']}; operational window: {RATE_WINDOW_INTERVALS}")
    print("Wrote identical evaluation JSON artifacts and generated docs/EVALUATION.md")


if __name__ == "__main__":
    main()
