# Build plan and handoffs

Planning only. Begin implementation after the confirmed October 8 kickoff; verify the final cutoff instead of assuming a time.

## Execution order

| Prompt | Milestone | Gate before moving on |
|---|---|---|
| 00 | Permitted preparation | Rules checked; unknowns recorded; no submission code |
| 01 | Fresh repository and memory | Brief/contract/layout locked; truthful initial commit |
| 02 | Local vertical slice | POST observation → persisted state → browser |
| 03 | Early AWS slice | Actual API + DynamoDB path; hosting or candid eligible local fallback |
| 04 | Forecast and deadline | Hand-calculated cases; chronology; uncertainty/data states |
| 05 | Abnormal depletion and scenarios | Sustained anomaly; deterministic replay; provenance |
| 06 | Approval, alert, verification | Protected writes; failure truth; new readings required |
| 07 | Usability | One self-explanatory incident screen; small-screen and keyboard checks |
| 08 | Evaluation | Reproducible artifacts; baselines; final holdout evaluated without tuning |
| 09 | Optional Strands assistant | Tool evidence; no approval privileges; graceful fallback |
| 10 | Integration and reliability | Complete loop; cloud persistence; critical failures handled |
| 11 | Hostile judge review | Prioritized defects with smallest fixes |
| 12 | Repair and demo freeze | Reset + preflight + completed rehearsal; no remaining P0 |
| 13 | Submission materials | Verified public links; under-three-minute video; evidence audit |

R resumes an interrupted milestone. X cuts scope when behind. P coordinates bounded parallel work. A re-scopes to school air before implementation if that problem proves stronger.

## Time budget

These are planning budgets, not performance promises. On Oct 8 complete the local spine and attempt the AWS slice early. On Oct 9 complete the forecast/anomaly/action loop. On Oct 10 concentrate on usability, evidence, deployment repair, and mentor feedback. On Oct 11 rehearse, record, verify links, and submit early. Adjust to the actual kickoff/cutoff and available team hours.

If account access blocks cloud deployment, record it and proceed with a working AWS open-source route allowed by the rules. If the deterministic loop is incomplete, omit the assistant. If all core gates are green, spend remaining time on clarity and reproducibility rather than a second domain.

## Parallel ownership

Independent agents can help, but dependencies still exist.

| Worker | Owns | Must not edit |
|---|---|---|
| Integrator | Contracts, shared state, dependency locks, CI, integration, deployment | No blind overwrite of worker changes |
| Forecast worker | Forecast module and its focused tests | API contracts, frontend, shared checkpoint |
| UI worker | Frontend against agreed contract/sample responses | Backend, infra, contract generation, shared checkpoint |
| Reviewer/evidence worker | Static review and evaluation/report files assigned to them | Running workers' implementation files |

Freeze the API contract after Prompt 02. On a shared filesystem, assign disjoint directories; subagents are not isolated worktrees. Separate human Codex chats need worktrees or explicit file ownership. Do not ask several workers to update the same PROJECT_STATE file. The integrator collects their handoffs and writes one truthful checkpoint.

Every handoff says: owned files, behavior changed, exact checks/results, interface expectations, unresolved failures. Integrate and run the affected workflow before marking the combined milestone complete.

## Active memory after kickoff

Keep these small and purposeful:

- `AGENTS.md`: stable constraints and verification conventions.
- `docs/PROJECT_BRIEF.md`: locked mission, scope, terminology, architecture.
- `docs/PROJECT_STATE.md`: current milestone, actual done/next/blockers, commands, evidence.
- `docs/DECISIONS.md`: architectural changes with reasons.
- `docs/EVIDENCE.md`: claim → artifact/test/recording and measured/simulated status.
- `docs/DEMO_SCRIPT.md`: final click path, narration, reset, fallbacks.

Aim for a checkpoint of roughly one page. Read it at session start and milestone boundaries, not before every line edit. Open other docs when the task requires them. [Durable project memory](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex), [concise contextual instructions](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra), [AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

After kickoff, choose real commands and write them into the checkpoint: backend tests, frontend typecheck/build, SAM validation, demo reset/check. Windows is the current host. Prefer documented Python/npm/PowerShell commands; do not make Unix `make` the only route.

For an extracted archive on another host, detect OS/shell/tooling and adapt commands. Keep supported platform instructions explicit; local success on Windows does not establish Linux/macOS setup success. Lambda packaging still targets the chosen Linux runtime.

## Recovery checkpoint shape

```text
Updated / branch / commit / dirty files:
Current milestone:
Implemented and observed:
Tests/checks: command → result → artifact
Decisions changed:
Known failures and limitations:
External blockers and owner:
Next exact action:
```

Save this at a milestone end or interruption. Never set a green gate because a worker said the code “should work.”
