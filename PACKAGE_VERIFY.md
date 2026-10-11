# Verify this application archive

The lean version 0.2.2 ZIP contains source, locked dependencies, built interface, tests, current evaluation, three product screenshots and active context. Historical prep/prompts and all screenshots are separately available through `scripts/package.py --full-context`. Required legal notices stay in both bundles.

PACKAGE_FILES.json hashes every other payload path and byte length. Run:

```text
python scripts/verify_archive.py <zip-path>
```

This checks safe paths, unique entries, complete manifest coverage, payload SHA-256 and ZIP CRC. Adjacent .sha256 and verification JSON describe the ZIP; these are integrity evidence, not signatures. Runtime databases, credentials, installed dependencies, reference checkouts and Git internals are excluded.

See artifacts/verification.json for current runtime/build/source hashes and the adjacent delivered-ZIP report for integrity. `artifacts/portable-install-verification.json` is the historical v0.2.1 fresh installation; it does not validate changed v0.2.2 application bytes. Dependency versions are unchanged, but no new fresh installation is claimed for this disclosure patch. The delivered v0.2.2 ZIP's app/build/lock hashes are checked against the current tested workspace. Domain and both evaluation artifacts are also compared directly to v0.2.1.

Use **JalRakshak-App-v0.2.2-2026-10-03.zip** for app review. Package names come from PACKAGE_STATUS.json's explicit version/date. Older application/preparation ZIPs are historical. Adjacent verification JSON describes the delivered archive. Local runtime checks do not verify AWS, sensor accuracy, alert-fatigue reduction or caretaker usefulness.
