# Prompt 06 — Approved notification and evidence-based verification

**Result:** risk → explicit action → truthful status → fresh observations → verified outcome.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, and incident/action contracts.
Close the loop without an LLM or pump/vendor integration.

Generate deterministic proposals such as inspect unexplained usage,
confirm planned supply, or request additional supply, with supporting
facts/deadline. A proposal is not a tanker booking. Bind approval to an
authenticated actor, site, action ID, evidence version, scope, expiry,
and idempotency key. Reject stale/changed/unauthorized approvals. Model
text, quoted approval, or a recommendation must never count as consent.

Implement separate incident and notification lifecycles. Store pending
dispatch durably before sending; use conditional transitions, bounded
retries/backoff, and reconciliation for interrupted/uncertain dispatch.
Do not record failed delivery as success or suppress all future retries.
Do not claim exactly-once external delivery; identify duplicate receipts.
SNS Publish returning a MessageId means publication accepted, not human
receipt, booking, repair, or environmental resolution.

Use an SNS notifier plus a local HTTP receiver adapter for integration
tests. Send externally only to an explicitly authorized confirmed test
destination and after concrete action approval. If none exists, do the
local receipt proof and record external proof as pending. Never publish
to a guessed contact or configure arbitrary webhook targets. Demonstrate
real receipt if available; expose PUBLISHED/FAILED/RECEIPT separately.

Record repair/delivery as an intervention claim. Verification uses fresh
post-action observations, a configured sustained normal band, and renewed
reserve margin. Missing/stale readings → VERIFYING/UNKNOWN or escalation.
The intervention form, agent, and browser cannot set RESOLVED. Preserve
verification evidence IDs and simulated/manual status.

Test concurrent double clicks, wrong IDs/site, expired/stale evidence,
publish failure/retry, crash gap, duplicate callbacks, repair-with-no-new-
reading, stale telemetry, and a real local HTTP payload/receipt. Complete
healthy → anomaly → propose → approve → notify → new readings → verify.
Run checks, update checkpoint/evidence/limitations, commit. Next Prompt 07.
```
