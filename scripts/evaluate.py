"""Frozen legacy demand metrics and full-horizon synthetic reserve evaluation."""

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
from backend.app import domain  # noqa: E402
from scripts.backtest_reserve import (  # noqa: E402
    build_reserve_report, generate_stress, percentile, reserve_splits, STRESS_PATTERNS, STRESS_SEEDS,
)


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


def evaluate_anomaly(dataset: dict, origins: list[int], site: dict | None = None) -> dict:
    outcomes: dict[int, bool] = {}
    site = site or SITE
    # Observe the preceding state so a continuing alert at the split boundary
    # cannot be mislabeled a newly initiated false alert.
    monitored = ([origins[0] - 1] if origins[0] > 0 else []) + origins
    for origin in monitored:
        rows, arrivals, at = history_at(dataset, origin)
        outcomes[origin] = analyze(site, rows, arrivals, at)["anomaly"]["active"]
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
            new_alerts = [time for time in range(origin, end + 1)
                          if outcomes.get(time) and not outcomes.get(time - 1, False)]
            episodes.append({"onset_at": dataset["readings"][origin]["observed_at"], "duration_hours": end - origin + 1,
                             "detected": bool(detections), "delay_hours": detections[0] - origin if detections else None,
                             "active_before_onset": outcomes.get(origin - 1, False),
                             "new_alert_during_episode": bool(new_alerts),
                             "new_alert_delay_hours": new_alerts[0] - origin if new_alerts else None})
    delays = [row["delay_hours"] for row in episodes if row["detected"]]
    return {"monitored_site_hours": len(origins), "normal_site_hours": normal_hours, "false_alert_events": false_alerts,
            "false_alerts_per_site_hour": round(false_alerts / normal_hours, 8) if normal_hours else None,
            "labeled_episodes": len(episodes), "missed_episodes": sum(not row["detected"] for row in episodes), "episodes": episodes,
            "detected_episodes": len(delays), "mean_detection_delay_hours": sum(delays) / len(delays) if delays else None,
            "max_detection_delay_hours": max(delays) if delays else None,
            "episodes_already_alerted_before_onset": sum(row["active_before_onset"] for row in episodes),
            "episodes_with_new_alert_transition": sum(row["new_alert_during_episode"] for row in episodes),
            "definition": "Detection is an active-alert overlap with a labeled episode, not necessarily a new warning. Prior-active and new-transition counts are separate. False alert means a new active transition during a labeled-normal monitored hour; continuing alerts count once."}


