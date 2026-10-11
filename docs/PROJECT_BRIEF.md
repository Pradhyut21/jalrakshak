# Implementation brief

Updated October 3, 2026. One caretaker manages one tank. JalRakshak helps decide when to arrange supply and inspect abnormal site-level depletion before reserve crossing.

Implemented: local operator log entry/import, editable site settings, separate supply ledger, wall-time freshness, 48-hour reserve planning, read-only previews, incident history, evidence-bound local notices, fresh-reading recovery, backup export and reproducible synthetic evaluation. The demo uses fictional 50,000 L capacity, 5,000 L reserve, 14-hour lead time and 3-hour buffer; these are editable in the empty observed workspace.

Observed interval demand accounts for arrivals once. Central forecasts use local-hour historical medians; the upper planning path uses empirical observed-demand bounds, a recent upper-rate floor and measured storage minus declared error. Lookback168h, upper quantile0.9, minimum bucket2h and multiplier1.0 were frozen before final reporting. Sparse history is explicit. No guaranteed safety or calibrated probability is claimed.

Since version 0.2.1, an explicit positive per-reading error bound in litres and its documented operator-entered basis are required. The observed form has no preset error. Older observed workspaces remain UNKNOWN until the declaration is saved; logs and incident facts are preserved. Declaration is not calibration, and an understated bound may produce late warnings. A single tank-level log cannot reliably estimate the bound.

Version 0.2.2 adds only an advisory below 0.5% of tank capacity, prompting a datasheet/reference-measurement check. The cutoff is a review heuristic, not a safe minimum; smaller accurate bounds can be legitimate, while a larger declaration can warn too early. It does not change numerical forecasts, UNKNOWN rules, incident detection or approval. Feature scope is frozen pending actual logs and a caretaker usefulness check.

Three consecutive intervals above1.5Ã— the earlier median flag abnormal depletion. This detector has false alerts under daily cycles and cannot locate a leak. UNKNOWN is a temporary quality view, separate from stored lifecycle facts. Approval and intervention do not establish physical success; recovery needs three fresh normal post-intervention readings and at least three hours of modeled planning margin.

Observed mode runs on loopback SQLite only. It starts empty and uses the real clock. Entries retain manual_observed/simulated:false provenance but are not authenticated sensor evidence. The session retains the newest1,000 readings, at most200 supply records and expires after30 days without a write. Export backups; cloud guests cannot enter actual-site data.

Tech: React/TypeScript/Vite, original SVG, FastAPI/Pydantic, transactional SQLite, optional DynamoDB and SAM source. The current checkpoint records tests. Actual caretaker utility, sensor accuracy, cloud execution and external transport remain future evidence milestones. Preserve truthful pre-event dates and scope; avoid city-wide claims, leak localization, pump automation, unnecessary deep learning or favorable-rating instructions.
