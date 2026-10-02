# AWS source and deployment status

Prepared 1 October 2026. The user authorized immediate implementation; this prototype's real pre-event dates must be preserved. It is not claimed eligible under the event's current project-start rule.

**AWS deployment has not been performed or verified.** No AWS account, region, cost scope, public frontend, real sensor, or external notification destination has been verified. `infra/template.yaml` is source for a disposable simulated-session backend; a template or offline check is not cloud execution evidence.

Version0.2 adds a DynamoDB atomic global creation budget (default100 new sessions/hour), a300KB serialized payload cap and per-instance peer rate checks, alongside API Gateway throttling. Offline counter tests do not verify live AWS capacity, billing or TTL cleanup latency. JAL_DEMO_ONLY=true and DynamoDB storage both disable local observed workspaces; actual operator records must stay on the local loopback SQLite application until production identity/access controls are implemented.

On **2 October 2026**, `python infra/check_template.py --check-source` passed the offline YAML/wiring and handler-AST checks against the existing backend. SAM transformation, Linux dependency packaging and actual AWS deployment were not run. These results do not establish runtime cloud compatibility.

## Resources and runtime contract

The SAM template defines an API Gateway HTTP API, one Python 3.13 Lambda, a DynamoDB session table, a table-scoped DynamoDB policy, and a seven-day Lambda log group. It does not create SNS topics, subscriptions, pumps, tankers, a model endpoint, or a frontend hosting account.

`CodeUri: ../backend` packages the backend directory; `Handler: app.main.handler` requires the global Mangum adapter in `backend/app/main.py`. Backend dependencies must be in `backend/requirements.txt`. AWS lists Python 3.13 on Amazon Linux 2023; the local interpreter version does not prove Linux wheel compatibility. [Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), [SAM function contract](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html).

| Environment | Meaning |
|---|---|
| `JAL_STORAGE=dynamodb` | Cloud repository selection; never fall back silently to SQLite on Lambda. |
| `JAL_TABLE_NAME` | CloudFormation-created session table. |
| `ALLOWED_ORIGINS` | One exact frontend origin, such as `https://branch.example.amplifyapp.com`; no path/trailing slash/wildcard. |
| `JAL_COOKIE_SECURE=true` | Secure cloud cookie transport; cross-site hosting also needs the backend's `SameSite=None` behavior. |
| `JAL_DEMO_ONLY=true` | Cloud API handles disposable simulated sessions; no real-site operational access. |
| `JAL_SESSION_TTL_HOURS` | Disposable-session lifetime, 24 hours by default. |

Each DynamoDB record uses `session_id` as its string partition key, `payload_json` for context, `version` for optimistic conditional writes, and `expires_at` for epoch-second expiry. The repository must reject expired records itself: DynamoDB TTL cleanup is asynchronous. The backend owns guest/session isolation and current CSRF/approval checks; CORS alone is not authentication. Cloud mode must not accept a manual reading as evidence from a real installation.

The JSON session context must fit DynamoDB's item-size limit. Keep demo history/action/event collections bounded and report persistence failures truthfully; a static table definition does not prove arbitrary session sizes will persist. [DynamoDB constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html).

External notifications remain disabled. Local receipt records demonstrate the local action workflow only. Do not label them SNS publication, email delivery, human receipt, tanker booking, or a physical repair.

## Local/offline checks

From the extracted repository root, use the host's Python executable:

```text
python -m pip install -r infra/requirements-validation.txt
python infra/check_template.py
python infra/check_template.py --check-source
```

The first check reads YAML and tests relevant wiring. `--check-source` also checks the handler binding through Python AST and the requirements file's existence. Neither executes the backend, transforms SAM, builds Linux dependencies, contacts AWS, or certifies deployment. Read the reported `check_kind` and `NOT_RUN` fields.

SAM and AWS CLIs were not found during initial implementation inspection. On a host with official SAM CLI and Docker installed, complete the stronger packaging checks:

```text
sam validate --template-file infra/template.yaml --lint
sam build --template-file infra/template.yaml --use-container
```

Do not package Windows native dependencies directly for Linux Lambda. SAM's container build gathers dependencies in a Lambda-like environment. [SAM build documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-build.html).

## Deployment once account and cost scope are authorized

Replace the example profile/region/origin with actual approved values. These commands are instructions, not evidence that they have run.

```text
aws sts get-caller-identity --profile YOUR_AUTHORIZED_PROFILE --region YOUR_CHOSEN_REGION
sam deploy --guided --profile YOUR_AUTHORIZED_PROFILE --region YOUR_CHOSEN_REGION --capabilities CAPABILITY_IAM --parameter-overrides AllowedOrigin=https://YOUR_FRONTEND_HOST SessionTtlHours=24
```

Deploy the build output after `sam build`; guided deployment should use `.aws-sam/build/template.yaml`. Check the resolved template path before accepting the change set. Do not infer an account, budget, or role from advertised event credits. Keep account IDs and resource identifiers in private deployment notes.

The template uses on-demand DynamoDB, capped API request rates, reserved Lambda concurrency, and short log retention. These bound specific workloads; they are **not a spending cap**. Establish an account budget/alert and review current regional API Gateway/Lambda/DynamoDB/hosting rates before deployment. No estimated bill is asserted without that account/traffic basis.

After actual deployment, record the stack output `ApiBaseUrl` and demonstrate:

1. `/api/health` reports the actual storage/runtime mode.
2. One browser session resets and changes its simulated state; a different session cannot access or overwrite it.
3. State survives a fresh Lambda execution environment through DynamoDB.
4. Concurrent updates conflict safely rather than losing an approved action or newer reading.
5. Cookie, CORS and CSRF behavior works from the exact permitted frontend origin; requests from another origin cannot mutate a session.
6. Local receipt statuses and simulated provenance remain visible; no external send is implied.

Preserve actual request/status evidence without cookies, credentials or private account details. A successful deploy command alone does not establish these behaviors.

## Frontend hosting source

`infra/amplify.yml` supplies a React/Vite build specification for a repository with `frontend/` as the app root. Configure an authorized Amplify app manually or through a separately reviewed hosting change, choose the branch, and use this build specification. It is not an existing live URL or deployment.

Set the frontend API-base environment variable supported by the actual frontend implementation to the deployed `ApiBaseUrl`, then rebuild. The variable name must match the frontend source; do not assume a planned name works. Cookie-authenticated fetches must include credentials, and cloud cookie/CSRF behavior must be tested from that hosting domain.

The local Vite proxy serves same-origin `/api` requests during development. A static host does not automatically recreate that proxy. If the frontend currently only uses relative `/api`, configure a real reverse proxy on the hosting domain or change its supported build-time API base before claiming the hosted workflow is ready. Basic frontend hosting and this SAM backend are separate operations.

## Cleanup and limitations

Once deletion is explicitly within the approved disposable-stack scope, use SAM's normal stack deletion flow for the correct account/profile/region. This template does not retain the session table; deleting the stack deletes its simulated data. Frontend hosting and SAM deployment-artifact buckets may require separate cleanup. Do not delete unrelated resources or use a broad account cleanup script.

Current proof limits: offline source/wiring checks only until stronger commands actually run. Account access, SAM transformation, Linux packaging, cloud persistence, cross-domain browser behavior, hosting and deployment remain unverified. The deterministic local app can work without those cloud claims.
