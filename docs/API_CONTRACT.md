# API contract Â· version0.2

All routes use /api. Timestamps are timezone-aware ISO strings; storage uses UTC and UI uses IST. Volumes are litres; rates litres/hour. GET /dashboard creates or resumes a cookie session and returns csrf_token; POST requests require X-CSRF-Token. Origin is checked when present.

Dashboard includes site, clock, mode, version, state, analysis, incident, actions, events, deliveries, evaluation and features.local_observed_mode. Mode is SIMULATED_DEMO or LOCAL_OBSERVED. Empty state volumes/timestamps are null, source none, data_state insufficient, and analysis UNKNOWN.

Analysis preserves reserve/empty deadlines, observed current_rate_lph, conditional central projections and local-hour forecast details: forecast_description, forecast_assumptions, forecast_config, demand_profile, sufficient_forecast_history and measurement_bounds. The legacy conservative_breach_at key now means the assumption-based empirical upper-demand planning path. No probability or guaranteed safety is implied. A preview changes future projections without rewriting measured rates.

| Route | Payload / result |
|---|---|
| GET /dashboard | Current dashboard; no-store. Observed clock refreshes from wall time. |
| GET /health | Version/storage/notification status. |
| GET /evaluation | Packaged synthetic artifact, independent of actual logs. |
| POST /workspace/live | name,capacity_l,reserve_l,lead_hours,buffer_hours,measurement_error_l,time_zone â†’ empty LOCAL_OBSERVED dashboard. Local SQLite/loopback only. Existing observed records cannot be replaced by this route. |
| POST /site | Same fields â†’ update observed settings; evidence version changes. Reserve/error must be below capacity. |
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

Errors:401 expired/missing session;403 CSRF/origin/locality;404 missing action;409 conflicting state/record/evidence;422 invalid schema/provenance;429 creation/storage quota. Schema rejects unknown fields and nonfinite values. Database mutations roll back on failure. Session IDs, runtime records and credentials are excluded from archive/export.
