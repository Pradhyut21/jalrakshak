# Active JalRakshak checkpoint

Updated October 2, 2026 Â· Asia/Kolkata. **Version 0.2: WORKING_LOCAL_OBSERVED_PROTOTYPE. Local repair and portable packaging milestone complete.**

## Objective and decisions

The user asked to fix the independent review and continue the original water-operations app in this workspace. Scope remains one caretaker, one tank and one incident loop. Winner repositories informed research; their restricted or unlicensed code was not copied. Preserve actual October 1â€“2 development dates and unresolved event-start eligibility.

## Completed

- Replaced constant last-rate Ã— 1.2 forecasting with historical local-hour medians, empirical upper-demand bounds and a recent upper-rate floor. Parameters were frozen using validation only. Forecasts account for arrivals once, preserve measured rates, separate reserve crossing from emptiness and expose sparse history and reading-error assumptions.
- Separated incident lifecycle facts from UNKNOWN data quality. Valid readings restore prior workflow state; older saved approval receipts are preserved on upgrade. Approval remains bound to session, action, evidence revision, expiry and a strict boolean.
- Recovery requires three independent fresh normal post-intervention readings plus adequate modeled margin. Claims alone cannot resolve incidents. Changed imports, ambiguous intervals and historical revisions invalidate recovery credit. No intervention event is created without an incident.
- Added an empty local observed workspace, editable tank settings, timestamped manual entries, atomic CSV/arrival imports, actual/planned delivery records, wall-time freshness and JSON backups. Demo fixtures cannot carry into actual records. Inputs remain unverified operator entries, available only on loopback SQLite; cloud guests remain simulated.
- Bounded anonymous creation, active SQLite sessions and payload size. Added offline-tested DynamoDB hourly quota source. Removed the preview/assistant second-read expiry race and return401 for mutation expiry.
- Fixed CSV accessibility labels, mobile evaluation overflow and faint explanatory text. The browser refreshes every30 seconds and on visibility changes, with request-order guards and clear refresh failure.
- Created a lean app archive and a separate full-context archive. Current screenshots, active handoff and six continuation prompts are easy to find. Required dependency notices are preserved.

Observed records retain the newest1,000 readings and at most200 supply records. They expire after30 days without a write; export backups. Combined supply lead time and buffer cannot exceed the48-hour model horizon. This is local session isolation, not a production identity system.

## Verified

- **124 backend tests pass**, zero failures and two upstream deprecation warnings, in a new environment from the extracted archive.
- **24 Chromium checks pass**, zero JavaScript errors, covering the demo, observed data path, imports, local approval/recovery, backups,390px mobile pages, polling and error flows. Generated E2E inputs are explicitly test data; stale polling uses a declared mock, while backend wall-clock aging is independently tested.
- Fresh locked Python install, npm ci and production build pass on Windows. All49 application-source, built-interface and lock files checked match the tested archive bytes. See artifacts/portable-install-verification.json.
- Exact synthetic evaluation reproduction passes; both packaged JSON copies match. Original generator hash remains688ad1143797468282f2e051acd7bc9a870f5272633a6ce9164143393f4e23c0.
- Offline infrastructure structure/static AST checks pass. SAM transform, Linux Lambda build and deployment were not run.
- Dependency inventory remains35 Python distributions,25 installed npm packages and44 platform-specific/uninstalled lock entries. One optional native development dependency has metadata-only license evidence; notices and scope remain documented.
- Archive manifests verify safe paths, full coverage, hashes and CRC. Runtime records, installed dependencies, credentials and Git internals are excluded.

## Forecast evidence and limits

Full48-hour targets are purged across chronological splits. Original120-window holdout: legacy53 late predictions, upgraded0, but mean5.700h early and P9013.848h. Normal-only65 windows: legacy27 late, upgraded0. The protocol differs from the external review's63/20 counts; no executable review protocol was supplied.

Twelve predeclared untuned stress cases contain1,440 windows,1,232 true crossings and208 censored outcomes. The new method still has12 late predictions (maximum0.930h), no missed horizon events and substantial early warnings. All208 censored windows also received predicted crossings. The detector has44 false-alert events over1,515 normal site-hours.13 episodes overlap alerts, including3 already alerted before onset. These are synthetic results, not field accuracy, calibrated probability or a safety guarantee.

## Run and resume

From this root: `python scripts/run.py --setup`; later `python scripts/run.py`. Initial setup needs Python3.13, Node22.18+ and internet. Default URL is http://127.0.0.1:8000. Another project currently uses8000; the final root app is running at **http://127.0.0.1:8012**, launched with `python scripts/run.py --no-browser --port 8012`.

Tests: `.venv/Scripts/python.exe -m pytest -q backend/tests`. Reproduce evaluation: `.venv/Scripts/python.exe scripts/evaluate.py`. Browser check accepts the running URL. Packaging: `python scripts/package.py` and optional `--full-context`.

Read AI_HANDOFF.md, PROJECT_BRIEF.md, API_CONTRACT.md, EVALUATION.md and REVIEW_RESPONSE.md before continuing. Historical prep is separate; its old preparation-only gate is superseded by the user's explicit immediate-build authorization. Preserve source and failures; refresh checks and archives after changes.

## Next evidence milestone

Actual caretaker tank logs and a usefulness check have not been supplied. There is no calibrated sensor, real caretaker pilot, live AWS execution, external supplier send, model call or measured water saving. Cloud work needs concrete account, region and cost scope; external transport needs an authorized destination. No universal rating or award is promised. No required local work remains for this milestone.