def build_report() -> dict:
    dataset = generate()
    origins = split_origins()
    validation = {window: evaluate_method(dataset, origins["validation"], "recent_mean", window) for window in WINDOWS}
    selected = choose_window(validation)
    test = {"recent_mean_selected": evaluate_method(dataset, origins["test"], "recent_mean", selected),
            "last_rate": evaluate_method(dataset, origins["test"], "last_rate"),
            "earlier_median": evaluate_method(dataset, origins["test"], "earlier_median")}
    reserve = build_reserve_report(dataset, SITE)
    original_anomaly = evaluate_anomaly(dataset, origins["test"], reserve["site"])
    anomaly_cases = [{"pattern": "original_seed42", "seed": SEED, **original_anomaly}]
    for pattern in STRESS_PATTERNS:
        for seed in STRESS_SEEDS:
            stress = generate_stress(pattern, seed)
            site = {**reserve["site"], "measurement_error_l": stress["stress_metadata"]["measurement_error_l"]}
            anomaly_cases.append({"pattern": pattern, "seed": seed,
                                  **evaluate_anomaly(stress, reserve_splits()["test"], site)})
    episodes = [{"pattern": case["pattern"], "seed": case["seed"], **episode}
                for case in anomaly_cases for episode in case["episodes"]]
    detected_delays = [episode["delay_hours"] for episode in episodes if episode["detected"]]
    normal_hours = sum(case["normal_site_hours"] for case in anomaly_cases)
    false_alerts = sum(case["false_alert_events"] for case in anomaly_cases)
    anomaly = {"monitored_site_hours": sum(case["monitored_site_hours"] for case in anomaly_cases),
               "normal_site_hours": normal_hours, "false_alert_events": false_alerts,
               "false_alerts_per_site_hour": round(false_alerts / normal_hours, 8) if normal_hours else None,
               "labeled_episodes": len(episodes), "detected_episodes": len(detected_delays),
               "missed_episodes": len(episodes) - len(detected_delays),
               "episode_detection_fraction": len(detected_delays) / len(episodes) if episodes else None,
               "mean_detection_delay_hours": sum(detected_delays) / len(detected_delays) if detected_delays else None,
               "p90_detection_delay_hours": percentile(detected_delays, 0.9),
               "max_detection_delay_hours": max(detected_delays) if detected_delays else None,
               "episodes_already_alerted_before_onset": sum(episode["active_before_onset"] for episode in episodes),
               "episodes_with_new_alert_transition": sum(episode["new_alert_during_episode"] for episode in episodes),
               "episodes": episodes, "cases": anomaly_cases,
               "definition": "Detection is active-alert overlap with an episode; prior-active and new transitions are separately counted. False alerts are new active transitions during labeled-normal site-hours; preceding origin avoids boundary double counts. Delays apply to overlaps only; misses are separate.",
               "data_kind": "SIMULATED_WITH_ADDITIONAL_SYNTHETIC_STRESS"}
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in ("scripts/evaluate.py", "scripts/backtest_reserve.py", "backend/app/domain.py")}
    split_details = {name: {"samples": len(indices), "first_origin": dataset["readings"][indices[0]]["observed_at"],
                            "last_origin": dataset["readings"][indices[-1]]["observed_at"],
                            "last_target_end": dataset["readings"][indices[-1] + 1]["observed_at"]}
                     for name, indices in origins.items()}
    mae = test["recent_mean_selected"]["mae_l"]
    old = reserve["holdout"]["legacy"]["all_windows"]
    new = reserve["holdout"]["upgraded"]["all_windows"]
    return {
        "data_kind": "SIMULATED", "status": "complete", "evaluated_on": "2026-10-02", "seed": SEED,
        "summary": f"Synthetic 48h holdout: frozen legacy {old['late_event_predictions']}/{old['paired_evaluable_event_windows']} late reserve predictions; upgraded {new['late_event_predictions']}/{new['paired_evaluable_event_windows']}, mean earliness {new['mean_earliness_hours']:.2f}h. Legacy one-hour MAE remains {mae:.1f}L. Synthetic stress and failures are reported separately; no field accuracy or calibrated probability.",
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
                      "operational_method_label": domain.FORECAST_METHOD,
                      "matches_operational_method": domain.FORECAST_METHOD == "last_interval_rate" and selected == RATE_WINDOW_INTERVALS,
                      "scope": "Legacy next-hour comparison preserved; it is not the upgraded time-of-day forecast's accuracy score."},
        "final_test": test, "anomaly_final_test": anomaly, "anomaly_original_holdout": original_anomaly,
        "reserve_timing": reserve,
        "limitations": ["All inputs are synthetic; original fixed seed plus 12 predeclared pattern/seed stress cases. No field validation or real campus readings.",
                        "Final test is reporting only; selection uses validation, never holdout results.",
                        "Reading error bounds and empirical demand envelopes are explicit simulator/planning assumptions, not calibrated confidence intervals.",
                        "No measured water savings, physical leak localization, supplier response or health effect is established.",
                        "Detector threshold 1.5× and persistence three intervals are fixed rules; not fitted or calibrated on this holdout.",
                        "The baseline comparison reports unfavorable results if a simpler method wins.",
                        "Overlapping48h windows within a split are correlated; counts do not establish independent-sample statistical confidence.",
                        "No-future-refill scoring is a counterfactual; actual simulator refills may prevent the predicted shortage.",
                        "Early warnings can be operationally costly; earliness, already-passed deadlines, censored truth and missed predictions are retained.",
                        "The old one-hour MAE is unchanged and is not relabeled as improved48h operational accuracy."],
    }


