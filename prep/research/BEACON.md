# Beacon: static repository review

Reviewed on 1 October 2026 for SAANS / Environmental Hacks preparation. Scope: repository files, a bundled UI screenshot, and the GitHub repository page. No dependencies installed, tests executed, application started, cloud writes performed, or live deployment authenticated. Award status is not established by this review.

## Which version was reviewed

The repository distinguishes two hackathon submissions: `main` for First Commit and `assemblyai` for a later voice-agent event. The First Commit submission tag resolves to **`c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27`**. Current `main` is `03247dba07cb61727da10a4bc4fe5ca209e23fc9`; its only difference from that tag is four README lines directing visitors to the correct branch. Consequently, the code observations below also apply to the frozen First Commit entry. [Submission snapshot](https://github.com/Prashant-thakur77/Beacon/tree/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27)

## What makes the product memorable

Beacon serves one person in a specific situation: a tired on-call engineer facing a repeat outage. Its differentiator is an observable sequence with a second act: discover what broke, propose one controlled fix, obtain consent, apply it, check recovery, and let the engineer grant a bounded permission for the same future incident. The next recurrence is handled without another page. This turns an infrastructure assistant into a story with a measurable outcome. [Submission problem and flow](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/docs/submission.md#L9-L22)

The included Night Board screenshot puts outcome counters, the main conversation, recovery checks, a small before/after error chart, and a judge-friendly “Run the night” control on one page. It labels local mode visibly. This is a more persuasive pattern than spreading the essential demonstration across many generic dashboard pages. [Bundled screenshot](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/docs/assets/night-board.png)

## Architecture supported by code

| Stage | Observed implementation | Environmental project lesson |
|---|---|---|
| Detect and diagnose | A CloudWatch alarm enters the triage handler. Logs, deterministic security-group drift against a healthy snapshot, and a CloudTrail change ledger feed the RCA. Deterministic diagnosis can replace model-suggested resource parameters. | Let validated readings and a transparent rule detect risk; use an LLM to explain supporting evidence. |
| Propose | A small action registry rejects unknown actions, missing/extra parameters, wrong types, and booleans masquerading as integers. Proposals include dry-run evidence and blast radius. | One practical intervention should have explicit inputs, conditions, owner, and scope. |
| Consent | Tools read the current transcript from server-side turn context, rather than trusting a model-supplied confirmation argument. An approval stores the exact action, canonical parameter hash, channel, quote, and expiry. | A model may suggest an action; an explicit UI/server decision should authorize consequential action. |
| Execute and verify | Step Functions follows DryRun → RequireApproval → Execute → Wait → Verify, up to six checks, then Resolve or Escalate. Verification combines a fresh alarm transition, error metric, and action postcondition. | Separate “plan generated,” “action accepted,” and “outcome checked.” |
| Repeat handling | Contracts match alarm, action, and exact parameter hash; uses are consumed conditionally and bounded by expiry. | A repeated workflow can reuse a reviewed plan without widening its scope. |

Code: [triage and contract handler](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/handler.py), [registry](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/remediation/registry.py#L100-L114), [approval record checks](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/approvals.py#L168-L208), [state machine](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/remediation-template.yaml#L423-L549), [three checks](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/remediation/verify.py#L145-L172), [contracts](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/contracts.py#L107-L151).

Sponsor services have assigned jobs: Bedrock/Nova and Strands for reasoning, Transcribe/Polly for voice, DynamoDB for records, Step Functions for orchestration, and CloudWatch for observation. Code and IAM keep the conversational role separate from infrastructure write permissions. The transferable advantage is justified service integration; the number of services itself is not a useful target. [Template safety tests](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/tests/test_template_safety.py#L107-L228)

## Evidence and runtime limits

There is substantial test infrastructure: local HTTP workflow tests, a walker that drives the actual ASL through the handler, invalid-approval checks, bounded-verification checks, template IAM assertions, and CI with lint, types, tests, template validation, and a frontend build. The README says 244 tests; that count and pass status were not independently verified here. [Local workflow tests](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/tests/test_local_server.py#L42-L139), [ASL tests](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/tests/test_asl_walk.py#L242-L323), [CI](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/.github/workflows/build.yaml).

The submission explicitly reports blocked Bedrock access and CloudFront creation during judging and says the film uses a scripted-model local loop, alongside real account deployment evidence. This is an honest author disclosure, not independent confirmation that every cloud component worked. [Submission disclosure](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/docs/submission.md#L7)

The local simulation is broader than the README phrase “only Bedrock is scripted” suggests. It inlines the state machine; manufactures zero metrics and an OK alarm when the restored rule exists; replaces the agent; disables backend Polly; substitutes log retrieval, RCA text, token usage, and prefetch. This proves useful integration behavior against moto, but cannot establish independent real-world recovery, LLM reliability, voice transport performance, or actual model cost. [Simulation substitutions](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/scripts/local_server.py#L194-L268)

## Weaknesses to turn into stronger build prompts

These are static findings, not tested remote exploits.

1. **Consent is substring matching.** `approve_fix` checks whether `approve fix 1` occurs anywhere in the normalized transcript. A negative or quoted sentence containing that phrase, or `approve fix 10` when the proposed fix is 1, can satisfy that server gate if the model calls the tool. Tests cover loose affirmation and a valid phrase but do not show these adversarial cases. Require an exact structured decision bound to proposal ID/version; test negation, quotation, wrong IDs, repeated requests, and transcripts with multiple commands. [Gate](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/voice_tools.py#L313-L343), [tests](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/tests/test_voice_tools.py#L226-L247)
2. **Read-back does not enforce a separate consent turn or bind spoken days.** The contract code stores pending days/uses, accepts a broad grant regex, then uses the pending duration. It does not require a new turn identifier or compare spoken duration against the stored scope; a second call in the same turn can encounter the just-created pending record. Bind confirmation to a scope hash and a subsequent explicit confirmation event. [Grant matching](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/voice_tools.py#L50-L55), [read-back and grant](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/voice_tools.py#L442-L508)
3. **“Exactly once” is stronger than the implementation establishes.** The approval is marked used before the external action, and its result is recorded afterwards. A process interruption between those operations can consume approval without a durable result. Treat this as at-most-once dispatch plus replay of recorded results; test interrupted dispatch and reconcile uncertain outcomes. [Execution ordering](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/remediate.py#L158-L227)
4. **Missing telemetry must be domain-specific.** Beacon treats a recent absence of error-metric datapoints as zero errors. For air-quality or water monitoring, missing/stale readings must produce “unknown” and prevent a verified-safe claim. Copy the verification architecture, not this telemetry interpretation. [No-data behavior](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/remediation/verify.py#L89-L141)

## Patterns worth carrying into SAANS or JalRakshak

- Commit to one user, one costly decision, and one complete incident story.
- Show signal → evidence → intervention → human decision → follow-up observation on the main screen.
- Give judges one reproducible demo entrypoint, plus a labeled replay/simulator fallback and reset procedure.
- Keep rules, permissions, thresholds, provenance, units, timestamps, freshness, and unknown states outside free-form model claims.
- Measure outcomes that the prototype can substantiate: time to decision, valid action completion, observed readings, and refusal/error handling. Avoid claiming prevented illness, avoided floods, saved water, or causal environmental improvement from a synthetic scenario.
- Maintain compact status, decision, risk, learning, and demo documents; ensure stale planning statements are reconciled before submission. Beacon's `STATUS.md` contains an outdated “nothing has been deployed” item alongside later deployment claims, showing why context files also need a consistency review. [Status](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/docs/STATUS.md)
- Use the same action/state contracts for live, fixture, and replay paths, with visible provenance. A simulation should not silently generate the observations used to claim live success.

The strongest reusable lesson is an intervention with visible evidence and an explicit verification state. A larger feature count would dilute that advantage.
