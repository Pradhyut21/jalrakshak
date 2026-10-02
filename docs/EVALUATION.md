# Synthetic evaluation

Generated on 2 October 2026. No real sensor or campus data was used.

Synthetic holdout: recent-mean (1 intervals) next-hour demand MAE 149.1 L across 166 origins. No real sensor data or calibrated probability.

Run from the extracted project root:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
```

The authoritative artifact is `artifacts/evaluation.json`; the same bytes are copied to `backend/app/data/evaluation.json` for packaged Lambda/API use.

Chronological generation separates evaluator-only demand truth from operational readings. At each origin, inputs contain only readings and arrivals already observed/received. The forecast target is next-hour consumption in litres, not a claim of 48-hour forecast accuracy.

Window selection uses validation MAE only. One-hour target windows do not overlap splits; boundary origins are purged. Earlier observed history remains available to later origins, as it would in use.

A one-interval recent mean is exactly the last-rate baseline; no complexity advantage is claimed.

| Final-test method | Origins | MAE (L) | RMSE (L) | Bias (L) |
|---|---:|---:|---:|---:|
| recent_mean_selected | 166 | 149.098 | 227.340 | 2.314 |
| last_rate | 166 | 149.098 | 227.340 | 2.314 |
| earlier_median | 166 | 266.060 | 393.709 | -34.770 |

Detector: 1 labeled holdout episode(s), 0 missed, 0 new false-alert event(s) across 159 labeled-normal site-hours.

Delay is measured from the first observed abnormal interval. A continued alert counts once; the three-interval persistence rule intentionally delays activation. See artifact episode records and denominator definitions.

## Practical limits

- Synthetic assumptions and a single fixed seed; no field validation or real campus readings.
- Final test is reporting only; selection uses validation, never holdout results.
- Reading and demand error bounds are simulator assumptions, not calibrated confidence intervals.
- No measured water savings, physical leak localization, supplier response or health effect is established.
- Detector threshold 1.5× and persistence three intervals are fixed rules; not fitted or calibrated on this holdout.
- The baseline comparison reports unfavorable results if a simpler method wins.

Next-hour demand metrics do not validate 48-hour reserve timing under uncertain future supply. Arithmetic behavior is covered separately by domain tests.

Data/source hashes, split boundaries, candidate validation results, and method match are stored in the JSON. The generator was not retuned after seeing the holdout.
