# JalRakshak local HTTP contract v1

Implementation contract, October 1, 2026. All endpoints are `/api/...`; frontend uses a Vite proxy to localhost:8000. JSON times are timezone-aware UTC ISO strings, UI formats Asia/Kolkata. All quantities carry litres/hours where named. Guest/demo state is simulated and local notifications are labeled local receipts.

## GET /api/dashboard

```json
{
  "site": {"id":"hostel-1","name":"Aravali Student Hostel","location":"New Delhi · Sample campus","capacity_l":50000,"reserve_l":5000,"lead_hours":14,"buffer_hours":3,"freshness_minutes":90},
  "clock": "ISO UTC",
  "mode": "SIMULATED_DEMO",
  "csrf_token": "session-bound random token; send X-CSRF-Token on every POST",
  "version": 1,
  "state": {"volume_l":32000,"percentage":64,"observed_at":"ISO UTC","source":"synthetic_demo","simulated":true,"data_state":"fresh"},
  "analysis": {
    "status":"SAFE",
    "current_rate_lph":960,"baseline_rate_lph":960,
    "reserve_breach_at":"ISO UTC or null","empty_at":"ISO UTC or null",
    "conservative_breach_at":"ISO UTC or null","latest_action_at":"ISO UTC or null",
    "hours_to_reserve":28.1,"action_margin_hours":6.4,
    "next_supply_at":"ISO UTC or null","supply_status":"PLANNED",
    "anomaly":{"active":false,"observed_rate_lph":960,"expected_rate_lph":960,"ratio":1,"evidence_count":0,"reason":"plain text"},
    "recommendation":{"type":"MONITOR","title":"plain text","body":"plain text","deadline":"ISO UTC or null"},
    "facts":["plain text"],"method":"recent_mean","uncertainty_label":"Sensitivity envelope: demand ±20%; not calibrated probability",
    "history":[{"at":"ISO UTC","volume_l":32000,"rate_lph":960}],
    "projection":[{"at":"ISO UTC","volume_l":32000,"conservative_l":32000,"optimistic_l":32000}],
    "shortage_hours":0,"unmet_demand_l":0,"overflow_l":0
  },
  "incident": null,
  "actions":[],
  "events":[{"id":"event-id","at":"ISO UTC","kind":"READING","title":"plain text","detail":"plain text"}],
  "evaluation": {"data_kind":"SIMULATED","status":"pending","summary":"Evaluation has not yet run"}
}
```

Status: `SAFE | WATCH | ACT_NOW | UNKNOWN`. Incident when present: `{id,status,opened_at,intervention_at,verified_at,verification_count,reason}` with status `OPEN | ACTION_REQUESTED | VERIFYING | RESOLVED | UNKNOWN`. Action: `{id,type,status,created_at,approved_at,published_at,receipt_at,evidence_version,message,destination}`; status `PROPOSED | APPROVED | PUBLISHED | LOCAL_RECEIVED | FAILED`. Receipt is not physical action.

## Commands

- `POST /api/demo/reset` body `{}` → dashboard. Fresh isolated simulated history and planned supply; no external notifications.
- `POST /api/demo/scenario` `{ "scenario": "excess_usage" | "repair" | "delivery", "hours": 2 }` → dashboard. Insert readings through shared domain path and advance the simulated clock. Repair records an intervention and subsequent readings; it cannot directly force resolution.
- `POST /api/simulate` `{ "delay_hours": 6, "added_supply_l": 0, "demand_change_percent": 0 }` → `{analysis,before,summary,simulated:true}`; preview only, never mutate.
- `POST /api/readings` `{reading_id,observed_at,volume_l,source:"manual_demo",simulated:true,advance_clock:false}` → dashboard. Optional `advance_clock:true` explicitly advances only the simulated session clock to the observation, strictly later than now and at most three hours ahead. Identical retries do not advance twice. Default isolated-demo mode rejects real-site observations; there is no production identity claim. Conflicting IDs or same-time volumes are rejected; latest observation is chronological.
- `POST /api/actions/propose` `{ "type": "REQUEST_SUPPLY" }` → action; bound to current dashboard version.
- `POST /api/actions/{id}/approve` `{ "evidence_version": 1, "confirmed": true }` → dashboard; exact current explicit consent, dedup, protected operational writes. Development same-origin local session authentication; do not call this production authentication.
- `POST /api/interventions` `{ "type": "REPAIR_RECORDED", "note": "Caretaker reports inspection" }` → dashboard. Records claim only, awaits new readings.
- `POST /api/assistant` `{ "question": "deadline" | "delay" | "buffer" }` → `{answer,facts,provider:"deterministic",simulated:true}`. Explain computed facts; no model claim.
- `GET /api/health`, `GET /api/evaluation`.

Command errors: non-2xx `{detail:"readable message"}`. Frontend must display errors, and preserve prior known data rather than fabricate success/zero. Backend owns all computed numbers/states. Chart/history data in sample above illustrates shape, not results to hard-code.

## Domain module interface

`analyze(site: dict, readings: list[dict], deliveries: list[dict], now: datetime) -> dict` returns the `analysis` object above. Readings: `{reading_id,observed_at,volume_l,source,simulated}`. Deliveries: `{id,scheduled_at,arrived_at,amount_l,status}`. Anchor current volume at latest reading. History can include refill cycles; infer interval demand with actual arrived inflow inside `(previous_at,current_at]`. Future planned deliveries are conditional central projection; conservative breach excludes unconfirmed planned supply. Bound storage and separate unmet demand/overflow. No scenario labels available to analyze.
