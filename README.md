# JalRakshak

**Plan water supply before the reserve runs low. Follow an incident through to fresh-reading recovery.**

For a hostel caretaker managing one tank, arranging water takes time. JalRakshak combines storage readings, recorded arrivals and delivery lead time into a planning deadline, flags sustained abnormal depletion, and keeps a clear trail of decisions and subsequent observations.

**Version 0.2.2 · working local prototype.** Try a simulated demonstration or start an empty workspace for operator-entered tank logs. Caretaker usefulness, sensor accuracy and water savings have not been validated.

[![Watch the JalRakshak narrated demo](docs/media/demo-poster.jpg)](docs/media/JalRakshak-Demo.mp4)

**[Watch the 2:54 narrated demo](docs/media/JalRakshak-Demo.mp4)** · [22-second launch clip](docs/media/JalRakshak-Launch.mp4) · [Transcript and video evidence](docs/DEMO_VIDEO.md)

*October 11 interface capture with fictional, simulated tank readings. Synthetic Hindi-preset narration in English; no human recording is claimed. Download the MP4 if GitHub does not play it inline.*

## Follow one complete incident

1. **Record:** enter timestamped storage readings and actual arrivals, or use the isolated demo.
2. **Plan:** inspect the reserve forecast and action deadline, which account for supply lead time, buffer and declared reading error. Preview a late delivery without changing the records.
3. **Review:** sustained abnormal depletion opens an incident. Review the exact notice and explicitly approve it into the local inbox.
4. **Check recovery:** record an intervention and add fresh observations. Three normal post-intervention readings plus adequate modeled margin are required to resolve the incident.

Missing or stale evidence produces **UNKNOWN**. A notice receipt records a local decision; a repair claim alone cannot establish recovery.

React/TypeScript/Vite interface · FastAPI/Pydantic backend · SQLite local storage · optional DynamoDB/Lambda source. Explanations use deterministic computed facts; no language model is involved.

## Run locally

Use Python 3.13 and Node.js 22.18+ with npm. From the extracted project root:

```powershell
python scripts/run.py --setup
```

Windows users can double-click START_APP.cmd. Later, `python scripts/run.py` starts without reinstalling. Open **http://127.0.0.1:8000**; Ctrl+C stops the server. The ZIP includes the built interface. No API keys are required. Setup needs internet; optional environment values must be set in the shell.

If port 8000 is occupied, run `python scripts/run.py --port 8012` and open http://127.0.0.1:8012.

In the demo, try **Excess usage → Review supply request → approve → Repair + readings**, then inspect **Incident history**. Generated readings remain visibly simulated; approval saves a local receipt and does not contact a supplier.

## Verification you can inspect

| Evidence | Observed scope |
|---|---|
| [October 11 source CI](https://github.com/Pradhyut21/jalrakshak/actions/runs/38140601260) | Passed at application-source commit `eaa9dc7`: locked dependency installation, complete backend suite, synthetic evaluation, static infrastructure checks and frontend build. |
| [October 11 focused browser report](artifacts/incident-progress-verification.json) | Five Chromium/HTTP checks passed with zero JavaScript errors, including an old approval followed by a new incident and approval of the current incident. |
| [October 3 local reports](artifacts/verification.json) | Historical complete suite: 186 backend tests and 31 Chromium checks passed. The full browser suite was not rerun for the October 11 correction. |

These checks use generated records and do not establish field accuracy or live AWS execution. The October 3 ZIP retains its original bytes and excludes the later approval-display correction; Git source includes it. See the [active checkpoint](docs/PROJECT_STATE.md) and [independent selection review](docs/SELECTION_REVIEW_2026-10-11.md).

## Use actual logs

Open **Data & settings**, configure capacity, reserve, supply lead time, buffer and a positive per-reading error bound in litres with its documented basis. Choose an empty observed workspace; demo records are cleared. Use a supplier specification or independent reference measurements for the bound, or identify an estimate as unverified. Declaration is not calibration; an understated bound can warn late.

Add actual timestamped observations, or preview and import CSV with timezone-aware `observed_at,volume_l` and optional `reading_id`. Include recorded arrivals to explain level increases; future plans remain separate. Older saved workspaces retain their logs but remain UNKNOWN until the error declaration is saved.

A bound below 0.5% of capacity prompts a datasheet/reference check. This advisory is an uncalibrated review heuristic: smaller accurate bounds can be legitimate, while larger bounds can warn too early. A tank-level log alone cannot establish reliable sensor accuracy.

Observed mode uses the real clock and local SQLite storage behind a session cookie. Export JSON backups: only the latest 1,000 readings and at most 200 supply records are retained, and sessions expire after 30 days without a write. Production identity controls are unimplemented; cloud guests accept simulated data only. Feature scope is frozen pending real logs and caretaker feedback.

## Forecast evidence and limits

- Forecasts reconcile arrived water once and distinguish reserve crossing from an empty tank.
- A local-hour demand profile and empirical upper-demand envelope produce the planning deadline. Unsupported hours and measurement-error assumptions are exposed.
- Planned supply is conditional and cannot extend the upper-envelope deadline.
- Three high intervals flag site-level abnormal depletion; aggregate tank readings cannot locate a leak. The detector produces false alerts.
- Approval is bound to its evidence revision and expiry; incident facts survive temporary UNKNOWN data quality.

The deadline is assumption-dependent. In the original synthetic 48-hour holdout, late event predictions improved from 53/120 to 0/120. Untuned stress cases still contain 12 late predictions among 1,232 true crossings and substantial early-warning tradeoffs. The broader detector evaluation contains false alerts. See [evaluation](docs/EVALUATION.md); synthetic results do not establish field reliability.

## Verify and continue

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe infra/check_template.py --check-source
```

Build the interface with `npm ci` and `npm run build` in frontend. On Windows install the test browser with `.venv/Scripts/python.exe -m playwright install chromium`, then run `.venv/Scripts/python.exe scripts/browser_check.py http://127.0.0.1:8012` against the running app (adjust the URL to its port).

Run `.venv/Scripts/python.exe scripts/check_incident_progress.py` after building for the focused approval regression. It starts and stops its own loopback server with a temporary database and generated demo records.

Read [AI_HANDOFF.md](AI_HANDOFF.md) and [active checkpoint](docs/PROJECT_STATE.md) to continue. [REVIEW_THIS_PROJECT.md](REVIEW_THIS_PROJECT.md) provides an independent review entry; [review fixes](docs/REVIEW_RESPONSE.md) map the reported defects to changes and remaining gaps.

## AWS, provenance and license

The repository contains a boto3 DynamoDB adapter, Lambda handler and [SAM template](infra/template.yaml). SAM/Linux packaging and deployment have not been verified. External notifications remain disabled; no connected sensor or real caretaker pilot is claimed.

Development began October 1, 2026, before the published October 8 event start. This pre-event build cannot be claimed eligible under the [current project-start rule](https://www.wemakedevs.org/aws/env/rules) without organizer clarification. Original dates and Git history are preserved.

Original domain code and SVG assets are released under the [MIT license](LICENSE). Reference repositories informed research only; licensed dependency code retains its own [notices and attribution](THIRD_PARTY_NOTICES.md).
