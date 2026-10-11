# JalRakshak selection review — October 11, 2026

This is an assessment of the existing v0.2.2 application, not a new application release. Three separate AI review agents within Codex reviewed judging merit, technical evidence and submission compliance. They are additional perspectives from the same system, not independent model vendors or official judges. Their conclusions are summarized below without a selection probability or promised award.

## Verdict

JalRakshak is a credible local prototype with a focused caretaker workflow. It has not satisfied every competition requirement, and real-world usefulness remains unproven. The strongest pitch is a supply decision tied to reserve and delivery lead time, followed by approval and recovery supported by subsequent readings.

The decisive eligibility problem is the actual October 1 implementation start. Environmental Hacks opened October 8. The current rules exclude projects begun before opening, including rewritten projects. The user confirmed that no written organizer acceptance exists. Publishing or committing on October 11 does not change these facts. Preserve the existing October 2 Git commits, the October 1–3 build record and all truthful metadata. An explicit organizer ruling is necessary before claiming this build qualifies. [Official rules](https://www.wemakedevs.org/aws/env/rules)

## Judging and submission status

| Area | Status and evidence |
|---|---|
| Idea and environmental relevance | Fits Heat and Water: hostel tank reserve planning, supply lead time and abnormal depletion. Actual water savings or better caretaker decisions have not been measured. |
| AWS | Source contains a boto3 DynamoDB adapter, Lambda handler and SAM template. SQLite is the demonstrated local path. Offline checks do not prove SAM CLI use or live AWS execution. Local AWS open-source tools are permitted; cloud deployment is not compulsory. Demonstrate substantive AWS use in the recording and confirm any ambiguous SDK-only interpretation. [Overview](https://www.wemakedevs.org/aws/env) |
| Design and usability | Clear desktop and mobile presentation and recorded browser checks; no unfamiliar caretaker walkthrough. A new UI association defect is documented below. |
| Execution | A coherent deterministic incident loop, stale/missing-data UNKNOWN, separate reserve/empty timing and reading-supported recovery. A reviewer reran 41 relevant backend/evaluation tests successfully today. |
| Recorded demo | Script and screenshots exist; no recording or YouTube link has been supplied. Existing script reaches 3:00. Record less than three minutes and show actual AWS use. |
| Public repository and writeup | Local Git source and substantial documentation exist; no configured remote or submitted public repository was found. Final public links and submission receipt are absent. |
| Entrant and account eligibility | Registration/check-in, qualifying student/age status, team membership and Builder Center status remain unverified. Pending SheerID cases may submit and be considered while resolving verification. |

Public repository, public/unlisted YouTube recording and short writeup are mandatory submission components; AI tool use must be disclosed. A Builder Center blog is a separate optional prize entry. Prize selection and Amazon interview selection are separate; interviews are not guaranteed. [Rules](https://www.wemakedevs.org/aws/env/rules), [overview](https://www.wemakedevs.org/aws/env)

The organizer's October 6 announcement specifies **October 11, 8:00 PM IST** for online submissions. The schedule page still leaves hours unspecified, and the public submission page only returned loading content during review. Confirm the current form deadline and receipt. Inspection began around 5:57 PM IST on the final day. [Organizer announcement](https://www.wemakedevs.org/blogs/what-is-happening-in-delhi-on-10-october), [schedule](https://www.wemakedevs.org/aws/env/schedule)

## Comments from the three AI reviewers

The judging reviewer found the narrow incident loop more distinctive than a water-level dashboard or chatbot. They recommended leading with the caretaker's actual decision and showing the full workflow. Real usefulness, AWS proof and the submitted recording are the major gaps; additional features would not resolve them. They inspected code, reports and screenshots, without rerunning browser or backend tests.

The technical reviewer reproduced the evaluation and exercised the incident loop entirely in memory. Resolution required three later readings; the notice remained LOCAL_RECEIVED, with no external publication or physical-repair claim. They found substantial warning costs and a reproducible UI issue. Their highest priorities were genuine tank evidence and caretaker feedback, measuring unnecessary urgency alongside lateness on new validation data, and a demonstration that accurately proves the complete loop. The existing holdout must remain reporting-only.

The submission reviewer verified current primary rules and dates, inspected licensing and AWS source, and reran the offline infrastructure checker. It passed static AST checks, explicitly without SAM transformation, Linux build or deployment. They confirmed that no Git remote, local video or AWS execution proof was found. Boto3 is genuinely AWS-maintained, but its optional adapter is not exercised by the demonstrated SQLite path; offline quota tests inject a fake table. A template alone does not establish use of SAM CLI.

## Technical evidence and a newly found defect

All numerical results below remain synthetic, and holdout windows overlap:

- Original holdout: 0 late reserve predictions, mean 5.70 hours early and P90 13.85 hours. Predicted planning deadlines are already overdue in 120/120 windows versus 80/120 counterfactual truth deadlines. This deadline comparison is distinct from detector false alerts; all original windows eventually cross reserve.
- Stress: 12 late predictions, maximum 0.93 hours; all 208 windows without a true reserve crossing inside the evaluated horizon still have a predicted crossing. Stress earliness averages approximately 9.30 hours with P90 22.44 hours among eligible paired crossings.
- Detector: 44 new false-alert events in 1,515 labeled-normal site-hours. The 13 episode overlaps include three episodes already alerting before onset.
- The evaluator starts its disclosed no-future-refill counterfactual from measured storage; it does not establish independent physical truth or validate the declared sensor-error bound.

See [evaluation](EVALUATION.md), [evaluator](../scripts/backtest_reserve.py) and [domain implementation](../backend/app/domain.py). A warning that is frequently too early may cause unnecessary inspections or deliveries. No reduction in caretaker effort or water use is established.

**UI defect found during the review:** `IncidentProgress` in `frontend/src/App.tsx` checked all historical actions for approval instead of matching the current incident. In-memory reproduction: approve a pre-incident notice, introduce excess usage and open a new incident. The backend incident was OPEN without an approved action; the old notice had `incident_id: null`, yet the UI predicate marked “Request approved” complete. Backend approval remained correctly bound to its incident.

**Publication follow-up, October 11:** the user authorized pushing to `Pradhyut21/jalrakshak`. Before publication, corrected the indicator to require the current incident ID and added the existing backend field to the frontend Action type. Production build and type checking pass. Five focused Chromium/HTTP checks observe no incident, an old pre-incident approval, a newly opened incident, a pending current proposal and a correctly approved current incident. The first two check attempts exposed test assertion assumptions about class whitespace and an absent optional key; those assertions were corrected, and the passing report is `artifacts/incident-progress-verification.json`. Earlier failed reports remain in the excluded local verification-history directory. No algorithm, approval authorization or incident-recovery behavior changed. The October 3 ZIP remains unchanged and does not contain this later Git-source correction.

Source publication subsequently succeeded on `main` at commit `eaa9dc76281c67228bc1237204f941ec652cc1e4`, verified against the remote Git ref and signed-out public access. The original history and development dates remain visible. The public-repository requirement is now addressed; this does not resolve the other eligibility, demonstration or submission gaps recorded at review time.

Fresh check command:

```powershell
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider backend/tests/test_domain.py backend/tests/test_evaluation.py backend/tests/test_reserve_backtest.py
```

Result: **41 passed in 58.25 seconds**. Checks cover domain arithmetic and gates, chronology, validation selection, full-horizon purging, metric calculations and exact reproduction of both packaged evaluation JSON reports. The evaluation script's file-writing entry point was not run. Earlier 186-test and 31-browser-check results are dated October 3; the complete suites, browser, fresh installation and live AWS were not rerun today.

## Priorities

1. Obtain a written organizer ruling on the actual early start. Do not treat a new commit as changing eligibility.
2. If accepted, establish demonstrable AWS use, truthful public source, qualifying account status, a concise recorded demo and an on-time submission receipt.
3. Use any already available authorized real logs and caretaker feedback honestly. Seven days of new readings cannot be collected before tonight's deadline; this remains a later evidence milestone if existing logs are unavailable.
4. Address the verified UI approval association and assess warning usefulness using new validation evidence, preserving the frozen holdout. Keep the scope narrow.

The project can become a stronger practical project through these steps. Current evidence supports potential, not a reliable selection probability. Existing ZIPs remain the October 3 application deliverables; this review does not refresh or replace their verification records.
