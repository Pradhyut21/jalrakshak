# Recommendation and reference lessons

Prepared October 1, 2026. This is research and planning, not a built submission or a guarantee of an award.

## Recommendation

Use **JalRakshak** as the provisional Heat and Water project in the existing SAANS workspace. Build for one caretaker deciding whether stored water lasts until reliable supply, when action must begin, and whether later observations support recovery. Validate that problem with a real caretaker before locking the track at kickoff.

Water is the preferred engineering direction because inventory, consumption, and delivery lead time support an understandable deadline; a controlled scenario can demonstrate the whole incident in a short recording; and the MVP does not need a new ML model, health-policy expertise, public-data availability, or hardware. These are our feasibility judgments. They do not imply that Water is less competitive or that judges prefer it.

Air remains strong if you have a school connection and a concrete timetable decision. A working Open-Meteo request helps feasibility, but Delhi output is coarse modeled CAMS data, with US/European AQI rather than official Indian AQI. The earlier pack's “safe outdoors” wording and station-like interpolation need stronger evidence. A school prototype should recommend a lower predicted exposure option under configured policy, disclose data scale, and never equate a less polluted hour or indoor location with safety. [Data documentation](https://open-meteo.com/en/docs/air-quality-api).

Do not combine Air and Water. Keep one user, one scenario, one consequential decision.

## What the three references contribute

| Reference | Pattern to adopt | Boundary to preserve |
|---|---|---|
| Beacon Night Shift | One memorable incident, constrained intervention, explicit approval, recovery check | Its filmed local mode scripts more than just model output; it does not establish independent cloud recovery |
| CampusEvac | A scenario and intervention that a viewer can immediately understand | Client-authored events and reports are prototype trust assumptions, not independent physical truth |
| Fraud Risk Manager | Baselines, inspectable metrics, operational tradeoffs, real local HTTP tests | Synthetic outcomes, chronology concerns, stale metric prose, and notification failure semantics need correction |

