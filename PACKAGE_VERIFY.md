# Verify this application archive

The lean version0.2 ZIP contains source, locked dependencies, built interface, tests, current evaluation, three product screenshots and active context. Historical prep/prompts and all screenshots are separately available through `scripts/package.py --full-context`. Required legal notices stay in both bundles.

PACKAGE_FILES.json hashes every other payload path and byte length. Run:

```text
python scripts/verify_archive.py <zip-path>
```

This checks safe paths, unique entries, complete manifest coverage, payload SHA-256 and ZIP CRC. Adjacent .sha256 and verification JSON describe the ZIP; these are integrity evidence, not signatures. Runtime databases, credentials, installed dependencies, reference checkouts and Git internals are excluded.

See artifacts/verification.json for current runtime checks and artifacts/portable-install-verification.json for the tested extraction. Version0.1 checks cannot prove the changed version0.2 source. Final documentation updates may change ZIP bytes after an installation check; app-source and lock hashes must match the extracted source under test.

Use **JalRakshak-App-v0.2-2026-10-02.zip** for app review. The old application/preparation ZIPs are historical. A successful local installation does not verify AWS, field accuracy or caretaker usefulness.
