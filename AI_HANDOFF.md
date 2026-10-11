# Continue JalRakshak without losing context

Read AGENTS.md, docs/PROJECT_STATE.md and PACKAGE_STATUS.json first. The user authorized original implementation in this folder and asked to repair the independent review. Continue existing code; do not restart or copy restricted winner repositories.

The product has an isolated simulated demo and a local SQLite workspace for operator-entered logs. Forecast facts are deterministic. A model must never approve actions, fabricate readings or resolve incidents.

The forecast now uses historical local-hour medians, observed 90th-percentile demand bounds and a recent upper-rate floor. Its parameters were frozen using validation only. Read docs/EVALUATION.md before interpreting results: original 48-hour holdout improved, but stress lateness, early warnings and detector false alerts remain.

Version 0.2.1 follows the October 3 re-review: observed settings require a positive numeric reading-error bound and documented basis, without a default. Old observed sessions remain UNKNOWN until redeclared, preserving records. The shared declaration gate covers previews, assistant and approvals. Bound/basis/timestamp persist into site backups; local notices carry the assumptions. Declared accuracy remains unverified. Do not estimate a safety bound from a single log, copy the simulator bound into real defaults, or retune the detector on reporting data.

Version 0.2.2 adds only a nonblocking warning strictly below 0.5% capacity, labeled as a review heuristic. It reaches settings, observed analysis, previews, assistant and new local notices without changing any bound, forecast or approval rule. Domain and evaluation files remain byte-identical to v0.2.1. The user now explicitly requested stopping feature expansion: obtain an authorized real log, datasheet and caretaker feedback next. The v0.2.1 fresh-install report is historical; do not present it as a fresh v0.2.2 install.

Incident lifecycle comes from stored intervention, approval and verification facts; UNKNOWN is a data-quality view. Ingestion, configuration, import and approval are transactional. Read docs/API_CONTRACT.md and docs/ARCHITECTURE.md before changing shared contracts. Run relevant tests and update the checkpoint and archive after changes.

Real logs can be entered locally; none has been supplied or field-validated. Cloud mode remains demo-only. AWS infrastructure is unverified. Notices remain local receipts; the assistant is deterministic. No actual caretaker interview, sensor connection, water saving, external notification or award is proven.

Use docs/CONTINUE_PROMPTS.md for staged follow-ups and REVIEW_THIS_PROJECT.md for independent assessment. Reviews must not be instructed to inflate ratings. Historical prep stays in the full-context archive and workspace, outside the lean app bundle.
