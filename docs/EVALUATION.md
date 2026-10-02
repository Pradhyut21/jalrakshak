# Synthetic evaluation

Generated on 2 October 2026. No real sensor or campus data was used.

Synthetic 48h holdout: frozen legacy 53/120 late reserve predictions; upgraded 0/120, mean earliness 5.70h. Legacy one-hour MAE remains 149.1L. Synthetic stress and failures are reported separately; no field accuracy or calibrated probability.

Run from the extracted root with the application's Python environment:

```text
python scripts/evaluate.py
```

The authoritative [JSON artifact](../artifacts/evaluation.json) is copied byte-for-byte to `backend/app/data/evaluation.json` for packaged API/Lambda use. Reproduction tests check both bytes and source/data hashes.

## Original generator and frozen comparison

The original seed42,504-hour generator is unchanged. Its canonical output SHA-256 is `688ad1143797468282f2e051acd7bc9a870f5272633a6ce9164143393f4e23c0`. Its original one-hour splits and demand metrics remain available; they are **not** the upgraded method's48-hour accuracy score.

For reserve timing, every origin has48 complete future demand intervals. Train origins72–119 end by167; validation169–287 ends by335; heldout337–456 ends by504. Full future targets never cross the next split's first origin. Origins overlap within each split and are correlated, so120 windows are not120 independent experiments.

Truth is the fractional first reserve crossing after the observed level, subtracting evaluator-only future demand. No future refill is credited. Past arrived/received deliveries reconcile measured depletion, but future simulator decisions and labels are never forecast inputs. Demand is spread uniformly within each truth hour; this is a counterfactual, not actual refill-managed tank storage.

Frozen legacy predicts a constant last-interval rate×1.2 from measured storage. The upgrade projects a historical local-hour profile, an empirical upper-demand envelope and a recent upper-rate floor. It also starts conservative storage at measured level minus declared error:180L here,300L in noisy stress. The paired comparison therefore includes both the profile and explicit storage safeguard. These bounds are simulator assumptions, not confidence intervals.

A normal window has no labeled abnormal demand at its origin or any of the48 following intervals. Our endpoint, observed-anchor and whole-window protocol produces65 normal windows and27 legacy late predictions; it does not force the externally reported63/20 counts for which no executable protocol was supplied.

## Validation selection and operational match

Lookback168h,upper quantile0.9 and minimum bucket support2h were fixed before holdout reporting. Only the conservative multiplier candidates1.0/1.1/1.2 were compared on119 validation origins. Selection minimizes late+missed+unknown penalties, then positive mean earliness, then the smaller multiplier. The JSON preserves all candidates and the explicit unknown penalty.

Selected/frozen config: `{"conservative_multiplier":1.0,"lookback_hours":168,"minimum_bucket_hours":2,"upper_quantile":0.9}`. Operational method `time_of_day_empirical_envelope` matches the evaluated method/config. Drift raises an error; a label alone cannot establish a match.

| Multiplier | Validation windows | Late | Missed | UNKNOWN | Mean early(h) | P90 early(h) |
|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 119 | 0 | 0 | 0 | 7.796 | 12.508 |
| 1.1 | 119 | 0 | 0 | 0 | 8.371 | 13.167 |
| 1.2 | 119 | 0 | 0 | 0 | 8.860 | 13.676 |

The selected validation envelope covers 99.965% of hourly points and 118/119 complete windows. Point coverage is separately reported and was not substituted into selection after inspecting these outcomes.

## Untuned48-hour original holdout

| Method/slice | Windows | True events | Censored | Paired timing | UNKNOWN | Late | Missed within48h |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy/all_windows | 120 | 120 | 0 | 120 | 0 | 53 | 0 |
| legacy/normal_windows | 65 | 65 | 0 | 65 | 0 | 27 | 0 |
| upgraded/all_windows | 120 | 120 | 0 | 120 | 0 | 0 | 0 |
| upgraded/normal_windows | 65 | 65 | 0 | 65 | 0 | 0 | 0 |

| Method/slice | Mean late(h) | Max late(h) | Mean early(h) | P90 early(h) | Max early(h) | Hourly coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy/all_windows | 3.883 | 17.729 | 4.233 | 9.369 | 13.597 | 84.861% |
| legacy/normal_windows | 3.939 | 17.729 | 3.672 | 9.045 | 10.816 | 84.615% |
| upgraded/all_windows | 0.000 | 0.000 | 5.700 | 13.848 | 15.454 | 99.983% |
| upgraded/normal_windows | 0.000 | 0.000 | 5.744 | 13.690 | 14.723 | 100.000% |

Upgraded warnings classify 120/120 planning deadlines as already passed, while truth does so for 80/120. Lead14h plus buffer3h is subtracted from both true and predicted reserve times; record-level margins are retained in the JSON. Early deadlines can incur avoidable calls or deliveries.

Coverage means simulated conservative volume is at or below no-refill truth at48 hourly checkpoints, among available forecasts. UNKNOWN availability and censored truth remain separate. A right-censored window has no true crossing within48h; no exact timing error is invented for it. Numerical lateness tolerance is one second.

## Additional independent-seed synthetic stress

These twelve cases use predeclared seeds73,101,211 across daily peaks, upward trend, low usage with noisy readings, and shifting refill thresholds/amounts. They are synthetic stresses, not measured realistic performance. None selects or retunes the frozen configuration. Full metadata, hashes, legacy scores and upgraded late/missed examples are in the JSON.

