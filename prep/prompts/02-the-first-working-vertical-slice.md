# Prompt 02 — The first working vertical slice

**Result:** input → persistence → response → browser; no forecast yet.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, and the contract/brief relevant to
this milestone. Implement only the first end-to-end reading workflow.

Create one sample site with explicit sample provenance. A water reading
has a client-stable reading ID, site ID, observed_at, received_at, volume
in litres, source kind, simulated flag, and optional measurement error.
Validate finite values, capacity bounds, UTC timestamps, and known site.
Don't reject legitimate delayed observations merely because they arrived
out of order: preserve them, but they cannot replace a newer latest state.
Repeated IDs must not create duplicate observations; conflicting payloads
with the same ID must return a clear conflict.

Implement GET /health, GET /sites, POST /sites/{id}/readings,
GET /sites/{id}/state, and arrived-delivery recording. A recorded delivery
is not an automatic second increment of an already observed tank level.
Keep the authoritative measurement and inferred accounting consistent.

Use persistent local SQLite through the repository interface. Create an
isolated disposable store for tests. Build a tiny operations page showing
current litres/percentage, reserve setting, source, age, and a manual
reading form. Show loading, empty, invalid, stale, and error states.
Do not render UNKNOWN as SAFE. No invented KPI cards or forecast values.

Generate or check frontend types against the actual OpenAPI contract.
Freeze the contract for parallel work, documenting any future versioned
change. Verify a real HTTP POST and GET plus a browser update when browser
tools are available. Test duplicate/conflicting IDs, bounds, missing site,
and out-of-order arrivals. Run the relevant backend and frontend checks.

Update README local commands, EVIDENCE, and PROJECT_STATE with exact
results. Check and commit only this milestone's files. Next is Prompt 03.
```
