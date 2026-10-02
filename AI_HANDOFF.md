# Continue JalRakshak without losing context

Read AGENTS.md, docs/PROJECT_STATE.md and PACKAGE_STATUS.json first. The user authorized original implementation in this folder and asked to repair the independent review. Continue existing code; do not restart or copy restricted winner repositories.

The product has an isolated simulated demo and a local SQLite workspace for operator-entered logs. Forecast facts are deterministic. A model must never approve actions, fabricate readings or resolve incidents.

The forecast now uses historical local-hour medians, observed 90th-percentile demand bounds and a recent upper-rate floor. Its parameters were frozen using validation only. Read docs/EVALUATION.md before interpreting results: original 48-hour holdout improved, but stress lateness, early warnings and detector false alerts remain.

Incident lifecycle comes from stored intervention, approval and verification facts; UNKNOWN is a data-quality view. Ingestion, configuration, import and approval are transactional. Read docs/API_CONTRACT.md and docs/ARCHITECTURE.md before changing shared contracts. Run relevant tests and update the checkpoint and archive after changes.

Real logs can be entered locally; none has been supplied or field-validated. Cloud mode remains demo-only. AWS infrastructure is unverified. Notices remain local receipts; the assistant is deterministic. No actual caretaker interview, sensor connection, water saving, external notification or award is proven.

Use docs/CONTINUE_PROMPTS.md for staged follow-ups and REVIEW_THIS_PROJECT.md for independent assessment. Reviews must not be instructed to inflate ratings. Historical prep stays in the full-context archive and workspace, outside the lean app bundle.
