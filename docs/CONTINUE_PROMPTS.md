# Continuation prompts

Read AGENTS.md, AI_HANDOFF.md, PACKAGE_STATUS.json and docs/PROJECT_STATE.md first. Continue existing source; preserve actual dates and evidence.

## Resume

```text
Continue JalRakshak from the active checkpoint. Inspect git status, source and
verification artifacts. Implement the next unfinished milestone and verify it.
Keep simulated and operator-entered data distinct. Update memory and archive;
do not restart or fabricate metrics.
```

## Review and repair

```text
Run the current app and read REVIEW_RESPONSE, API_CONTRACT and EVALUATION.
Reproduce a concrete correctness or usability defect. Repair it with meaningful
checks. Preserve the frozen evaluation protocol and report failures and early
warning costs. Do not tune on holdout data or request favorable ratings.
```

## Caretaker pilot

```text
Inspect the local observed workspace and available actual logs. Validate tank
units, timestamps, arrived-inflow completeness and measurement error assumptions.
Separate participant feedback and real data from simulator evidence. Import only
authorized actual records. Record what was observed; do not invent interviews,
sensor accuracy, savings or field reliability.
```

## Refine the demo

```text
Rehearse DEMO_SCRIPT in the running app. Improve clarity, keyboard and mobile
usability, forecast assumptions, UNKNOWN recovery and backup flow. Keep the demo
under three minutes. Show actual evidence and limitations; do not fake receipts.
```

## Deploy when scoped

```text
Read DEPLOYMENT and infra/template.yaml. Check available identity without
revealing secrets. Prepare Linux/SAM packaging. If account,region,budget or
destination scope is absent, complete a concrete reviewable deployment plan.
Deploy only within supplied authorization. Prove health,persistence,CSRF,quotas
and the full demo loop. Cloud guests must not accept observed-site records.
```

## Package and independent review

```text
Verify current source, locks, notices, numerical evaluation and local workflows.
Run scripts/package.py for the lean app and --full-context for historical research.
Verify manifest hashes and run from an extracted folder. Update the checkpoint
with actual results and remaining gaps. Preserve truthful history and event
eligibility; use REVIEW_THIS_PROJECT for independent evidence-based assessment.
```
