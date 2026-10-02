# Environmental Hacks: verified rules and project-selection evidence

Checked on **1 October 2026, Asia/Kolkata**. This is a preparation/research document. It does not contain submission implementation. Recheck the official pages at kickoff and before submission.

## Official rules: source facts

The [tour rulebook](https://www.wemakedevs.org/aws/env/rules), updated 16 September 2026, establishes:

- Participants must be university students in India, aged 18 or older; teams contain 1–4 eligible people. Each member registers independently; one team per person, one submission per team.
- A WeMakeDevs account and verified AWS Builder Center enrollment are required. An unresolved SheerID case permits entry and judging while verification is resolved; rewards and interview eligibility still depend on verification.
- Learning, planning and practice before kickoff are permitted. Submission project work must start when the event opens. A project begun earlier is ineligible even if rewritten; repository history inconsistent with event dates can disqualify the team.
- Libraries, public APIs, boilerplate and starter templates are permitted; judging covers event additions. Credit third-party work and respect its licence.
- AWS use must appear in the demo. AI coding tools are allowed and must be named in the writeup.
- Submit a public repository, short problem/build/AWS writeup, and public or unlisted YouTube recording **under three minutes**; test signed-out access. No live judging call; video-visible functionality counts.
- Submission closes strictly at the announced deadline. Interview consideration is separate from prizes, limited to eligible 2027/2028 graduates, with at most ten opportunities and no guaranteed interview or employment.

## Event and prize facts

The [Environmental Hacks overview](https://www.wemakedevs.org/aws/env) specifies **8–11 October 2026**, online across India, with an optional DTU Delhi build day on **10 October, 08:00–20:00**. Participation location does not affect judging. First Commit participants may enter again, but must check in for this event.

There are three problem tracks: **Air**, **Heat and Water**, and **Waste and Energy**. Each has one winner receiving **₹2,00,000 cash + $2,000 AWS credits**. Four runners-up across tracks receive **$1,000 AWS credits per team**. Five blog authors receive AirPods; publish the build story on AWS Builder Center and link it in the submission.

For prize eligibility, the overview accepts **at least one AWS open-source tool OR deployment on AWS**. Local AWS-tool projects and deployed projects are both valid; Build It/Ship It describe build approaches, not separate Environmental Hacks prize tracks. There is no published requirement to use Bedrock, an LLM, multiple AWS services, or paid infrastructure.

Published judging categories are **Idea and Impact**, **Built on AWS**, **Design and usability**, **Execution**, and **Demo video**. No numerical weighting is published. The emphasis is a specific environmental problem, an understandable product, and a working result.

## Timing conflict: preserve the uncertainty

| Source checked 1 October | What it currently says | How to use it |
|---|---|---|
| [Official Environmental Hacks schedule](https://www.wemakedevs.org/aws/env/schedule) | Kickoff is Thursday 8 October; submission day is Sunday 11 October. Exact kickoff/session/deadline hours are still being finalised and will appear there first. | The opening hour and definitive form cutoff remain unconfirmed on the designated schedule page. |
| [Organizer-linked Delhi Luma event](https://luma.com/env) | Its Saturday agenda says online submissions remain open until **Sunday 11 October, 20:00 IST**. | Treat 20:00 IST as a published organizer hint and provisional deadline; do not claim the main schedule has confirmed it. |

**Planning decision:** provisionally target submission by **18:00 IST on 11 October**, two hours before the Luma time. This is our buffer, not an official deadline. Recheck the schedule and actual submission form at kickoff and again on Sunday. If they announce an earlier cutoff, move the buffer earlier. Do not assume midnight or 23:59.

The opening time is also unresolved. Do not start implementation merely because the calendar changes to 8 October; wait for the organizer's actual opening/check-in notice or confirmed clock.

## What can be done during 1–7 October

**Authorized preparation:** read rules and reference repositories; interview potential users; choose scope; document decisions, architecture and acceptance criteria; prepare prompt sequences; verify data access manually; practise generic AWS workshops in a separate scratch area; verify account/student eligibility.

**Defer until the event clock opens:** submission-specific application scaffolding, source code, infrastructure templates, model training code, UI implementation and project fixtures. Keep preparation docs distinct from the submission source history. Do not rewrite history or fabricate event dates. A genuinely generic external starter is permitted by the rulebook, but custom SAANS/JalRakshak development before kickoff is not.

These boundaries are a conservative implementation of the explicit project-start rule, not a request for new approval. Existing preparation files should record their true dates.

## Previous First Commit recognition: verified list

The [official First Commit winners page](https://www.wemakedevs.org/aws/first-commit/projects) names:

| Award | Project |
|---|---|
| First prize / Ship It | Suraksha — An Agentic Companion for an aging parent |
| Second prize / Build It | Beacon Night Shift |
| Third prize / Best UI | CampusEvac |
| Runner-up | Magpie — AI-native finance workspace |
| Runner-up | FreshTrace |
| Runner-up | Expressive captions |
| Runner-up | Factcade — AI Operations Copilot for your Factories |

Beacon and CampusEvac are confirmed award recipients. **Fraud Risk Manager is absent from this winners/runners-up list.** That does not establish that it received no other recognition; it means we should not call it an official listed winner without another reliable source. The event was **First Commit**, not FinTech Hacks.

## Organizer guidance that affects strategy

The [29 September Environmental Hacks announcement](https://www.wemakedevs.org/blogs/announcing-environmental-hacks) describes a recurring failure: projects display environmental data without helping a person make a decision. Its examples include a principal deciding whether assembly moves indoors and a housing society deciding when to book water. It also asks teams to explain data meaning and freshness rather than treating hourly stations and satellite passes as interchangeable.

**Our inference:** define the person, decision, action, and evidence of completion before choosing advanced technology. A narrow complete workflow offers stronger execution evidence than a wide dashboard. This is strategic judgment, not an official score formula or a promise of winning.

## Water prior art: three primary sources

| Official source | Verified capability | Implication for JalRakshak positioning |
|---|---|---|
| [Flume Water](https://flumewater.com/) | Hardware-backed household usage monitoring, real-time flow, abnormal-usage/leak alerts, budgets and shared access. | Usage monitoring and leak alerts are established capabilities. Do not present either as a new invention. |
| [WINT](https://wint.ai/) | Commercial water-management platform using usage-pattern analysis, anomaly detection, alerts and automatic remote shutoff; facility and residential use cases. | Anomaly-to-action water operations already exist commercially. Our prototype must be specific about its target and limitations. |
| [US EPA EPANET](https://www.epa.gov/water-research/epanet) | Public-domain water-distribution modeling used for tank/pump operation, infrastructure design, water quality and emergency/resilience analysis. | Predictive water-system modeling is established. A four-day prototype need not implement a hydraulic network simulator to justify a tank inventory forecast. |

These sources establish prior art; they do **not** establish the absence of a particular competing tanker-planning product. We have not performed an exhaustive patent, market, or literature search.

**Defensible prototype claim:** a campus caretaker workflow combining stored-water reserve forecasting, configured supply lead time, a latest-action deadline, abnormal-usage evidence, human-approved notifications and subsequent state verification. The distinguishing work is that combined campus workflow and evidence, not the invention of water prediction or AI leak detection. Any environmental savings demonstrated only in scenarios must remain **simulated/projected**.

## SAANS data feasibility: verified documentation and manual access test

The [Open-Meteo Air Quality API documentation](https://open-meteo.com/en/docs/air-quality-api) says air-quality forecasts use CAMS models. The global atmospheric composition domain relevant to Delhi has approximately **45 km spatial resolution**, not the Europe-focused 11 km headline. It exposes PM2.5/PM10 and US/European AQI, not an Indian AQI field. API keys are required for its commercial customer resources; attribution to Open-Meteo and the underlying CAMS provider is required.

Therefore, model output returned for a coordinate is not a school sensor measurement. Do not label US AQI as Indian AQI, claim individual-school precision, or claim the least-polluted forecast hour is medically safe. An instantaneous PM2.5 value alone is insufficient grounds to label a number official Indian AQI. A SAANS prototype should visibly separate forecast/model output, measurements, school-configured policies, and any authority-issued directions.

A **manual, read-only request succeeded on 1 October 2026**:

[Delhi PM2.5/PM10/US-AQI query](https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.6139&longitude=77.2090&hourly=pm2_5,pm10,us_aqi&timezone=Asia%2FKolkata&forecast_days=2)

Observed response: 48 hourly rows; timezone `Asia/Kolkata`; first timestamp `2026-10-01T00:00`; returned grid coordinate approximately `28.599998, 77.20001`; first PM2.5 `109.2`, PM10 `438.7`, US AQI `159`. This proves access for that request only, not provider reliability, forecast accuracy, or future availability.

[OpenAQ's official authentication documentation](https://docs.openaq.org/using-the-api/api-key) requires an API key obtained through registration. Treat OpenAQ as an account-dependent integration. A web-tool attempt to open the [CPCB AQI portal](https://airquality.cpcb.gov.in/AQI_India/) failed in this environment; that does not prove the portal or all government APIs are unusable. Access and geographic coverage remain unverified here.

## Four-day choice: strategic judgment, not source facts

| Consideration | SAANS: school air decisions | JalRakshak: campus water operations |
|---|---|---|
| One-user focus | Principal reviewing one day's outdoor schedule | Caretaker reviewing one tank's reserve and next delivery |
| Minimal credible data | Forecast provider, freshness/scale labels, school policy; measured data optional | Manual tank readings, delivery logs, capacity/reserve and supply lead time; sensors optional |
| No external API guarantee | Captured provider response or clearly labelled synthetic scenario can preserve the demo | Manual inputs and seeded scenarios can preserve the demo without environmental APIs |
| Smallest complete loop | Review plan → approve → send notice → record schedule acknowledgment | Detect reserve risk → recommend → approve notice → record later reading/delivery → recompute risk |
| Verification limit | Moving assembly indoors changes the schedule; it does not prove indoor air is clean or health outcomes improved | A notification does not deliver water; a later logged reading/delivery changes the estimated reserve state |
| Largest avoidable risk | Misleading safety claims, AQI scale mix-ups, unvalidated custom ML, assuming indoor is clean | Simulated sensor claims, treating excess use as a confirmed leak, pretending a tanker was dispatched |
| Differentiating demonstration | Time-window choice and visual schedule before/after | Reserve/runout/action deadline moving after delayed supply and a logged intervention |

**Recommendation:** do not pivot automatically just because the attached strategy prefers water. Keep SAANS if the team has a school contact, a clear decision workflow, and enthusiasm for Air. Prefer JalRakshak if the team can get campus caretaker input and tank/delivery facts more easily. Neither requires custom ML or an LLM in the first working milestone. Both should begin with deterministic decisions, one real AWS path, visible provenance, and an honest demonstration. Choose one; do not combine both domains into a platform.

The organizer's school/tanker examples are public, so neither idea alone proves originality. Differentiation comes from user evidence, decisions that change behavior, implementation quality and the short recording.

## Remaining items to recheck

- Actual event opening time and confirmed submission form cutoff.
- Each member's eligibility, registration, check-in and verification state.
- Chosen AWS services/model availability in the team's account and region; available credits do not prove every service/model is accessible.
- Successful signed-out access to repository, deployed URL if supplied, video and writeup.
- Chosen data-provider licensing, coverage, freshness, rate limits and endpoint availability.
- Every public claim against actual code, evidence and video-visible behavior after implementation.
