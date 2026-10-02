# Active JalRakshak checkpoint

Updated October 2, 2026, Asia/Kolkata. **Phase: WORKING_LOCAL_SIMULATED_PROTOTYPE.** Local implementation and portable packaging milestone complete.

## Locked direction

Original JalRakshak in the SAANS workspace: one caretaker, one tank, conservative reserve/action deadline, sustained abnormal depletion, explicitly approved local notice and recovery evidence. The user authorized immediate implementation after the event timing consequence was explained. Real implementation began October1 and continued October2. Preserve dates; never claim this early prototype satisfies the previously reviewed project-start rule without organizer clarification.

## Implemented

React/Vite/TypeScript responsive interface with original SVG tank/projections, scenarios, notice review, incident history and API-derived evaluation. Modular FastAPI with validated simulated inputs, random isolated sessions, CSRF/origin checks, persistent atomic SQLite, deterministic analysis/assistant and future-only previews. Actions bind evidence revision/expiry and require an actual JSON boolean confirmation. Duplicate approvals retain one local receipt. SAM/API Gateway/Lambda source and optional DynamoDB conditional-update repository are included.

Numerical rules: forecast anchored at latest measurement, actual arrivals reconciled once, 48-hour bounded trajectories, conservative excludes planned supply and increases demand20%. Validation selected the simple last-interval forecast; detector separately requires three high intervals against earlier median. Delivery preserves excess demand; only repair scenario reduces it. Verification requires three fresh normal post-intervention intervals and adequate margin. UNKNOWN or late evidence clears/reopens verification; claims and notifications do not prove repair. Nonfinite requests return422 rather than crashing. SQLite connections close after every transaction.

## Verified evidence

- 57 backend tests pass,0failures;2 upstream deprecation warnings.
- Production TypeScript/Vite build passes.
- 12 Chromium checks pass,0unexpected page errors: initial state,24h delay,assistant,excess,approval,repair/refill,recovery,manual entry,evaluation,reset,mobile overflow,UNKNOWN and API failure.
- Fresh archive extraction: new .venv, locked install,npm ci/build,57tests and12browserchecks pass on Windows. Source/lock hashes recorded in artifacts/portable-install-verification.json.
- Synthetic chronological holdout:166 one-hour forecasts,MAE149.097767L; validation-only window selection. One labeled holdout abnormal episode detected after2h;0newfalsealerts/159normal site-hours. No real-data,calibrated uncertainty or48-hour forecast accuracy claim. See docs/EVALUATION.md.
- SAM YAML/wiring/static AST checks pass offline; no transform,Linux build or deployment verified.
- Observed dependency inventory:35Python,25npm,26preservednoticefiles; absent-platform entries and metadata-only gap explicit. Current ZIP manifest verifies all payload hashes and safe paths.

## Run and resume

From this root: `python scripts/run.py --setup`; later `python scripts/run.py`. Local appURL http://127.0.0.1:8000. First setup needs Python3.13,Node22.18+ and internet for locked dependencies. START_APP.cmd provides the same Windows startup. The packaged built UI is included; no API keys required. Tests: `.venv/Scripts/python.exe -m pytest -q backend/tests`. Reproduce evaluation: `.venv/Scripts/python.exe scripts/evaluate.py`. Browser harness requires Playwright Chromium installed separately.

Use AI_HANDOFF.md, docs/PROJECT_BRIEF.md and docs/CONTINUE_PROMPTS.md in a new chat. Preserve source/history; prep is historical and its earlier preparation-only gate is superseded. Keep old preparation ZIP separate. A new source change requires appropriate rechecks and a refreshed manifest/archive; never reuse this evidence for changed behavior.

## Next milestone and limits

No required local-app work remains for this milestone. Next high-value work is actual caretaker validation and a scoped AWS deployment, then optionally a grounded provider assistant or authorized transport. AWS identity/account,region,budget and notification recipient have not been supplied. There are no real sensors/interviews,cloud receipts,LLM calls,measured savings or awarded scores. Public demo isolation is not production authentication; all inputs remain simulated. Do not guess credentials,recipients or eligibility. Use the existing deployment guide/continuation prompts when concrete scope is available.