The [official results](https://www.wemakedevs.org/aws/first-commit/projects) confirm Beacon and CampusEvac as award recipients. Fraud Risk Manager is useful reference engineering but absent from the listed winners/runners-up. We do not know why the judges selected particular projects, and no project of your own from First Commit was supplied for diagnosis.

### Beacon: borrow the lifecycle, strengthen the evidence

The frozen submission contains concrete action validation, approval records, a state machine, and a recovery module. Its design makes “proposed,” “approved,” “executed,” and “resolved” different states. That separation is directly useful for water operations. [State machine](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/remediation-template.yaml), [verification module](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/remediation/verify.py).

Its own submission discloses account/model restrictions. The local server replaces the agent and generates recovery observations. Treat that as useful local integration evidence, not proof of cloud/model reliability. The approval gate also uses a substring check, and the action flow has an interruption gap between approval consumption and result recording. Our prompts use structured approval outside the assistant, bind it to current evidence, preserve uncertain dispatch outcomes, and test missing telemetry. [Disclosure](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/docs/submission.md), [local substitutions](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/scripts/local_server.py), [approval tools](https://github.com/Prashant-thakur77/Beacon/blob/c3f63e53faf07fe5fb5f19255ddb0ddbb7156c27/src/beacon/voice_tools.py).

### CampusEvac: make cause and consequence legible

Its role-specific views, explicit objectives, interventions, and reports communicate a shared situation. For JalRakshak, the equivalent is a tank trajectory, reserve line, supply marker, and action deadline that visibly change after abnormal depletion and a delayed delivery. Lightweight SVG is sufficient; the transferable value is clarity rather than the 3D stack. [Simulation UI](https://github.com/AfreenInnovates/campus/tree/568a585021fae096799599bb3d3fbbb9f6b3e6f6/app/simulation), [report computation](https://github.com/AfreenInnovates/campus/blob/568a585021fae096799599bb3d3fbbb9f6b3e6f6/app/simulation/report.ts).

The report API recomputes scores from submitted measurements; its verifier explicitly acknowledges that valid-looking forged timelines can pass. Use server-owned operational state and record exactly which subsequent readings support recovery. Even server records of a manual reading remain a human observation, not independently calibrated sensor truth. [Report route](https://github.com/AfreenInnovates/campus/blob/568a585021fae096799599bb3d3fbbb9f6b3e6f6/app/api/report/route.ts), [advisory verifier](https://github.com/AfreenInnovates/campus/blob/568a585021fae096799599bb3d3fbbb9f6b3e6f6/app/api/verify/%5Bcode%5D/route.ts).

### Fraud Risk Manager: adopt baseline honesty, correct the pipeline

The saved comparison admits that a simple model outperforms the complex model. Its local webhook tests check a genuine HTTP receiver. Those practices are worth adopting. [Baseline artifact](https://github.com/aaryanpawar16/fraud-risk-manager/blob/3937fae0085469e9e1613d07f2647903f9051dd8/backend/ml/reports/baseline_comparison.json), [receiver tests](https://github.com/aaryanpawar16/fraud-risk-manager/blob/3937fae0085469e9e1613d07f2647903f9051dd8/backend/tests/test_alerting.py).

But its generator updates customer history before sorting randomly assigned timestamps, so a chronological split alone does not prove point-in-time integrity. Its webhook failure path still records success, suppressing a later attempt. Our prompts demand chronological generation, origin-specific features, validation-only selection, honest failure states, and regenerated reports from one JSON artifact. [Generator](https://github.com/aaryanpawar16/fraud-risk-manager/blob/3937fae0085469e9e1613d07f2647903f9051dd8/backend/ml/generate_synthetic_data.py), [alerting](https://github.com/aaryanpawar16/fraud-risk-manager/blob/3937fae0085469e9e1613d07f2647903f9051dd8/backend/app/services/alerting.py).

All three reviews are static: source, documentation, artifacts, and selected committed screenshots. No reference application or test suite was executed. Detailed findings and pinned commits are in `research/BEACON.md` and `research/CAMPUS_AND_FRAUD.md`.

## What changes from the supplied prompt packs

- Resolve the conflicting directions into one provisional choice, with a problem-validation gate.
- Make the first deployment early, rather than leaving AWS packaging and account restrictions to Saturday night.
- Use a modular API, light forecasts, and only necessary AWS services. Step Functions and model inference are optional enhancements.
- Replace repeated “read every document” instructions with one compact checkpoint plus task-relevant references.
- Require validation-only method selection; the final holdout cannot be used to tune the system.
- Distinguish reserve breach from physical empty time, sensitivity from calibrated confidence, and aggregate depletion from localized leak detection.
- Distinguish SNS publication, endpoint receipt, human acknowledgment, actual intervention, and environmental verification.
- Give parallel workers disjoint ownership and one integrator. More concurrent edits do not make dependent milestones independent.
- Avoid treating test count or model complexity as judging goals. Use tests that can catch a real failure in the demo or claim.
- Make Windows-compatible commands, recovery prompts, scope cuts, and failure fallbacks explicit.

## Prior art and defensible differentiation

[Flume](https://flumewater.com/) already monitors usage and provides abnormal-use alerts; [WINT](https://wint.ai/) already offers building water analytics and action controls; [EPA EPANET](https://www.epa.gov/water-research/epanet) provides established water-system modeling. Do not claim that forecasting, anomaly detection, or AI water management is newly invented.

Our proposed differentiation is the specific caretaker workflow: usable reserve + uncertain consumption + configured supply lead time → deadline → approved request → fresh state → evidence of recovery. User interviews and implementation must establish whether that combination is useful. We have not established market size, uniqueness, or willingness to pay.

## How to use Codex well

Use Codex for repository research, scoped implementation, bounded parallel work, browser inspection when tools are available, meaningful tests, document consistency, and hostile review. Use durable files so a resumed chat can recover the current facts. Tool availability, model access, and usage depend on the account and environment; prompts cannot change those entitlements. [Official pricing](https://learn.chatgpt.com/docs/pricing), [long-running project memory](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex).

Keep AGENTS short and read documents according to the task. Excessive repeated instruction can consume useful context and slow work. [Official instruction guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

The best use of additional capacity is independent implementation/review with concrete acceptance gates. The final video still has less than three minutes to communicate the result. No prompt sequence can guarantee a win; this one is designed to make the submitted work coherent, credible, and reviewable.
