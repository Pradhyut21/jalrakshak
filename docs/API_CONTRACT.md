# API contract · version 0.2.2

All routes use /api. Timestamps are timezone-aware ISO strings; storage uses UTC and UI uses IST. Volumes are litres; rates litres/hour. GET /dashboard creates or resumes a cookie session and returns csrf_token; POST requests require X-CSRF-Token. Origin is checked when present.

Dashboard includes site, clock, mode, version, state, analysis, incident, actions, events, deliveries, evaluation and features.local_observed_mode. Mode is SIMULATED_DEMO or LOCAL_OBSERVED. Empty state volumes/timestamps are null, source none, data_state insufficient, and analysis UNKNOWN.

Analysis preserves reserve/empty deadlines, observed current_rate_lph, conditional central projections and local-hour forecast details: forecast_description, forecast_assumptions, forecast_config, demand_profile, sufficient_forecast_history and measurement_bounds. The legacy conservative_breach_at key now means the assumption-based empirical upper-demand planning path. No probability or guaranteed safety is implied. A preview changes future projections without rewriting measured rates.

| Route | Payload / result |
|---|---|
| GET /dashboard | Current dashboard; no-store. Observed clock refreshes from wall time. |
| GET /health | Version/storage/notification status. |
| GET /evaluation | Packaged synthetic artifact, independent of actual logs. |
| POST /workspace/live | name,capacity_l,reserve_l,lead_hours,buffer_hours,measurement_error_l,measurement_error_basis,time_zone → empty LOCAL_OBSERVED dashboard. Local SQLite/loopback only. Existing observed records cannot be replaced by this route. |
| POST /site | Same fields → update observed settings; evidence version changes. Reserve/error must be below capacity. |
| POST /readings | reading_id,observed_at,volume_l,source,simulated,advance_clock. Demo: manual_demo/true; optional bounded3h advance. Observed: manual_observed/false, no advance, no future timestamps. Capacity is validated. |
| POST /import | readings (max1,000) and deliveries (max100 actual arrivals). Atomic sorted import; observed mode only. Reading provenance as above; arrivals id,amount_l,arrived_at. |
| POST /deliveries | id,amount_l and exactly one of arrived_at or scheduled_at. Status is server-derived. Future plan can transition to actual arrival under the same id. |
| POST /export | {} â†’ JSON backup of records/settings/events; no cookie or CSRF secret. |
| POST /demo/reset | {} â†’ reset own simulated session; blocked for observed workspaces. |
| POST /demo/scenario | scenario excess_usage/repair/delivery, hours2â€“6. Simulated mode only. Repair generates subsequent observations; it cannot force verification. |
| POST /simulate | delay_hours0â€“48,added_supply_l0â€“50k,demand_change_percentâˆ’50â€“100 â†’ read-only forecast preview. |
| POST /actions/propose | type REQUEST_SUPPLY/REQUEST_INSPECTION â†’ exact local notice proposal. |
| POST /actions/{id}/approve | evidence_version,confirmed (strict boolean) â†’ dashboard with local receipt. Evidence/expiry/freshness required; repeat receipt is idempotent. |
| POST /interventions | type REPAIR_RECORDED,note â†’ restart verification for an existing incident; missing incident rejected. |
| POST /assistant | question deadline/delay/buffer â†’ deterministic answer and facts. |

Incident status UNKNOWN is a current data-quality view; lifecycle_status retains OPEN/ACTION_REQUESTED/VERIFYING/RESOLVED from stored facts. Approval never creates recovery proof. Recovery needs three fresh normal post-intervention observations and adequate forecast margin.

Observed settings require a finite JSON number `measurement_error_l` strictly greater than zero and below capacity. There is no default. Omission, null, strings, booleans and zero are rejected with 422. `measurement_error_basis` is a required string of at most 300 characters, trimmed and checked for nonblank content (including BOM-only input). It documents the operator's basis, such as a supplier specification in litres or an independently checked measurement; an estimate must be described honestly as unverified. The application cannot certify the basis. `measurement_error_declared_at` is a server-owned UTC timestamp returned with the site and backup, not accepted as request input.

An older observed workspace lacking the new basis remains intact but returns UNKNOWN with no forecast projection or operational deadlines. Dashboard, preview, assistant, proposals and approvals use the same declaration gate. Saving `/site` with an explicit bound and basis restores analysis subject to the ordinary freshness/evidence checks, invalidates older proposals and resets recovery credit after an intervention. Demo and synthetic evaluation arithmetic keep their existing assumptions, including exact-reading fixtures.

Observed analysis facts/assumptions and local notice messages carry the declared bound, basis and calibration limitation. An understated bound may warn late. A tank-level log alone cannot establish a reliable upper sensor-error bound; no error estimator or arbitrary safe minimum is supplied.

Version 0.2.2 adds `analysis.measurement_error_warning`: null, or `{code: "LOW_DECLARED_ERROR", message, declared_error_l, capacity_percent, review_threshold_percent: 0.5, review_threshold_l}`. It appears only for a complete observed declaration strictly below `capacity_l * 0.005`. The same advisory appears in previews, assistant text/facts and new local notice messages, even when otherwise valid declared data is empty/stale UNKNOWN. Missing declarations retain the existing UNKNOWN gate and do not receive this advisory. Settings shows the warning while typing before saving.

The 0.5% cutoff is a reviewer-suggested review heuristic, not a fitted noise bound, minimum safe error, calibration test or probability. Crossing it changes only disclosure. A null warning does not certify accuracy; the general calibration warning remains. Smaller rated bounds may be valid, and increasing the declaration can cause early warnings. No value is corrected automatically, no new approval step is added, and forecasts/detector/evaluation stay unchanged.

Errors:401 expired/missing session;403 CSRF/origin/locality;404 missing action;409 conflicting state/record/evidence;422 invalid schema/provenance;429 creation/storage quota. Schema rejects unknown fields and nonfinite values. Database mutations roll back on failure. Application archives exclude runtime records, session IDs and credentials. JSON backups include this session's records and settings while excluding session IDs, cookies and CSRF secrets.
