# JalRakshak: 18 staged Codex prompts

Prepared on October 1, 2026. These prompts specify future work; they do not represent implemented features. Keep the SAANS workspace and use JalRakshak as the provisional product name.

Portable use: the project root is the extracted/current folder containing AGENTS.md and this prep directory. Historical local paths are observations only. Read AI_HANDOFF.md in a new session. The user authorized dependency/reuse choices; use original domain code and appropriate licensed dependencies as documented in the reuse audit.

Detect the current host's OS, shell and tooling. Use appropriate commands there; Windows examples describe the original authoring environment. Preserve a supported Windows route, but do not require a Windows drive path or PowerShell on other hosts.

## How to use this pack

Run **00 now**, then **01–13 after the official kickoff**, one at a time. Prompt 09 is optional and must be skipped if core/demo gates are incomplete. R resumes work, X cuts scope, P coordinates parallel workers, and A changes the chosen domain before implementation. Individual copies are in `prep/prompts/`.

Continue in the same chat when practical. In a new chat, paste the next prompt or R: the files carry the current state. At kickoff, `docs/PROJECT_STATE.md` becomes the active checkpoint. Do not paste this entire pack or every source attachment into each chat.

Each implementation milestone follows AGENTS.md: inspect existing work, implement its requested behavior, run relevant checks, fix failures, update the checkpoint, and report evidence. An existing authorization should not trigger repeated permission questions. A concrete external action still needs an authorized account/destination and the product's explicit approval. Tool/setup failures must be reported honestly, with useful independent work continuing.

