# Verify the application archive

The app ZIP extracts directly into its root, containing README, source, locks, built interface, tests, evidence and AI_HANDOFF. PACKAGE_STATUS states the actual stage. PACKAGE_FILES records every other payload file's path, byte length and SHA-256.

Run `python scripts/verify_archive.py <zip-path>` to check path safety, unique entries, manifest coverage, hashes and ZIP CRC. The adjacent .sha256 and verification JSON describe the ZIP bytes; they are integrity evidence, not digital signatures.

This package excludes reference checkouts, Git internals, installed dependencies, SQLite/session data, environment secrets and nested archives. docs/licenses includes complete observed direct-dependency texts; installed dependency licenses are also documented in the inventory. See THIRD_PARTY_NOTICES for its scope and gaps.

A fresh extraction was installed with a new virtual environment and npm ci, rebuilt and tested on Windows. The source under test passed57 backend tests and12 Chromium workflow/mobile/error checks. artifacts/portable-install-verification.json records the tested preliminary archive hash and verified source hashes. The final archive adds the updated verification/checkpoint documents; its app-source and lock hashes are unchanged. An integrity check alone does not establish runtime behavior or cloud deployment.

The older SAANS-JalRakshak-Preparation-2026-10-01.zip is a separate historical artifact. Use JalRakshak-App-2026-10-02.zip for the current application.
