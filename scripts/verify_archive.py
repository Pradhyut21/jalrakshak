"""Read-only verification of archive paths, manifest coverage and content hashes."""
import hashlib
import json
from pathlib import PurePosixPath
import sys
import zipfile


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entries")
        for name in names:
            parsed = PurePosixPath(name)
            if parsed.is_absolute() or ".." in parsed.parts or "\\" in name or ":" in name:
                raise ValueError(f"Unsafe archive path: {name}")
            if any(part in {"node_modules", ".venv", "runtime", ".git", "__pycache__"} for part in parsed.parts):
                raise ValueError(f"Excluded runtime/dependency state: {name}")
        manifest = json.loads(archive.read("PACKAGE_FILES.json"))
        expected = {row["path"] for row in manifest["files"]}
        if expected != set(names) - {"PACKAGE_FILES.json"}:
            raise ValueError("Manifest does not cover exactly the archived files")
        for row in manifest["files"]:
            data = archive.read(row["path"])
            if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"Hash/size mismatch: {row['path']}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
    return {"status": "PASS", "manifest_entries": len(expected), "archive_entries": len(names), "paths": "safe", "hashes": "match", "secrets_and_session_state": "excluded_by_allowlist_not_a_content_audit"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/verify_archive.py <zip>")
    print(json.dumps(verify(sys.argv[1]), indent=2))
