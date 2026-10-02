# Prompt 05 — Abnormal depletion and deterministic scenarios

**Result:** a visible incident goes through the real ingestion/forecast path.

```text
Read AGENTS.md and docs/PROJECT_STATE.md. Implement sustained abnormal
depletion detection and a controlled demo replay around the current core.

Preserve Prompt 04's frozen forecast-evaluation history. Generate additional
incident scenarios chronologically with a fixed seed and separate detector
train/validation/final-test windows; do not replace a forecast holdout to
improve results. Model:
morning/evening demand, observed deliveries, realistic measurement noise,
and separate scenario truth. Start with healthy, sustained excess usage,
delayed delivery, intervention followed by normal demand, and new delivery.
Keep the physics coherent with capacity, reserve, supply, and consumption.
Do not tune fixtures until the favored model/detector wins. Store labels
only in evaluation/scenario metadata, never operational feature fields.

Use past residual dispersion plus persistence (e.g. sustained robust-score
or EWMA evidence), with configurable thresholds selected on validation.
Isolated noise should not repeatedly alert. Missing/gapped/irregular data
must not count as evidence of normal consumption. Report excess use as
abnormal depletion with possible causes, not a confirmed physical leak.
With aggregate tank data, do not identify a block or pipe. Use block labels
only when actual simulated/genuine submeter readings exist and are labeled.

Provide demo reset/seed/replay endpoints restricted to isolated simulated
sessions and bounded resources. Public guests have no real notification
rights; authenticated owner rehearsals may send clearly simulated alerts
only to an authorized confirmed test destination after concrete approval.
The scenario
must insert readings through the same ingestion API/domain path. UI cannot
directly set anomaly/forecast/resolved values. Record the replay clock and
provenance so future simulated observations don't look like real telemetry.

Add a clearly labeled Demo Lab. Sustained excess usage should move the
reserve forecast/deadline and evidence; repair replay supplies later normal
readings but cannot simply clear the incident. Test determinism, no future
truth leakage, noise, gaps, sustained onset, and duplicate replay steps.

Run relevant checks, update data provenance/model notes/state/evidence,
commit this milestone. Next Prompt 06.
```
