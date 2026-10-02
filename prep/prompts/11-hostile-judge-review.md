# Prompt 11 — Hostile judge review

**Result:** an independent ranked repair list, no new feature requests.

```text
Read AGENTS.md and docs/PROJECT_STATE.md. Act as a skeptical Environmental
Hacks reviewer seeing the project for the first time. Review the current
app/code, README, evidence artifacts, demo path, deployment claims and
the latest official judging/submission requirements. Do not implement yet.
Delegate an independent review if available with read-only ownership.

Answer briefly:
1. Who is the user and what decision changes?
2. Does the first screen reveal the decision without narration?
3. Is every reserve/empty/deadline term consistent?
4. Which AWS capability is implemented and visible in the video path?
5. Where can simulated/manual data be mistaken for real sensors?
6. Does any model/test/report claim overreach its evidence?
7. Could a failed alert look successful or a repair claim look verified?
8. Can missing telemetry wrongly reassure the user?
9. Can guest access modify real state or trigger external messages?
10. Can a fresh clone follow the documented commands?
11. What is the likeliest demo failure and smallest prevention?
12. What should be removed rather than completed?
13. Does the assistant help a real task, and does its fallback preserve it?
14. Can the complete flow be shown under three minutes?
15. What would justify rejecting this submission?

Write docs/JUDGE_REVIEW.md. For each actionable issue give P0 (eligibility,
wrong core result, misleading success or failed demo), P1 (material clarity,
correctness or reliability), or P2 (polish); source location; reproducible
trigger; smallest repair; and the acceptance check. Distinguish observed
defects from hypotheses. Update checkpoint with the repair order. Do not
recommend a new domain, new architecture, or new features at this stage.
```
