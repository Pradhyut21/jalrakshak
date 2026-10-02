# JalRakshak

A working local water-operations app for one caretaker and one tank: record storage, account for arrivals, plan reserve protection, review a notice and verify recovery with fresh readings.

**Version 0.2.** Start with the simulated demonstration, or open an empty local workspace for operator-entered tank logs. Actual entries remain unverified; no connected sensor, validated caretaker pilot or cloud deployment is claimed.

## Run

Use Python 3.13 and Node.js 22.18+ with npm. From the extracted project root:

```powershell
python scripts/run.py --setup
```

Windows users can double-click START_APP.cmd. Later, `python scripts/run.py` starts without reinstalling. Open **http://127.0.0.1:8000**; Ctrl+C stops the server. The ZIP includes the built interface. No API keys are required. Setup needs internet; optional environment values must be set in the shell.

If another application uses port8000, run `python scripts/run.py --port 8012` and open http://127.0.0.1:8012. The launcher keeps the other application running and reports an occupied port clearly.

## Use actual logs

Open **Data & settings**, enter your tank capacity, reserve, supply lead time, buffer and reading-error assumption, and explicitly choose an empty observed workspace. Demo records are cleared. Add observations with actual timestamps, or preview and import CSV with `observed_at,volume_l` and optional `reading_id`. Import recorded arrivals together with logs when necessary to explain level increases. Future plans are separate from actual arrivals.

Observed workspaces use server wall time and become UNKNOWN when observations are stale or inadequate. Storage remains on this computer, behind a browser session cookie. Export JSON backups. The latest 1,000 readings and at most 200 supply records are retained; the session expires after 30 days without a write. This is local record collection, not a production identity system. Cloud guest deployments accept simulated data only.

## Decisions and evidence

- Forecasts reconcile arrived water once and distinguish reserve crossing from an empty tank.
- A local-hour demand profile and empirical upper-demand envelope replace the old constant-rate 20% margin. The planning deadline subtracts delivery lead time and buffer. Unsupported hours and measurement-error assumptions are exposed.
- Planned supply is conditional and cannot extend the upper-envelope deadline.
- Three high intervals open an abnormal-depletion incident. A transient UNKNOWN view recovers from stored incident facts when usable readings return.
- A proposal requires explicit approval bound to its evidence revision and expiry. Receipt means the notice was saved locally; it does not book supply.
- Recovery requires three fresh normal post-intervention readings and adequate modeled margin. A repair claim alone cannot resolve an incident.

The deadline is assumption-dependent. In the original synthetic 48-hour holdout, late event predictions improved from 53/120 to 0/120. Untuned stress cases still contain 12 late predictions among 1,232 true crossings and substantial early-warning tradeoffs. The broader detector evaluation contains false alerts. See [evaluation](docs/EVALUATION.md); synthetic results do not establish field reliability.

## Verify and continue

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe infra/check_template.py --check-source
```

Build the interface with `npm ci` and `npm run build` in frontend. On Windows install the test browser with `.venv/Scripts/python.exe -m playwright install chromium`, then run `.venv/Scripts/python.exe scripts/browser_check.py http://127.0.0.1:8012` against the running app (adjust the URL to its port).

Read [AI_HANDOFF.md](AI_HANDOFF.md) and [active checkpoint](docs/PROJECT_STATE.md) to continue. [REVIEW_THIS_PROJECT.md](REVIEW_THIS_PROJECT.md) provides an independent review entry; [review fixes](docs/REVIEW_RESPONSE.md) map the reported defects to changes and remaining gaps.

Original code and SVG assets; reference repositories informed research only. [Dependency notices](THIRD_PARTY_NOTICES.md) and LICENSE are preserved. Development began October 1, 2026 before the published October 8 event start; do not assume eligibility or backdate history. AWS source, external notifications, sensor accuracy and real caretaker usefulness remain unverified.
