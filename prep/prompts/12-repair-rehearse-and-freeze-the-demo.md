# Prompt 12 — Repair, rehearse, and freeze the demo

**Result:** a repeatable under-three-minute path with no unresolved P0.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, docs/JUDGE_REVIEW.md, and actual
demo/deployment evidence. Fix P0 issues first and material P1 issues within
the remaining event time. Preserve working interfaces. After the fixes,
enter DEMO FREEZE: no new features, architecture migration or dependency
upgrades except an essential P0 repair.

Create small Windows-compatible demo reset/seed/check commands and a
preflight that validates required endpoints/config/fixtures without
printing secrets. Reset only disposable demo state; never erase real
observations or send notifications. Keep seed/replay deterministic and
visibly simulated. Fail loudly on missing dependencies or service access.

Rehearse the exact flow from a reset: healthy reserve → sustained anomaly
→ shifted deadline → six-hour delay preview → explicit request approval
→ honest receipt/publication proof → subsequent readings → verification
→ one evaluation result and limitation → actual AWS execution/use.
Do three clean rehearsals if failures/changes warrant them, confirming
repeatability and reset behavior rather than rerunning broad suites.

Write docs/DEMO_SCRIPT.md with exact clicks, narration, expected states,
actual numbers/evidence references, reset and fallback. Aim for 2:45–2:55.
Fallback is truthful: provider failure uses deterministic explanation;
blocked AWS action is shown failed/pending or the real local AWS-tool route,
never edited into an apparent success. Simulated intervention cannot claim
a physical repair. Check production build and the actual URL if claimed.

Update checkpoint/evidence and report readiness for frontend, backend,
AWS, scenarios, notification, assistant/fallback, verification, tests and
deployment, plus remaining P0/P1. If any P0 remains, keep working on the
smallest repair while time permits; do not call the demo ready. Commit
repairs. Once gates are green, freeze and move to Prompt 13.
```
