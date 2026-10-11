# Changes following the independent review

The original review correctly identified forecast and state defects. This document points to verifiable changes; it does not promise a score.

| Finding | Implemented response | Evidence / remaining limit |
|---|---|---|
|Constant last-rateÃ—1.2 can warn too late over48h|Historical local-hour profile, empirical upper-demand envelope, recent upper-rate floor and declared measurement bounds|Independent arithmetic and48h paired evaluation; original normal-only legacy27/65 late, new0/65. Protocol differs from review's63 windows. Untuned stress retains12 late predictions; no guarantee.|
|Incident remains UNKNOWN after readings recover|UNKNOWN view separated from factual lifecycle; approval is stored against incident|HTTP regressions recover OPEN and prior ACTION_REQUESTED, allow later approval without intervention, and preserve older saved receipt facts on upgrade.|
|No actual data path or wall-time freshness|Empty local observed workspace, editable site, timestamped manual records, atomic CSV/arrival import, wall clock, export|HTTP/browser behavior; no real log, authenticated sensor or caretaker trial supplied. Cloud mode remains simulated-only.|
|Noise causes unexplained rises|Declared Â±reading error bounds interval consumption; rises beyond2Ã—error remain UNKNOWN|Independent bounded-noise checks; error is an operator assumption, not field calibration.|
|Unbounded anonymous sessions|Atomic SQLite active cap, payload cap, per-peer creation rate, DynamoDB atomic hourly quota source|Concurrent local tests and offline cloud mocks. No public-cloud execution claim.|
|Expiry race crashes preview/assistant|Reuse validated snapshot; mutation expiry mapped401|Expiry boundary regressions.|
|Inspection recommendation has supply text|Dedicated usage/inflow inspection text|Domain and proposal checks.|
|Intervention event without incident|Reject missing incident without mutation/event|HTTP regression.|
|One synthetic seed/episode and no48h timing evaluation|Unchanged original generator plus12 predeclared pattern/seed stress cases; chronological48h split purge and event/censoring metrics|All data still synthetic. Broader false alerts and early-warning tradeoffs are exposed.|
|Review ZIP overloaded with historical prompts|Lean application bundle; historical research available separately in full-context archive|Required dependency notices remain preserved. Active handoff and six continuation prompts remain easy to find.|

The next evidence improvement needs actual caretaker tank logs and a usefulness check. The implementation cannot create that evidence without a real participant. No interview, calibrated sensor, saved litre, cloud receipt or winning outcome is invented.

## October 3 follow-up to the v0.2 re-review

The supplied re-review identifies a real remaining dependency: the forecast's sensor-error safeguard is useful only when the declared bound is appropriate. Its unseen-seed runs and error-sensitivity counts are reviewer-reported evidence; their executable protocol and tank data were not supplied here. They are not presented as author-run checks or field accuracy.

Version 0.2.1 removes the guessed 100 L observed default. Workspace creation and settings updates require a positive finite numeric bound below capacity plus a nonblank description of its basis. Blank and zero no longer become an implicit exact-reading assumption. The form starts blank; older observed sessions must redeclare, retaining their logs and incident facts. Dashboard, previews, assistant and action approval share the same gate. Local notices and exports retain the bound/basis; declaration time comes from the server. A persistent warning explains that an understated bound may warn late and that a declaration does not establish calibration.

We chose explicit declaration rather than an estimator. Level changes confound demand variation, inflow records, overflow, timestamp/geometry error and noise; constant sensor bias can disappear from differences. A single tank log cannot establish a reliable upper error bound or justify a numeric “probably too low” threshold. The implementation accepts an honestly identified unverified estimate without calling it calibrated. It does not substitute the simulator's 180 L bound for a real tank's accuracy.

Regression evidence is recorded in [the active checkpoint](PROJECT_STATE.md) and [runtime verification](../artifacts/verification.json). Rejected settings leave the entire session unchanged; valid declarations persist through export/restart; legacy data remains UNKNOWN until settings are saved; earlier approval evidence is invalidated.

The remaining critique still applies: synthetic datasets, correlated windows, substantial early warnings, 44 false alerts in 1,515 normal site-hours, three episodes already alerting before onset, 12 stress late predictions and unexecuted AWS infrastructure. The forecast and detector were not retuned on held-out results. No false-alert reduction, one-alert-per-week result, calibrated confidence or improved field readiness is claimed.

The next evidence step is one authorized real tank log: about seven days of hourly timezone-aware readings in litres, capacity/reserve, actual arrived-inflow records and a documented reading-error basis. Keep historical logs historical; stale records remain UNKNOWN in the operational screen. Any retrospective scoring needs independent reference storage or a declared truth protocol, and any future threshold choice needs separate validation and untouched reporting data. Ask the caretaker whether the output would change an action and what early/repeated warnings would make them ignore it; no such interview has occurred.

## October 3 follow-up to the v0.2.1 review

The review correctly distinguishes declaration from validation: 1 L with basis “x” is accepted, and an operator can still understate uncertainty. Version 0.2.2 adds the suggested small plausibility warning, then freezes feature scope. It does not claim to establish a sensible error bound.

Strictly below 0.5% of tank capacity, the form and observed analysis prompt the operator to check the sensor datasheet or independent reference measurements. The warning also reaches previews, assistant text and new local notices. For a 50,000 L tank, the review threshold is 250 L; both 1 L and the simulator's accurate 180 L assumption receive the advisory. That is deliberate: this is an uncalibrated review heuristic, not a minimum safe bound or empirical noise estimate. A larger value is not certified and may produce early warnings; the general calibration disclosure remains at all values. No automatic correction, blocking gate or confirmation step was added.

The core `domain.py` and both evaluation JSON files are byte-identical to the delivered v0.2.1 ZIP. Numerical forecasts and detector results did not move. New HTTP regressions compare the complete domain result after stripping only appended disclosure, check scaled/strict boundaries, retain empty/stale UNKNOWN, preserve operator settings on export/restart and propagate the warning without changing approval.

The reviewer's sandbox could not run package-dependent checks. Our actual local commands/results remain in the verification reports; their existence is not independent reviewer confirmation. Fresh installation was verified for v0.2.1; version 0.2.2 uses the same locked dependency versions and reports current runtime/build/archive checks separately.

Real tank logs, rated sensor accuracy and caretaker feedback remain absent. Alert fatigue, early warnings, stress lateness and AWS execution are unchanged. Obtain the real log and datasheet next; no further feature expansion or rating claim is authorized by this milestone.
