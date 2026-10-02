# Active implementation brief

Updated October 2, 2026. The earlier proposal is in prep/PROJECT_BRIEF.md.

One hostel caretaker manages one tank. The decision is when to request additional supply and inspect abnormal depletion before crossing the reserve. The fictional sample tank has 50,000 L capacity, 5,000 L reserve, 14-hour supply lead time and 3-hour buffer. These are demonstration assumptions, not measured campus parameters.

Implemented scope: operations dashboard, forecast/scenario view, incident timeline, local notice inbox, synthetic evaluation and deterministic evidence assistant. Supported readings are simulated; real-site collection and production authentication remain future work.

Recent demand uses the last usable measurement interval, accounting for arrived inflow once; this one-interval window was selected on synthetic validation MAE and frozen before final reporting, and is exactly the last-rate baseline. Earlier median demand excluding the last four hours is the anomaly baseline. Three consecutive intervals over 1.5 times that baseline open an abnormal-depletion incident. Aggregate data cannot locate a physical leak.

Forecasts start at the latest measured volume/time, run 48 hours, cap storage and track overflow/unmet demand separately. Central and optimistic paths conditionally include planned supply. The conservative path excludes unarrived supply and uses 20% higher demand. This is sensitivity analysis, not calibrated uncertainty. Reserve breach and physical emptiness are separate. Action deadline equals conservative reserve breach minus lead time and buffer. Missing, stale or conflicting evidence returns UNKNOWN.

Explicit approval binds session, action, evidence revision and expiry. It atomically records a receipt in the current session's local inbox; no external message or booking occurs. Repairs are claims. Verification requires three fresh post-intervention readings, normal interval depletion and adequate planning margin.

Tech: React/TypeScript/Vite, original SVG, FastAPI/Pydantic, atomic SQLite sessions, optional DynamoDB repository and SAM Lambda/API Gateway source. Each browser's state persists across local restart and expires after 24 hours. Local use needs no model credentials or paid services.

Acceptance: launch from the documented command, replay normal → excess → propose/approve → repair → delivery → verified recovery, observe truthful error/unknown behavior, reproduce tests and synthetic evaluation. Check the active checkpoint for actual evidence. Caretaker validation, sensor calibration, cloud hosting and authorized external transport are subsequent milestones.

Avoid expanding into cities, payment flows, leak localization, pump automation or unneeded deep learning. Strengthen the demonstrated workflow first. Reviews and awards depend on evidence; no score is promised.
