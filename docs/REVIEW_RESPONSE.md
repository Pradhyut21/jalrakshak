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
