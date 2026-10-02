# Prompt 04 — Reserve forecast and last-action deadline

**Result:** the core decision, with correct accounting and honest uncertainty.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, and the numerical contract in
docs/PROJECT_BRIEF.md. Implement deterministic forecast/decision modules
and GET /sites/{id}/forecast without an LLM.

Estimate usage only where observed storage changes and recorded inflow
make the estimate identifiable. Mark insufficient/ambiguous history.
Compare recent-average and same-hour historical-median baselines. Add a
small EWMA/trend candidate only if evidence justifies it. Features at an
origin use only data observed and available by that origin, including
delivery knowledge as it stood then. Unknown future weather/inflow must
not appear as known features. Never expose scenario truth/labels to logic.

Anchor projection at the latest measured volume/time. Add only later
inflow not already included in that measurement; a new observation resets
the anchor. Infer historical consumption with inflow inside the exact
observation interval and a documented timestamp convention. Keep delivery
and other-inflow ledgers disjoint; distinguish measured and projected-now
volume. Do not double count deliveries or abnormal usage. Bound storage
to [0, capacity], recording overflow and unmet demand separately. Return
reserve_breach_at and empty_at separately, no_breach_within_horizon when
applicable, and UNKNOWN for stale/insufficient input. A future delivery
is a conditional plan, not arrived water; show a conservative supply case.

latest_action_at = conservative reserve breach - supply lead time -
safety buffer. Keep overdue deadlines overdue. Use explicit demand/supply
sensitivity scenarios first; don't call them calibrated confidence bounds.
Persist the forecast origin, evidence version, method, assumptions, and
provenance. Show source age and key assumptions in the operations page.

If sufficient real history is absent, generate the first minimal seeded
chronological evaluation history now, visibly simulated with separate truth
metadata. Establish partitions only after the dataset exists and record
its fingerprint. Create train/validation/final-test partitions with purging
where target windows overlap. Select method on validation only; freeze
test data for Prompt 08. Verify hand-computed constant/zero use, breached
reserve, missing inflow, delayed supply, capacity overflow, no crossing,
out-of-order observations, stale readings, and midnight/timezone cases.

Run relevant checks; document real results and limitations. Update state,
evidence, assumptions and commands; make a scoped commit. Next Prompt 05.
```
