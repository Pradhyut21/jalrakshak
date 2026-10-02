# Project checkpoint

Updated: 1 October 2026, Asia/Kolkata.

## Current status

- Phase: PREPARATION. Product implementation has not begun.
- Workspace: `D:\SAANS`; it was empty and was not a Git repository on initial inspection.
- User clarified that the three GitHub links are previous reference projects. No earlier project of the user's own has been supplied or reviewed.
- User authorized choosing the stronger direction after research.
- User subsequently authorized downloading useful upstream sources, choosing reuse versus original implementation, and creating a context-preserving reviewable ZIP. Do not ask for that choice again.
- Recommendation: JalRakshak, Heat and Water track, one hostel caretaker. This is a proposed choice awaiting real problem validation, not a completed product.
- Reference repositories reviewed statically. Their applications and test suites were not executed by this research run.
- Complete planning deliverables saved: project brief, source-linked strategy/research, build plan, 18 prompts and individual copies, preparation readiness, and document verification report. Independent review corrections have been applied.
- Portable packaging adds README, AI handoff, neutral reviewer instructions, evidence-based rubric, license/reuse audit, machine-readable stage and file-hash manifest. Archive verification results are recorded separately from application readiness.
- No AWS account access, credentials, Bedrock entitlement, deployment, notification destination, real tank observations, or user interviews verified.

## Decisions and reasons

- Keep the folder name SAANS; use JalRakshak as the provisional product name. Folder naming should not decide the track.
- Favor water operations for a controlled visible scenario, a calculable action deadline, and an incident that can be verified with later readings. Air remains a fallback for a stronger firsthand problem.
- Start with simple forecast baselines and a modular Python API, not distributed services or a heavy ML stack.
- Deploy the smallest real AWS slice early during the event; do not discover account restrictions on the last evening.
- Use a short root AGENTS file and one active checkpoint. Read specialized docs as needed rather than reloading every document at every edit.
- Selected reuse route: original JalRakshak domain code with mature licensed dependencies. Avoid whole-product forks that add unrelated infrastructure or uncertain rights. Exact license evidence is in `research/REUSE_AUDIT.md` and `research/DEPENDENCY_LICENSES.md`.
- Permitted reference checkouts are separate from the submission root under the original host's `D:\SAANS-References`. Do not bundle them into the preparation ZIP. A receiving AI need not access that cache to resume from the included reports.

## Source status

- Official rules, event overview, schedule, announcement, and First Commit winners page: fetched on October 1. Links and conflicts appear in `research/EVENT_RULES.md`.
- Beacon, CampusEvac, Fraud Risk Manager: static code/document review at pinned commits; see individual research reports.
- Additional licensing audit: FastAPI/Vite MIT license files downloaded at pinned revisions; Beacon and Strands reference snapshots and SAM license/notice metadata inspected separately. No reference application or test was run.
- Open-Meteo: one keyless Delhi air-quality query succeeded during source research. It is modeled CAMS data, not a school sensor reading or official Indian AQI. Details in the rules/source report.
- Proposed water data: no real site data yet. Demo fixtures must be generated after kickoff and remain labeled simulated.

## Local tools observed

- Commands found: Git 2.52.0.windows.1, Python 3.13.5 (`C:\Program Files\Python313\python.exe`), Node v22.18.0, npm 10.2.5, rg.
- `aws` and `sam` were not found by command discovery. This does not establish account status or whether binaries exist elsewhere.
- Runtime/package compatibility has not been tested. Exact command versions are recorded in `READINESS.md`.

## Open questions

- Final official kickoff time and submission cutoff: verify announcement/form. Schedule says hours pending; DTU Luma says Oct 11, 8 PM IST.
- Team size and available hours; plan works sequentially and can delegate after contracts stabilize.
- Does a caretaker actually have useful tank readings and reliable supply lead times? Use the interview checklist.
- AWS account verification, authorized region, cost limit, confirmed notification destination.

## Next action

Research, prompt creation, and tooling inventory are complete. Run **Prompt 00** to close the remaining account/user preparation unknowns listed in `READINESS.md`. At the official start, run **Prompt 01**, creating the fresh submission repository and `docs/PROJECT_STATE.md` with truthful start status. Never mark a build gate complete from these planning documents.

## Recovery rule

If a new chat starts, read this file and AGENTS.md, then inspect files/Git status. If `docs/PROJECT_STATE.md` exists after kickoff, it takes over as the active checkpoint. Continue the next incomplete milestone; do not rebuild finished work.

Portable note: `D:\SAANS` and local tool paths are dated observations from the original machine. On another host, use the extracted root and redetect OS, shell, tools, accounts and current event time. Begin with root `AI_HANDOFF.md`.
