# Prompt 08 — Evaluation and claims from one source of truth

**Result:** reproducible evidence, including unfavorable results.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, data provenance, forecast/detector
selection notes, and frozen split definitions. Build a reproducible
evaluation report; do not add product features or optimize on test data.

Verify chronological generation and point-in-time feature availability
at each forecast origin, not merely ordered split timestamps. Assert
future readings/deliveries and scenario labels can't reach features.
Train/select/tune only on train/validation. Report the untouched final
holdout once. Do not change the selected method because test results
favor a different one; disclose the finding and prospective next step.

Write artifacts/evaluation.json as the authoritative output; generate
human tables/README figures from it. Include seed, code/data hash, windows,
origin/horizon, number of samples, split boundaries, missing-data handling,
method chosen and why. Compare baselines and candidate even if the baseline
wins. MAE must specify volume or usage target and unit. Report reserve-
breach timing error only for measurable events; report censoring/no-event
counts separately. Include anomaly delay, false alerts per site-hours,
missed labeled scenarios, and known confounders.

For scenario impact, share starting state, seed, exogenous baseline demand,
supply and noise draws across intervention/no-intervention branches. Change
only the declared intervention effect (e.g. repair reduces excess use;
extra delivery adds inflow), documenting that effect as an assumption.
Compute shortage duration from unmet demand, separate from reserve breaches.
Report warning margin,
projected shortage duration and estimated excess litres with explicit
SIMULATED/PROJECTED labels. Do not call them observed water savings.

Use independent hand-calculated examples for metric arithmetic. Check
API/UI/report values against the JSON artifact to prevent documentation
drift. Document manual/synthetic data limits, no confirmed leak localization,
no guarantee of supplier response, uncertainty, and auth/demo boundaries.

Update model notes, provenance, EVIDENCE, README, and checkpoint with actual
results. Run evaluation and targeted checks; commit. Next 09 only if core
and deployment/equivalent AWS gates are green; otherwise proceed to 10.
```
