# JalRakshak

A water-operations dashboard for one hostel caretaker: reserve forecasts, the latest time to arrange supply, abnormal depletion, approved notices and recovery evidence.

**Working local prototype with simulated data.** Original implementation began October 1, 2026 and continued October 2. AWS infrastructure is included; cloud deployment, real sensors, caretaker validation and external messages have not been demonstrated. This early prototype cannot be represented as an eligible new event build under the previously reviewed project-start rule.

## Run

Use Python 3.13 and Node.js 22.18+ with npm. From the extracted project root:

```powershell
python scripts/run.py --setup
```

This creates .venv, installs pinned Python packages, installs the frontend lockfile, builds the interface and opens **http://127.0.0.1:8000**. Windows users can double-click START_APP.cmd. Later, `python scripts/run.py` starts without reinstalling. Press Ctrl+C to stop. The ZIP includes the built interface. No API keys are needed. Optional environment values must be set in the shell; .env is not automatically loaded.

Each browser receives an isolated persistent SQLite demo session, expiring after 24 hours. Reset affects only that session. The fictional 50,000 L hostel tank uses a 5,000 L reserve, 14-hour supply lead time and 3-hour buffer.

## Implemented workflow

- Measurement-anchored bounded tank balance; arrived inflow is reconciled once.
- Separate reserve breach and empty-tank times. Conservative deadline excludes unarrived supply and assumes 20% higher demand.
- Sustained abnormal-depletion detection, with provenance and timestamps.
- Read-only supply-delay and future-demand previews preserving observed history.
- Explicit notice approval bound to evidence, action and expiry; idempotent local inbox receipt.
- Recovery requires three fresh post-intervention readings, normal depletion and adequate planning margin. A repair claim alone does not resolve an incident.
- Deterministic evidence assistant and reproducible synthetic evaluation.

All supported inputs are simulated. Tank-level data cannot locate a physical leak. A notice is neither an external message nor a tanker booking. The sensitivity envelope is not a calibrated probability. No hidden model calls or invented environmental savings are presented.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe infra/check_template.py --check-source
cd frontend
npm run build
```

For development run the API on port 8000 and `npm run dev` in frontend on port 5173. Vite proxies /api locally; the built interface is served by FastAPI. API docs: /docs. See [architecture](docs/ARCHITECTURE.md), [evaluation](docs/EVALUATION.md), [deployment](docs/DEPLOYMENT.md) and [demo script](docs/DEMO_SCRIPT.md).

## Continue

Start a new AI with [AI_HANDOFF.md](AI_HANDOFF.md), [active checkpoint](docs/PROJECT_STATE.md) and [continuation prompts](docs/CONTINUE_PROMPTS.md). Use [REVIEW_THIS_PROJECT.md](REVIEW_THIS_PROJECT.md) for an independent assessment. The prep folder preserves earlier research and 18 historical prompts; its preparation-only phase is superseded.

Source and SVG interface assets are original. Winner repositories informed research only; restricted or unlicensed winner code was not incorporated. See [notices](THIRD_PARTY_NOTICES.md), [reuse audit](prep/research/REUSE_AUDIT.md) and LICENSE. Passing local checks cannot establish cloud execution, field reliability or an award.