The official event clock governs implementation and resumed work. Dates in these prompts are planning context, not evidence the event has opened. Do not assume midnight kickoff. After the confirmed cutoff, stop submission implementation, preserve the submitted revision, and label later development separately. [Rules](https://www.wemakedevs.org/aws/env/rules), [schedule](https://www.wemakedevs.org/aws/env/schedule).

## Prompt 00 — Preparation and capability check

**When:** October 1–7 or anytime before the confirmed kickoff. **Result:** a truthful readiness checklist, no submission code.

```text
Work in the current/extracted project root. Read AGENTS.md, prep/PROJECT_STATE.md,
prep/PROJECT_BRIEF.md, and prep/research/EVENT_RULES.md.

Complete the permitted preparation for Environmental Hacks. Verify the
current official rules, kickoff notice, and submission cutoff. Record
source URLs and conflicts; the schedule currently leaves exact hours
pending while DTU Luma mentions Oct 11 at 20:00 IST.

Inspect local versions/PATH for Git, Python, Node/npm, AWS CLI, and SAM.
Do not print secrets, credential files, or full environment variables.
If an AWS profile is already configured, perform only a read-only identity
and region check and redact account details in public docs. Do not create
cloud resources, model invocations, subscriptions, or notifications.

Create or update prep/READINESS.md with verified / unknown / user-action
items: event check-in, every teammate's eligibility, Builder Center
student verification, AWS account access/region, tooling, cost limit,
authorized notification destination, and available team time. Do not
claim these were verified merely because the event page mentions them.

Use the caretaker interview checklist in the brief. Record any answers
actually supplied; never invent a user interview. Check the proposed
scope against those answers. Keep JalRakshak provisional if facts are
missing. Recommend the single highest-value next preparation action.

Check official documentation for current runtime/dependency/service
compatibility where needed. Generic learning/workshop practice belongs
outside the submission project and must remain clearly separate.

Do not scaffold the application, create project fixtures, train models,
write deployment templates, initialize submission history, or backdate
anything before kickoff. Update prep/PROJECT_STATE.md. Report what is
ready, what is unknown, and which milestone can legally run next.
```

## Prompt 01 — Kickoff, fresh repository, and compact memory

**Gate:** official event opening verified. **Result:** an agreed foundation with a truthful implementation start.

```text
Read AGENTS.md and the active checkpoint (docs/PROJECT_STATE.md if it
exists, otherwise prep/PROJECT_STATE.md). Read prep/PROJECT_BRIEF.md and
prep/BUILD_PLAN.md. Verify the official hackathon clock has opened from
the organizer announcement/form/schedule. If it has not, complete only
remaining permitted preparation and explain the event-rule gate.

When open, begin a fresh submission project in the chosen project root. Inspect existing
files and Git state; preserve unrelated work and dated preparation. Do
not clone a winner into our submission. Initialize Git only if missing;
keep prep/ as historical planning outside tracked submission sources.
Never rewrite history to disguise pre-event work.

Lock one build direction: JalRakshak, Heat and Water, one caretaker,
one site, one tank, unless actual user evidence clearly favors the Air
fallback. Read actual user evidence if available. Without caretaker
validation, keep the problem/value claim an explicit hypothesis and the
demo simulated; never claim validated demand. Use React +
Vite + TypeScript, a modular Python FastAPI backend, local persistent
SQLite, cloud DynamoDB behind a repository interface, SAM, and minimal
AWS services. Prefer Python 3.13 only if dependencies/cloud packaging
support it; record a justified compatible alternative if necessary.

Create only the minimum valid foundation: frontend/, backend/app/,
backend/tests/, data/, infra/, scripts/, docs/, README.md, .gitignore,
environment-variable names in .env.example, and basic quality config.
Do not add forecasting, an assistant, or decorative pages yet.

Create concise docs/PROJECT_BRIEF.md, docs/PROJECT_STATE.md,
docs/DECISIONS.md, docs/EVIDENCE.md, and a demo outline. Copy the chosen
planning decisions as proposals, never as completed behavior. Update
root AGENTS.md to use the active docs checkpoint and relevant references.
Define a small Site/Reading/Delivery/State API contract with provenance,
UTC timestamps, litres, freshness, and simulated status. Reserve breach
and physical empty time must remain different fields.

Write exact host-appropriate development/check commands with a supported
Windows route. Update PACKAGE_STATUS.json to the actual partial-build
phase when implementation begins; refresh manifests for later delivered
archives rather than reusing a preparation checksum. Record
dependency versions rather than inventing successful installs. Verify
the foundation's import/type/build checks as applicable. Make a scoped
initial commit only after inspecting its staged files; no secrets or
reference clones. Update the checkpoint with actual results and next
Prompt 02. Report the tree, locked choices, and failures if any.
```

## Prompt 02 — The first working vertical slice

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

## Prompt 03 — Prove the smallest AWS path early

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

## Prompt 04 — Reserve forecast and last-action deadline

**Result:** the core decision, with correct accounting and honest uncertainty.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, and the numerical contract in
docs/PROJECT_BRIEF.md. Implement deterministic forecast/decision modules
and GET /sites/{id}/forecast without an LLM.

Estimate usage only where observed storage changes and recorded inflow
make the estimate identifiable. Mark insufficient/ambiguous history.
Compare recent-average and same-hour historical-median baselines. Add a
small EWMA/trend candidate only if evidence justifies it. Features at an
origin use only data observed and available by that origin, including
delivery knowledge as it stood then. Unknown future weather/inflow must
not appear as known features. Never expose scenario truth/labels to logic.

Anchor projection at the latest measured volume/time. Add only later
inflow not already included in that measurement; a new observation resets
the anchor. Infer historical consumption with inflow inside the exact
observation interval and a documented timestamp convention. Keep delivery
and other-inflow ledgers disjoint; distinguish measured and projected-now
volume. Do not double count deliveries or abnormal usage. Bound storage
to [0, capacity], recording overflow and unmet demand separately. Return
reserve_breach_at and empty_at separately, no_breach_within_horizon when
applicable, and UNKNOWN for stale/insufficient input. A future delivery
is a conditional plan, not arrived water; show a conservative supply case.

latest_action_at = conservative reserve breach - supply lead time -
safety buffer. Keep overdue deadlines overdue. Use explicit demand/supply
sensitivity scenarios first; don't call them calibrated confidence bounds.
Persist the forecast origin, evidence version, method, assumptions, and
provenance. Show source age and key assumptions in the operations page.

If sufficient real history is absent, generate the first minimal seeded
chronological evaluation history now, visibly simulated with separate truth
metadata. Establish partitions only after the dataset exists and record
its fingerprint. Create train/validation/final-test partitions with purging
where target windows overlap. Select method on validation only; freeze
test data for Prompt 08. Verify hand-computed constant/zero use, breached
reserve, missing inflow, delayed supply, capacity overflow, no crossing,
out-of-order observations, stale readings, and midnight/timezone cases.

Run relevant checks; document real results and limitations. Update state,
evidence, assumptions and commands; make a scoped commit. Next Prompt 05.
```

## Prompt 05 — Abnormal depletion and deterministic scenarios

**Result:** a visible incident goes through the real ingestion/forecast path.

```text
Read AGENTS.md and docs/PROJECT_STATE.md. Implement sustained abnormal
depletion detection and a controlled demo replay around the current core.

Preserve Prompt 04's frozen forecast-evaluation history. Generate additional
incident scenarios chronologically with a fixed seed and separate detector
train/validation/final-test windows; do not replace a forecast holdout to
improve results. Model:
morning/evening demand, observed deliveries, realistic measurement noise,
and separate scenario truth. Start with healthy, sustained excess usage,
delayed delivery, intervention followed by normal demand, and new delivery.
Keep the physics coherent with capacity, reserve, supply, and consumption.
Do not tune fixtures until the favored model/detector wins. Store labels
only in evaluation/scenario metadata, never operational feature fields.

Use past residual dispersion plus persistence (e.g. sustained robust-score
or EWMA evidence), with configurable thresholds selected on validation.
Isolated noise should not repeatedly alert. Missing/gapped/irregular data
must not count as evidence of normal consumption. Report excess use as
abnormal depletion with possible causes, not a confirmed physical leak.
With aggregate tank data, do not identify a block or pipe. Use block labels
only when actual simulated/genuine submeter readings exist and are labeled.

Provide demo reset/seed/replay endpoints restricted to isolated simulated
sessions and bounded resources. Public guests have no real notification
rights; authenticated owner rehearsals may send clearly simulated alerts
only to an authorized confirmed test destination after concrete approval.
The scenario
must insert readings through the same ingestion API/domain path. UI cannot
directly set anomaly/forecast/resolved values. Record the replay clock and
provenance so future simulated observations don't look like real telemetry.

Add a clearly labeled Demo Lab. Sustained excess usage should move the
reserve forecast/deadline and evidence; repair replay supplies later normal
readings but cannot simply clear the incident. Test determinism, no future
truth leakage, noise, gaps, sustained onset, and duplicate replay steps.

Run relevant checks, update data provenance/model notes/state/evidence,
commit this milestone. Next Prompt 06.
```

## Prompt 06 — Approved notification and evidence-based verification

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

## Prompt 07 — Make the decision understandable in seconds

**Result:** a coherent operations screen with observable state changes.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, the current contract, and demo
outline. Improve the existing frontend around the functioning core.
Do not add backend domains, new models, or a decorative marketing site.

Design one operations screen for a caretaker. Lead with the reserve risk
and latest action time, then usable litres, reserve threshold, supply
status, data age/source, sensitivity range, and one recommended action.
Show the tank and storage trajectory, reserve line, planned supply marker,
and action deadline. Use simple chart/SVG components and the established
design system; unnecessary 3D is out of scope.

Keep a visible simulated/manual/modeled provenance badge. Distinguish
UNKNOWN, WATCH, ACT NOW and verified recovery through text/icons as well
as color. Display uncertain/overdue forecasts honestly. Explain reserve
versus empty time. A published notification cannot look like a completed
repair. Place Demo Lab controls apart from operational actions.

Make approval review the exact current proposal and destination scope.
Use accessible buttons, keyboard focus, readable contrast, and sensible
small-screen layout. Include loading, API unavailable, stale data, empty,
and retry states. Don't render invented zeroes while data loads. Keep
advanced evidence/metrics in a details drawer rather than many dashboards.

When browser tools are available, run the actual app and inspect the
main screen, abnormal scenario, pending verification, error state, and
a narrow viewport. Fix observed usability issues. If browser verification
is unavailable, state that limitation and supply a concrete manual check.

Run frontend typecheck/build and meaningful workflow/component checks.
Update the demo click path, evidence, and checkpoint. Commit. Next 08.
```

## Prompt 08 — Evaluation and claims from one source of truth

**Result:** reproducible evidence, including unfavorable results.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, data provenance, forecast/detector
selection notes, and frozen split definitions. Build a reproducible
evaluation report; do not add product features or optimize on test data.

Verify chronological generation and point-in-time feature availability
at each forecast origin, not merely ordered split timestamps. Assert
future readings/deliveries and scenario labels can't reach features.
Train/select/tune only on train/validation. Report the untouched final
holdout once. Do not change the selected method because test results
favor a different one; disclose the finding and prospective next step.

Write artifacts/evaluation.json as the authoritative output; generate
human tables/README figures from it. Include seed, code/data hash, windows,
origin/horizon, number of samples, split boundaries, missing-data handling,
method chosen and why. Compare baselines and candidate even if the baseline
wins. MAE must specify volume or usage target and unit. Report reserve-
breach timing error only for measurable events; report censoring/no-event
counts separately. Include anomaly delay, false alerts per site-hours,
missed labeled scenarios, and known confounders.

For scenario impact, share starting state, seed, exogenous baseline demand,
supply and noise draws across intervention/no-intervention branches. Change
only the declared intervention effect (e.g. repair reduces excess use;
extra delivery adds inflow), documenting that effect as an assumption.
Compute shortage duration from unmet demand, separate from reserve breaches.
Report warning margin,
projected shortage duration and estimated excess litres with explicit
SIMULATED/PROJECTED labels. Do not call them observed water savings.

Use independent hand-calculated examples for metric arithmetic. Check
API/UI/report values against the JSON artifact to prevent documentation
drift. Document manual/synthetic data limits, no confirmed leak localization,
no guarantee of supplier response, uncertainty, and auth/demo boundaries.

Update model notes, provenance, EVIDENCE, README, and checkpoint with actual
results. Run evaluation and targeted checks; commit. Next 09 only if core
and deployment/equivalent AWS gates are green; otherwise proceed to 10.
```

## Prompt 09 — Optional evidence-grounded Strands assistant

**Gate:** complete core loop and available time. **Result:** useful explanation/what-if assistance, never numerical authority.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, evidence, and demo plan. If core
or reliability gates are incomplete, skip this optional milestone and
explain which core gate receives the time. Don't add an assistant to hide
missing deterministic behavior.

Verify current official Strands documentation and installable version.
Use a supported provider only if actual account credentials/model access
are available. Codex/Plus access is not an application API or Bedrock key.
Never hard-code a model ID, region entitlement, or promised free access.

Add bounded read/simulation tools: get_state, get_forecast, get_incident,
simulate_supply_delay, simulate_demand_change, simulate_added_supply.
Scope tools to the current authorized site and evidence version. Simulations
return a preview without writing readings, proposals, approvals, or actions.
Do not expose approval/notification/resolve tools to the agent. Do not
give it shell, filesystem, arbitrary URL, or unrestricted cloud tools.

Return structured fact references and short explanations. Bind each
operational claim to a tool field, unit, timestamp and provenance. A
number-whitelist alone is insufficient: the same number can be assigned
the wrong meaning/unit/time. Prefer backend-rendered numeric facts plus
model text that cites fact IDs. Reject unsupported/stale claims and use
a deterministic template on validation/provider/timeout failure.

Suggested questions: Why did the deadline move? What if supply is six
hours late? How much buffer would an extra delivery create? Keep the
assistant as a small panel, not the whole product.

Test tool schema/range bounds, wrong-site access, invented/wrong-unit facts,
stale evidence, malicious instructions in data, missing data, provider
failure, and attempts to approve or resolve. Fake-model tests are not proof
of live inference. Record a real call/tool trace if available, and label
scripted tests or deterministic fallback visibly. Run relevant checks;
update state/evidence/limitations; commit. Next Prompt 10.
```

## Prompt 10 — Integration, failure handling, and deployed parity

**Result:** the whole implemented loop behaves truthfully locally and in the claimed runtime.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, actual deployment notes and demo
path. Complete integration and repair failures; do not add stretch features.

Run the full flow against local persistent storage and the actual deployed
AWS path where authorized: healthy → sustained excess → changed forecast
→ delayed-supply preview → proposal → approval → notification status →
post-intervention readings → deterministic verification → incident evidence.
Prove cloud persistence across fresh invocations. Ensure latest evidence
version wins when two updates race; old forecasts can't overwrite new ones.

Check targeted failure behavior: stale/missing readings, provider timeout,
notification failure, duplicate submissions, API outage, denied writes,
unauthorized cross-site access, and reset while a request is in flight.
Guest demo/reset/seed cannot touch real operational state or notification
targets. Do not leak credentials or personal details in logs/artifacts.

Add only useful operational logs/health evidence: request/action/run IDs,
source timestamps, transitions and failure reasons. Add a scheduler only
if stale-state/verification refresh actually needs it; give it bounded
idempotent work. Do not add Step Functions solely for the sponsor diagram.

Run backend checks, frontend typecheck/build, SAM validation, and critical
integration/browser checks once, rerunning affected gates after repairs.
If account/service blockers remain, preserve and demonstrate the real
AWS open-source route and label missing cloud proof. No fake service badges.

Update commands/README, deployed URL and evidence where real, checkpoint,
and known limitations. Inspect the diff and commit. Next Prompt 11.
```

## Prompt 11 — Hostile judge review

**Result:** an independent ranked repair list, no new feature requests.

```text
Read AGENTS.md and docs/PROJECT_STATE.md. Act as a skeptical Environmental
Hacks reviewer seeing the project for the first time. Review the current
app/code, README, evidence artifacts, demo path, deployment claims and
the latest official judging/submission requirements. Do not implement yet.
Delegate an independent review if available with read-only ownership.

Answer briefly:
1. Who is the user and what decision changes?
2. Does the first screen reveal the decision without narration?
3. Is every reserve/empty/deadline term consistent?
4. Which AWS capability is implemented and visible in the video path?
5. Where can simulated/manual data be mistaken for real sensors?
6. Does any model/test/report claim overreach its evidence?
7. Could a failed alert look successful or a repair claim look verified?
8. Can missing telemetry wrongly reassure the user?
9. Can guest access modify real state or trigger external messages?
10. Can a fresh clone follow the documented commands?
11. What is the likeliest demo failure and smallest prevention?
12. What should be removed rather than completed?
13. Does the assistant help a real task, and does its fallback preserve it?
14. Can the complete flow be shown under three minutes?
15. What would justify rejecting this submission?

Write docs/JUDGE_REVIEW.md. For each actionable issue give P0 (eligibility,
wrong core result, misleading success or failed demo), P1 (material clarity,
correctness or reliability), or P2 (polish); source location; reproducible
trigger; smallest repair; and the acceptance check. Distinguish observed
defects from hypotheses. Update checkpoint with the repair order. Do not
recommend a new domain, new architecture, or new features at this stage.
```

## Prompt 12 — Repair, rehearse, and freeze the demo

**Result:** a repeatable under-three-minute path with no unresolved P0.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, docs/JUDGE_REVIEW.md, and actual
demo/deployment evidence. Fix P0 issues first and material P1 issues within
the remaining event time. Preserve working interfaces. After the fixes,
enter DEMO FREEZE: no new features, architecture migration or dependency
upgrades except an essential P0 repair.

Create small Windows-compatible demo reset/seed/check commands and a
preflight that validates required endpoints/config/fixtures without
printing secrets. Reset only disposable demo state; never erase real
observations or send notifications. Keep seed/replay deterministic and
visibly simulated. Fail loudly on missing dependencies or service access.

Rehearse the exact flow from a reset: healthy reserve → sustained anomaly
→ shifted deadline → six-hour delay preview → explicit request approval
→ honest receipt/publication proof → subsequent readings → verification
→ one evaluation result and limitation → actual AWS execution/use.
Do three clean rehearsals if failures/changes warrant them, confirming
repeatability and reset behavior rather than rerunning broad suites.

Write docs/DEMO_SCRIPT.md with exact clicks, narration, expected states,
actual numbers/evidence references, reset and fallback. Aim for 2:45–2:55.
Fallback is truthful: provider failure uses deterministic explanation;
blocked AWS action is shown failed/pending or the real local AWS-tool route,
never edited into an apparent success. Simulated intervention cannot claim
a physical repair. Check production build and the actual URL if claimed.

Update checkpoint/evidence and report readiness for frontend, backend,
AWS, scenarios, notification, assistant/fallback, verification, tests and
deployment, plus remaining P0/P1. If any P0 remains, keep working on the
smallest repair while time permits; do not call the demo ready. Commit
repairs. Once gates are green, freeze and move to Prompt 13.
```

## Prompt 13 — Honest submission, writeup, and blog

**Result:** concrete submission material grounded in the completed build.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, final demo script, evaluation JSON,
deployment/runtime evidence, and latest official form/rules. Do not change
product behavior. Finish the submission materials from what actually works.

Prepare docs/SUBMISSION.md with a 40-word and 150-word description, precise
user/problem/decision, how it works, implemented AWS use, data provenance,
evaluation method/results, limitations, reused libraries/assets/licences,
and disclosure of Codex/other AI tools. Separate prototype from future plans.
Do not invent a user interview, physical deployment, tanker booking, saved
litres, model accuracy, paid customer, or user adoption.

Finalize README with the real demo/video/runtime links, architecture,
reproducible Windows/local setup, cloud or AWS-tool instructions, demo
reset, evidence artifact links, and limitations. Keep the paper architecture
consistent with actual services. Generate reported figures from the final
evaluation artifact; do not copy example numbers from the preparation pack.

Draft docs/BLOG_DRAFT.md for AWS Builder Center: actual problem, deadline
idea, implementation, what failed, AWS lessons, results, limitations and
next steps. A blog is an optional prize opportunity, not a replacement
for the mandatory writeup. Don't invent weekend anecdotes. Prepare drafts
locally; publish only within explicit existing publishing authorization.

Create a claim audit: Claim | Code/artifact | Runtime/demo proof | Provenance
| Safe to publish. Flag unsupported claims and repair the prose. Check
signed-out access to the public repo, claimed deployment, and public/unlisted
YouTube video. Verify actual video duration is under 180 seconds and AWS
use is visible. If recording/upload tools or account access are unavailable,
provide the exact user steps and keep those items visibly incomplete.

Verify final kickoff/history/cutoff requirements without altering history.
Use the earlier confirmed deadline buffer. Prepare a concrete submission
checklist; submit/publish only when explicitly authorized and accessible.
Update checkpoint with completed items, real links and remaining user-only
actions. Never report 'submitted' without a confirmation from the form.
```

## Prompt R — Resume without rebuilding

**When:** a chat closes, context compacts, or you move to a new session.

```text
Resume the Environmental Hacks work in the current/extracted project root. Read AGENTS.md and
docs/PROJECT_STATE.md if present, otherwise prep/PROJECT_STATE.md.
Inspect Git status, recent commits, current files, and available evidence.
Don't assume earlier chat memory or a green gate from prose alone.

Identify the current milestone, what's implemented, dirty work ownership,
actual last check results, blockers, and the next incomplete acceptance
criterion. Read only the brief/code/docs needed for that next action.
Verify the current event window before code work. If not open, remain in
preparation; after the confirmed cutoff, preserve the submitted revision
and label any further development separately from the event submission.

Preserve completed work and other workers' edits. Do not scaffold again,
rename the project, replace the stack, retrain to obtain nicer metrics,
or repeat successful broad checks without a concrete reason. Repair stale
checkpoint statements from observed evidence and note any discrepancy.

Continue the smallest next action in the active milestone, run its relevant
checks, fix failures, and update the checkpoint. Report observed progress,
exact results, and the next prompt ID. Do not ask me to paste the old chat.
```

## Prompt X — Rescue a late or overgrown build

**When:** the core loop is incomplete or time is shrinking.

```text
Read AGENTS.md, the active checkpoint, current demo path and confirmed
cutoff. Rescue the existing project within the remaining time. Don't
restart, switch domains, or add features.

Rank unfinished work by what can break the recorded core flow: reading,
deadline, sustained anomaly, concrete proposal, explicit approval,
truthful notification status, new-reading verification, usable screen,
real AWS use, and reset. Identify the smallest missing link.

Cut optional assistant, extra scenarios, custom ML, 3D, maps, complex
schedulers and unnecessary services from the active plan when they block
completion. Preserve the usable simple baseline and current interfaces.
Do not silently delete unrelated work; remove unreachable/broken demo
paths only with a scoped rationale and recoverable diff.

Implement the smallest missing link and its meaningful failure checks.
If cloud access is blocked, preserve a genuine AWS open-source route and
disclose it. If receipt is pending, retain PUBLISHED after confirmed SNS
acceptance and show receipt pending/unknown separately. If publication
itself is uncertain, show uncertain dispatch. No simulated 'delivered' or
'verified' state as a shortcut.

Update scope/decisions/checkpoint, rerun the affected critical path, and
report remaining P0/P1 plus the exact next repair. Continue necessary
repairs while time permits; 'almost works' is not completion.
```

## Prompt P — Coordinate bounded parallel work

**Gate:** stable contract and disjoint file ownership.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, agreed contracts and BUILD_PLAN.
Identify genuinely independent subtasks in the current milestone. Use
available subagents if they improve speed or review quality; don't create
user-owned chats unless the user explicitly requests them.

You are the integrator. Own contract changes, migrations, dependency locks,
CI, deployment, and the shared checkpoint. Give each worker a bounded goal,
directory/file ownership, inputs, acceptance checks and handoff format.
Examples: forecast module/tests; frontend against stable API; read-only
review/evidence. No two workers edit the same file. Contract/dependency
changes return to you before integration. Shared filesystem means shared
edits; don't assume isolation. Separate human chats need worktrees or
explicit disjoint ownership.

Workers report owned files, behavior, exact checks/results, interface
expectations and unresolved failures. Don't let all workers update the
same state document or commit overlapping changes. Gather reports, inspect
diffs, resolve conflicts, integrate the actual workflow, and run the
relevant combined checks. If agents aren't available, execute sequentially.

Write one truthful checkpoint and commit scoped integrated work. Parallel
completion claims do not replace integration evidence. End with the next
incomplete gate, not a list of unconnected new feature ideas.
```

## Prompt A — Choose school air before implementation if evidence favors it

**When:** actual school access/problem is stronger than the water hypothesis. **Result:** a coherent replacement plan, not two products.

```text
Read AGENTS.md, prep/PROJECT_STATE.md, prep/PROJECT_BRIEF.md and the source
research. Evaluate actual school/caretaker evidence supplied by the user.
This prompt re-scopes planning before implementation; do not create both
domains or destroy working code. If implementation already exists, explain
the cost of a late pivot and preserve the stronger complete path.

If school evidence favors Air, lock SAANS for one principal deciding
whether and when to move assembly/PE under a school-configured policy.
Scope: verified provider/model output → freshness/scale labels → relative
exposure/time-window options → explicit reviewed notice → schedule
acknowledgment. Do not claim school closure authority, medical safety,
clean indoor air, or measured health improvement.

Verify current provider docs and make a read-only request. Open-Meteo's
Delhi CAMS output is roughly 45 km modeled data, and US/European AQI is
not official Indian AQI. OpenAQ needs a key. Do not interpolate synthetic
'stations' into real readings or train on synthetic history and report
real forecast accuracy. Display valid timestamp, retrieval time, provider,
AQI convention, units, modeled/sensor/simulated status and attribution.

Use the provider forecast first; optimize only within actual school hours
and constraints. Find a relatively lower predicted exposure window, not a
'safe' hour; allow no acceptable window. Official-policy claims require
current primary authority sources. Missing/stale data → UNKNOWN.

Revise the brief, contract, milestone gates, demo, and numbered prompts
coherently for Air. Keep early AWS proof, protected notice approval, honest
receipt, chronology/evidence discipline, compact memory and recovery.
Verification confirms schedule/action acknowledgment, not physical air
improvement. Remove water-specific assumptions from the active plan;
retain the dated research as history. Report the chosen domain and next
permitted milestone with evidence. No submission code before kickoff.
```
