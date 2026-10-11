# JalRakshak solo submission draft

Prepared October 11, 2026. This is a reviewed draft, not a submission receipt. Copy the answers below only where the form accepts them; leave missing links blank rather than inventing URLs.

## Project title

JalRakshak — Act Before the Tank Reserve Runs Low

## Track

Heat and Water

## GitHub link

https://github.com/Pradhyut21/jalrakshak

## Deployed link

**Field instruction — do not paste this note:** leave the optional field blank. There is no verified accessible deployment.

## YouTube video demo link

**Required field still missing — do not paste a placeholder:** upload the [2:54 demo](media/JalRakshak-Demo.mp4) and enter its published or unlisted YouTube URL. The user explicitly confirmed on October 11 that it has not been uploaded. Use the [ready upload pack](YOUTUBE_UPLOAD.md); a GitHub MP4 URL cannot fill this field.

## What does your project do?

A hostel tank can still contain water when it is already time to arrange the next delivery. JalRakshak helps one caretaker turn timestamped tank readings, recorded arrivals and delivery lead time into a clear planning deadline before the reserve runs low.

The working local prototype separates reserve-crossing time from the latest time to arrange supply. It supports manual entries and CSV import, a delayed-delivery preview, sustained abnormal-depletion alerts, and an incident history. The caretaker reviews and explicitly approves an exact notice into a local inbox. Recovery requires three fresh normal post-intervention readings and adequate modeled planning margin. Missing or stale evidence stays UNKNOWN; observed forecasts require a declared reading-error bound and its basis.

React/TypeScript provides the interface; FastAPI/Pydantic runs deterministic calculations and SQLite stores local sessions. The repository links a recorded end-to-end demo and passing application-source CI. Evaluation is reproducible but entirely synthetic; caretaker usefulness, sensor accuracy and water savings remain unvalidated.

## How did you use AWS in your project?

AWS open source: I implemented an optional session repository using boto3, the AWS SDK for Python, to map the application's session state to DynamoDB. It uses consistent reads, conditional version updates and an atomic hourly creation quota; quota checks use an offline fake table.

AWS service integration source: a SAM template defines Amazon API Gateway HTTP API, AWS Lambda, Amazon DynamoDB and Amazon CloudWatch Logs. A Mangum handler adapts FastAPI for Lambda. Table-scoped IAM, API throttling, Lambda concurrency limits and seven-day log retention are explicit; cloud mode is restricted to simulated sessions.

The recorded demo runs on SQLite. Validation covers static source checks and offline quota tests; SAM CLI execution, Linux Lambda packaging and live AWS deployment have not been verified.

## Blog links

**Field instruction — do not paste this note:** leave the optional field blank. No AWS Builder Center blog has been published.

## Team leader's contributions

I am the sole builder and team lead. Using OpenAI Codex for AI-assisted coding and review, I owned the product scope and integration across the caretaker interface, forecast and incident workflow, local observed-data workspace, tests and reproducible synthetic evaluation. I also prepared the optional AWS integration source, documentation and 2:54 demo. Brag/HyperFrames created the video composition; Kokoro supplied synthetic narration, with dependencies and media credited. Development began October 1, before the event's October 8 start; original history is preserved and no organizer exception has been obtained.

## Feedback: what could be better about the AWS services?

My feedback concerns SDK integration and deployment documentation, rather than deployed service performance. DynamoDB TTL is asynchronous, so the application must enforce exact session expiry itself. The repository checks expiry on reads and in conditional updates. I would value a boto3 reference example combining TTL, optimistic concurrency and a shared quota for temporary sessions.

For AWS SAM and Lambda, a concise Windows-to-Linux packaging checklist that distinguishes source checks, container builds and deployed smoke tests would improve onboarding. A working Windows application does not prove Lambda compatibility. I have not evaluated AWS runtime reliability or billing.

## What did you like about the AWS services?

Boto3 provides a clear SDK boundary for the optional DynamoDB repository, alongside the local SQLite repository. DynamoDB conditional expressions fit versioned session updates that preserve incident state and the atomic session-creation quota.

The SAM template makes the DynamoDB table, API Gateway routes, Lambda configuration, table-scoped IAM policy and CloudWatch log retention reviewable in one place. That helped keep permissions and intended resource limits explicit. These are SDK and architecture benefits observed in source work; live service behavior remains untested.

## Readiness and primary sources

- The public repository and [174-second video](media/JalRakshak-Demo.mp4) exist. YouTube upload and event submission have not occurred. No deployment or blog link exists.
- [The event overview](https://www.wemakedevs.org/aws/env) names Heat and Water as the relevant track and permits AWS open-source tools or AWS deployment. The acceptability of this optional SDK integration is an organizer decision, not a verified eligibility result.
- [The rules](https://www.wemakedevs.org/aws/env/rules) exclude projects started before the event, require the video to show AWS use, allow disclosed AI coding tools, and require a public/unlisted YouTube demo. This October 1 build does not satisfy the published start rule without an explicit organizer exception.
- [The organizer's October 6 announcement](https://www.wemakedevs.org/blogs/what-is-happening-in-delhi-on-10-october) states October 11, 8 PM IST as the submission deadline. That time had passed when this draft was prepared. The [schedule](https://www.wemakedevs.org/aws/env/schedule) still leaves the exact deadline unspecified; no public extension was found. The signed-out submission page requires sign-in, so form closure has not been observed.
- AWS factual references: [boto3](https://github.com/boto/boto3), [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html), [conditional expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html), [SAM container build](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-build.html).

See [deployment limits](DEPLOYMENT.md), [evaluation](EVALUATION.md), [video evidence](DEMO_VIDEO.md), and [active checkpoint](PROJECT_STATE.md). Three separate AI agents in Codex reviewed this draft. Their two-round critique and ratings are recorded in [the review record](SUBMISSION_REVIEW.md); they assess the draft and do not represent different AI vendors, official judges or selection odds.
