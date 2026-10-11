# Submission draft: two-round AI review

Reviewed October 11, 2026. The user requested multiple AI critiques, ratings and a refinement loop. Three separate review agents in Codex examined the actual project evidence and [submission draft](SUBMISSION_DRAFT.md), then reviewed the revised draft and [YouTube upload pack](YOUTUBE_UPLOAD.md). They are separate perspectives within Codex, not different AI vendors or official judges. Ratings are subjective editorial assessments, not selection probabilities.

## Review ownership and evidence

| Reviewer | Independent scope |
|---|---|
| `form_aws_audit` | boto3 adapter, SAM resource definitions, Lambda handler, fake-table quota tests and truthful AWS feedback |
| `form_judge_review` | Caretaker problem, useful differentiator, solo contributions, evidence strength and pitch usability |
| `form_rules_review` | Current official track, solo participation, submission rules, dates, deadline, AWS criterion and signed-out submission route |

The integrator alone edited the documents. Reviewers were asked to identify factual errors, distinguish draft quality from project evidence and assign honest ratings. They were not instructed to reach a target score. No application files, thresholds, dependencies or evaluation numbers changed.

## Round 1: critique and changes

- **AWS reviewer:** no factual AWS/contribution errors; change “versioned incident updates” to “versioned session updates that preserve incident state,” because the DynamoDB item stores the whole session. Reduce repeated execution caveats while keeping a clear source/offline/live boundary.
- **Pitch reviewer:** retain the supply lead-time opening and full approval/recovery loop; group solo deliverables, shorten the AWS answer and label missing-link instructions so they are not copied into the form. Disclose separate Codex agents accurately. Keep synthetic evaluation out of an unsupported accuracy headline.
- **Rules reviewer:** retain Heat and Water, solo membership and disclosed AI tools; describe the schedule as leaving the precise deadline unspecified. The reviewer provisionally questioned the upload-confirmation sentence; the integrator confirmed the actual user reply, “Not uploaded yet.” The October 1 disclosure and published-deadline issue remain.

The revision applied these changes and added the distinction between reserve-crossing time and the latest time to arrange supply, plus a concise link to actual source CI and the recorded demo.

## Ratings

Each criterion uses a subjective 1–10 scale. The mean gives equal weight to clarity, product specificity, evidence honesty, AWS precision and submission usability. It evaluates the text, including its handling of missing fields.

| Reviewer and round | Clarity | Product specificity | Evidence honesty | AWS precision | Submission usability | Mean |
|---|---:|---:|---:|---:|---:|---:|
| AWS audit, round 1 | 8.5 | 9 | 9.5 | 9 | 8 | 8.8 |
| Pitch review, round 1 | 8 | 9 | 9 | 9 | 7 | 8.4 |
| Rules review, round 1 | 9 | 9 | 9 | 9 | 8 | 8.8 |
| AWS audit, round 2 | 9 | 9 | 9.5 | 9.5 | 8.5 | 9.1 |
| Pitch review, round 2 | 9 | 9 | 9 | 9 | 8 | 8.8 |
| Rules review, round 2 | 9 | 9 | 9 | 9 | 9 | 9.0 |

The unrounded average across reviewers improved from 8.67 to 8.97, displayed as **8.7 → 9.0/10**. This is an editorial comparison of two drafts, not a validated scoring system.

## Round 2 outcome and unchanged project gaps

All three reviewers passed the revised draft and upload pack with no remaining must-fix wording. The pitch reviewer required the review-record link to exist before publication; this file satisfies that document dependency.

Separate evidence assessments did **not** rise because of improved prose:

- AWS reviewer: AWS evidence adequacy **3/10**; implemented source and offline checks exist, but live AWS execution and a demonstrated AWS-tool runtime remain unverified.
- Pitch reviewer: demonstrated local-product evidence **7.5/10** and real-world readiness **3/10**; no real tank log or caretaker usefulness study exists.
- Rules reviewer: formal readiness is **incomplete and not demonstrably eligible**. The required YouTube URL is missing. October 1 development conflicts with the published October 8 start rule absent an actual exception. The organizer's published October 11, 8 PM IST deadline had passed, with no public extension found. Acceptance of this particular offline SDK integration is unconfirmed.

Optional deployment and blog fields remain blank. No event submission, YouTube publication, blog publication, organizer message or AWS deployment was performed. Stronger wording cannot establish those missing facts.

## References and observed boundaries

Project sources: [DynamoDB repository](../backend/app/repository.py), [Lambda handler](../backend/app/main.py), [SAM template](../infra/template.yaml), [offline quota tests](../backend/tests/test_session_limits.py), [deployment limits](DEPLOYMENT.md), [README evidence](../README.md), and [video provenance](DEMO_VIDEO.md).

Official references: [event overview and Heat and Water track](https://www.wemakedevs.org/aws/env), [rules](https://www.wemakedevs.org/aws/env/rules), [schedule](https://www.wemakedevs.org/aws/env/schedule), [October 6 organizer announcement with deadline](https://www.wemakedevs.org/blogs/what-is-happening-in-delhi-on-10-october), [boto3](https://github.com/boto/boto3), [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html), and [conditional expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html).

The rules reviewer inspected the public submission route in signed-out Chromium and observed “Sign in to submit.” This establishes an account requirement; it does not establish whether the authenticated form remains open. Current public sources do not supply an organizer exception or extension for this project.