def markdown(report: dict) -> str:
    reserve = report["reserve_timing"]
    selected_validation = next(candidate["validation"]["all_windows"] for candidate in reserve["selection"]["candidates"]
                               if candidate["config"] == reserve["selection"]["selected_config"])
    lines = ["# Synthetic evaluation", "", "Generated on 2 October 2026. No real sensor or campus data was used.", "", report["summary"], "",
             "Run from the extracted root with the application's Python environment:", "", "```text", "python scripts/evaluate.py", "```", "",
             "The authoritative [JSON artifact](../artifacts/evaluation.json) is copied byte-for-byte to `backend/app/data/evaluation.json` for packaged API/Lambda use. Reproduction tests check both bytes and source/data hashes.", "",
             "## Original generator and frozen comparison", "",
             f"The original seed42,504-hour generator is unchanged. Its canonical output SHA-256 is `{report['data_sha256']}`. Its original one-hour splits and demand metrics remain available; they are **not** the upgraded method's48-hour accuracy score.", "",
             "For reserve timing, every origin has48 complete future demand intervals. Train origins72–119 end by167; validation169–287 ends by335; heldout337–456 ends by504. Full future targets never cross the next split's first origin. Origins overlap within each split and are correlated, so120 windows are not120 independent experiments.", "",
             "Truth is the fractional first reserve crossing after the observed level, subtracting evaluator-only future demand. No future refill is credited. Past arrived/received deliveries reconcile measured depletion, but future simulator decisions and labels are never forecast inputs. Demand is spread uniformly within each truth hour; this is a counterfactual, not actual refill-managed tank storage.", "",
             "Frozen legacy predicts a constant last-interval rate×1.2 from measured storage. The upgrade projects a historical local-hour profile, an empirical upper-demand envelope and a recent upper-rate floor. It also starts conservative storage at measured level minus declared error:180L here,300L in noisy stress. The paired comparison therefore includes both the profile and explicit storage safeguard. These bounds are simulator assumptions, not confidence intervals.", "",
             "A normal window has no labeled abnormal demand at its origin or any of the48 following intervals. Our endpoint, observed-anchor and whole-window protocol produces65 normal windows and27 legacy late predictions; it does not force the externally reported63/20 counts for which no executable protocol was supplied.", "",
             "## Validation selection and operational match", "",
             "Lookback168h,upper quantile0.9 and minimum bucket support2h were fixed before holdout reporting. Only the conservative multiplier candidates1.0/1.1/1.2 were compared on119 validation origins. Selection minimizes late+missed+unknown penalties, then positive mean earliness, then the smaller multiplier. The JSON preserves all candidates and the explicit unknown penalty.", "",
             f"Selected/frozen config: `{canonical(reserve['selection']['selected_config'])}`. Operational method `{reserve['selection']['operational_method']}` matches the evaluated method/config. Drift raises an error; a label alone cannot establish a match.", "",
             "| Multiplier | Validation windows | Late | Missed | UNKNOWN | Mean early(h) | P90 early(h) |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for candidate in reserve["selection"]["candidates"]:
        row = candidate["validation"]["all_windows"]
        lines.append(f"| {candidate['config']['conservative_multiplier']} | {row['windows']} | {row['late_event_predictions']} | {row['missed_horizon_events']} | {row['unknown_windows']} | {row['mean_earliness_hours']:.3f} | {row['p90_earliness_hours']:.3f} |")
    lines += ["", f"The selected validation envelope covers {100*selected_validation['hourly_envelope_coverage_fraction']:.3f}% of hourly points and {selected_validation['all_48_points_covered_windows']}/{selected_validation['windows']} complete windows. Point coverage is separately reported and was not substituted into selection after inspecting these outcomes.", "",
              "## Untuned48-hour original holdout", "",
              "| Method/slice | Windows | True events | Censored | Paired timing | UNKNOWN | Late | Missed within48h |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    result_rows = []
    for method in ("legacy", "upgraded"):
        for subset in ("all_windows", "normal_windows"):
            row = reserve["holdout"][method][subset]
            label = f"{method}/{subset}"
            result_rows.append((label, row))
            lines.append(f"| {label} | {row['windows']} | {row['truth_reserve_events']} | {row['truth_right_censored_windows']} | {row['paired_evaluable_event_windows']} | {row['unknown_windows']} | {row['late_event_predictions']} | {row['missed_horizon_events']} |")
    lines += ["", "| Method/slice | Mean late(h) | Max late(h) | Mean early(h) | P90 early(h) | Max early(h) | Hourly coverage |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for label, row in result_rows:
        lines.append(f"| {label} | {row['mean_lateness_hours']:.3f} | {row['max_lateness_hours']:.3f} | {row['mean_earliness_hours']:.3f} | {row['p90_earliness_hours']:.3f} | {row['max_earliness_hours']:.3f} | {100*row['hourly_envelope_coverage_fraction']:.3f}% |")
    new = reserve["holdout"]["upgraded"]["all_windows"]
    lines += ["", f"Upgraded warnings classify {new['already_passed_predicted_deadlines']}/{new['windows']} planning deadlines as already passed, while truth does so for {new['already_passed_true_deadlines']}/{new['windows']}. Lead14h plus buffer3h is subtracted from both true and predicted reserve times; record-level margins are retained in the JSON. Early deadlines can incur avoidable calls or deliveries.", "",
              "Coverage means simulated conservative volume is at or below no-refill truth at48 hourly checkpoints, among available forecasts. UNKNOWN availability and censored truth remain separate. A right-censored window has no true crossing within48h; no exact timing error is invented for it. Numerical lateness tolerance is one second.", "",
              "## Additional independent-seed synthetic stress", "",
              "These twelve cases use predeclared seeds73,101,211 across daily peaks, upward trend, low usage with noisy readings, and shifting refill thresholds/amounts. They are synthetic stresses, not measured realistic performance. None selects or retunes the frozen configuration. Full metadata, hashes, legacy scores and upgraded late/missed examples are in the JSON.", "",
              "| Pattern/seed | Legacy late | New late | New max late(h) | UNKNOWN | Censored | Mean early(h) | P90 early(h) | Censored predicted events |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for case in reserve["stress"]["cases"]:
        old, row = case["legacy"]["all_windows"], case["upgraded"]["all_windows"]
        lines.append(f"| {case['pattern']}/{case['seed']} | {old['late_event_predictions']} | {row['late_event_predictions']} | {row['max_lateness_hours']:.3f} | {row['unknown_windows']} | {row['truth_right_censored_windows']} | {row['mean_earliness_hours']:.3f} | {row['p90_earliness_hours']:.3f} | {row['censored_windows_with_predicted_breach']} |")
    aggregate = reserve["stress"]["aggregate"]["upgraded"]["all_windows"]
    lines += ["", f"Combined stress exposure: {aggregate['windows']} windows, {aggregate['truth_reserve_events']} truth crossings, {aggregate['truth_right_censored_windows']} censored, {aggregate['unknown_windows']} UNKNOWN, {aggregate['late_event_predictions']} late predictions and {aggregate['missed_horizon_events']} missed-horizon events. Mean lateness among late predictions:{aggregate['mean_lateness_hours']:.3f}h; maximum:{aggregate['max_lateness_hours']:.3f}h. Individual cases and overlap remain visible; this pooled count is not independent-sample confidence.", "",
              "Zero lateness on the original holdout does not generalize to these stresses. The noisy-low-usage bound can produce very early warnings and crossings where truth is censored; this operational cost remains visible. No zero-failure guarantee is made.", "",
              "## Expanded anomaly episodes", ""]
    anomaly = report["anomaly_final_test"]
    lines += [f"Across original holdout plus12 independent pattern/seed cases: {anomaly['detected_episodes']}/{anomaly['labeled_episodes']} episodes detected, {anomaly['missed_episodes']} missed; {anomaly['false_alert_events']} new false-alert events/{anomaly['normal_site_hours']} labeled-normal site-hours ({anomaly['false_alerts_per_site_hour']:.6f}/hour). Total monitored exposure:{anomaly['monitored_site_hours']} site-hours. Mean delay among detected episodes:{anomaly['mean_detection_delay_hours']:.3f}h; P90:{anomaly['p90_detection_delay_hours']:.3f}h; maximum:{anomaly['max_detection_delay_hours']}h.", "",
              f"Detection here means an active alert overlaps a labeled episode. {anomaly['episodes_already_alerted_before_onset']} episodes were already alerted before onset; {anomaly['episodes_with_new_alert_transition']} have a new alert transition during the episode. An overlapping alert can therefore give zero delay without being a new correct warning. Both counts and first-new-alert delays are retained per episode.", "",
              "A preceding state prevents split-boundary double counting. A continued alert counts once; overlap delay begins at the first observed labeled abnormal interval. Misses are counted separately, not omitted from the denominator. The detector was not retuned on these stresses.", "",
              "| Dataset/seed | Episodes | Missed | False alert events | Normal site-hours | Mean detected delay(h) |", "|---|---:|---:|---:|---:|---:|"]
    for case in anomaly["cases"]:
        lines.append(f"| {case['pattern']}/{case['seed']} | {case['labeled_episodes']} | {case['missed_episodes']} | {case['false_alert_events']} | {case['normal_site_hours']} | {case['mean_detection_delay_hours']} |")
    lines += ["", "## Preserved legacy one-hour demand benchmark", "",
              report["selection"]["interpretation"], "",
              "Its validation selects the window on one-hour MAE only, with the original disjoint target splits. This measured-rate benchmark differs from the upgraded operational forecast; `selection.matches_operational_method` is false. The separate reserve evaluation validates the actual method/config.", "",
              "| Legacy final-test method | Origins | MAE(L) | RMSE(L) | Bias(L) |", "|---|---:|---:|---:|---:|"]
    for name, result in report["final_test"].items():
        lines.append(f"| {name} | {result['samples']} | {result['mae_l']:.3f} | {result['rmse_l']:.3f} | {result['bias_l']:.3f} |")
    lines += ["", "## Practical limits", ""]
    lines += ["- " + text for text in report["limitations"]]
    lines += ["", "Data/source hashes, split boundaries, candidates, per-origin margins, stress failures and method match remain in the JSON. Future truth never enters operational features, and the original generator was not retuned to make the repair pass.", ""]
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
    print(f"Legacy one-hour window: {report['selection']['selected_window_intervals']}; actual48h method: {report['reserve_timing']['selection']['operational_method']}")
    print("Wrote identical evaluation JSON artifacts and generated docs/EVALUATION.md")


if __name__ == "__main__":
    main()
