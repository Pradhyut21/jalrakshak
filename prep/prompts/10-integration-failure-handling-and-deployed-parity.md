# Prompt 10 — Integration, failure handling, and deployed parity

**Result:** the whole implemented loop behaves truthfully locally and in the claimed runtime.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, actual deployment notes and demo
path. Complete integration and repair failures; do not add stretch features.

Run the full flow against local persistent storage and the actual deployed
AWS path where authorized: healthy → sustained excess → changed forecast
→ delayed-supply preview → proposal → approval → notification status →
post-intervention readings → deterministic verification → incident evidence.
Prove cloud persistence across fresh invocations. Ensure latest evidence
version wins when two updates race; old forecasts can't overwrite new ones.

Check targeted failure behavior: stale/missing readings, provider timeout,
notification failure, duplicate submissions, API outage, denied writes,
unauthorized cross-site access, and reset while a request is in flight.
Guest demo/reset/seed cannot touch real operational state or notification
targets. Do not leak credentials or personal details in logs/artifacts.

Add only useful operational logs/health evidence: request/action/run IDs,
source timestamps, transitions and failure reasons. Add a scheduler only
if stale-state/verification refresh actually needs it; give it bounded
idempotent work. Do not add Step Functions solely for the sponsor diagram.

Run backend checks, frontend typecheck/build, SAM validation, and critical
integration/browser checks once, rerunning affected gates after repairs.
If account/service blockers remain, preserve and demonstrate the real
AWS open-source route and label missing cloud proof. No fake service badges.

Update commands/README, deployed URL and evidence where real, checkpoint,
and known limitations. Inspect the diff and commit. Next Prompt 11.
```
