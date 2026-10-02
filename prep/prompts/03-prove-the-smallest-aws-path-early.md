# Prompt 03 — Prove the smallest AWS path early

**Result:** early cloud evidence or a candid eligible fallback; no last-day discovery of account restrictions.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, and the current contract. Preserve
the local reading flow. Verify current AWS SAM/Lambda/DynamoDB/hosting
documentation and existing account/profile/region authorization.

Build a minimal SAM template: HTTP API, one modular API Lambda, DynamoDB,
necessary roles, logs with bounded retention, and outputs. No wildcard
admin permissions, VPC/NAT, distributed forecast services, or extra AWS
services without a behavior they enable. Lambda must use DynamoDB for
durable state; SQLite or Lambda filesystem is not cloud persistence.
Package for the chosen Linux runtime; do not ship Windows-only binaries.

Implement DynamoDB repository parity for reading IDs, latest observation,
site access, and ordered history. Test meaningful parity and conditional
updates. Configure CORS for actual frontend origins. Protect real-site
reads and mutations with authenticated, site-scoped authorization (Cognito is a
managed candidate). A public guest demo may mutate only disposable
simulated state and may never send notifications or access real sites.
Never bundle AWS credentials or admin secrets in the frontend.

Prepare a concrete deployment with account/region, resource list, estimated
cost basis, cleanup instructions, and secret-free config. If deployment
is already authorized for this account/cost scope, proceed; otherwise
ask only for the missing concrete scope after preparing the reviewable
result. Do not infer an account or a budget from the event's credits.

When authorized, deploy the API and host the simple frontend on AWS
Amplify or an equally small justified AWS route. Prove POST reading →
DynamoDB → GET state → UI, including persistence across fresh invocations.
Record actual resource IDs privately and redacted evidence publicly.

If account verification or service access blocks deployment, record the
exact failure; complete useful local work and preserve real SAM/AWS
open-source usage allowed by the rules. Never label local execution cloud.
Run relevant tests/build/SAM validation, update state/evidence, and commit.
```