| Pattern/seed | Legacy late | New late | New max late(h) | UNKNOWN | Censored | Mean early(h) | P90 early(h) | Censored predicted events |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| daily_peaks/73 | 72 | 0 | 0.000 | 0 | 0 | 7.411 | 13.486 | 0 |
| daily_peaks/101 | 72 | 2 | 0.305 | 0 | 0 | 7.848 | 13.698 | 0 |
| daily_peaks/211 | 69 | 3 | 0.206 | 0 | 0 | 7.823 | 13.955 | 0 |
| upward_trend/73 | 40 | 2 | 0.386 | 0 | 0 | 2.965 | 8.429 | 0 |
| upward_trend/101 | 41 | 3 | 0.133 | 0 | 0 | 3.080 | 8.772 | 0 |
| upward_trend/211 | 46 | 2 | 0.930 | 0 | 0 | 3.050 | 8.488 | 0 |
| noisy_low_usage/73 | 3 | 0 | 0.000 | 0 | 69 | 28.306 | 37.053 | 69 |
| noisy_low_usage/101 | 3 | 0 | 0.000 | 0 | 70 | 28.617 | 37.808 | 70 |
| noisy_low_usage/211 | 4 | 0 | 0.000 | 0 | 69 | 28.569 | 37.214 | 69 |
| refill_shifts/73 | 46 | 0 | 0.000 | 0 | 0 | 8.939 | 15.966 | 0 |
| refill_shifts/101 | 47 | 0 | 0.000 | 0 | 0 | 8.979 | 15.784 | 0 |
| refill_shifts/211 | 47 | 0 | 0.000 | 0 | 0 | 8.860 | 15.672 | 0 |

Combined stress exposure: 1440 windows, 1232 truth crossings, 208 censored, 0 UNKNOWN, 12 late predictions and 0 missed-horizon events. Mean lateness among late predictions:0.213h; maximum:0.930h. Individual cases and overlap remain visible; this pooled count is not independent-sample confidence.

Zero lateness on the original holdout does not generalize to these stresses. The noisy-low-usage bound can produce very early warnings and crossings where truth is censored; this operational cost remains visible. No zero-failure guarantee is made.

## Expanded anomaly episodes

Across original holdout plus12 independent pattern/seed cases: 13/13 episodes detected, 0 missed; 44 new false-alert events/1515 labeled-normal site-hours (0.029043/hour). Total monitored exposure:1606 site-hours. Mean delay among detected episodes:1.385h; P90:2.000h; maximum:2h.

Detection here means an active alert overlaps a labeled episode. 3 episodes were already alerted before onset; 10 have a new alert transition during the episode. An overlapping alert can therefore give zero delay without being a new correct warning. Both counts and first-new-alert delays are retained per episode.

A preceding state prevents split-boundary double counting. A continued alert counts once; overlap delay begins at the first observed labeled abnormal interval. Misses are counted separately, not omitted from the denominator. The detector was not retuned on these stresses.

| Dataset/seed | Episodes | Missed | False alert events | Normal site-hours | Mean detected delay(h) |
|---|---:|---:|---:|---:|---:|
| original_seed42/42 | 1 | 0 | 0 | 159 | 2.0 |
| daily_peaks/73 | 1 | 0 | 9 | 113 | 2.0 |
| daily_peaks/101 | 1 | 0 | 9 | 113 | 2.0 |
| daily_peaks/211 | 1 | 0 | 8 | 113 | 2.0 |
| upward_trend/73 | 1 | 0 | 6 | 113 | 0.0 |
| upward_trend/101 | 1 | 0 | 5 | 113 | 0.0 |
| upward_trend/211 | 1 | 0 | 5 | 113 | 0.0 |
| noisy_low_usage/73 | 1 | 0 | 2 | 113 | 1.0 |
| noisy_low_usage/101 | 1 | 0 | 0 | 113 | 1.0 |
| noisy_low_usage/211 | 1 | 0 | 0 | 113 | 2.0 |
| refill_shifts/73 | 1 | 0 | 0 | 113 | 2.0 |
| refill_shifts/101 | 1 | 0 | 0 | 113 | 2.0 |
| refill_shifts/211 | 1 | 0 | 0 | 113 | 2.0 |

## Preserved legacy one-hour demand benchmark

A one-interval recent mean is exactly the last-rate baseline; no complexity advantage is claimed.

Its validation selects the window on one-hour MAE only, with the original disjoint target splits. This measured-rate benchmark differs from the upgraded operational forecast; `selection.matches_operational_method` is false. The separate reserve evaluation validates the actual method/config.

| Legacy final-test method | Origins | MAE(L) | RMSE(L) | Bias(L) |
|---|---:|---:|---:|---:|
| recent_mean_selected | 166 | 149.098 | 227.340 | 2.314 |
| last_rate | 166 | 149.098 | 227.340 | 2.314 |
| earlier_median | 166 | 266.060 | 393.709 | -34.770 |

## Practical limits

- All inputs are synthetic; original fixed seed plus 12 predeclared pattern/seed stress cases. No field validation or real campus readings.
- Final test is reporting only; selection uses validation, never holdout results.
- Reading error bounds and empirical demand envelopes are explicit simulator/planning assumptions, not calibrated confidence intervals.
- No measured water savings, physical leak localization, supplier response or health effect is established.
- Detector threshold 1.5× and persistence three intervals are fixed rules; not fitted or calibrated on this holdout.
- The baseline comparison reports unfavorable results if a simpler method wins.
- Overlapping48h windows within a split are correlated; counts do not establish independent-sample statistical confidence.
- No-future-refill scoring is a counterfactual; actual simulator refills may prevent the predicted shortage.
- Early warnings can be operationally costly; earliness, already-passed deadlines, censored truth and missed predictions are retained.
- The old one-hour MAE is unchanged and is not relabeled as improved48h operational accuracy.

Data/source hashes, split boundaries, candidates, per-origin margins, stress failures and method match remain in the JSON. Future truth never enters operational features, and the original generator was not retuned to make the repair pass.
