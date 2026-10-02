"""Create a portable source + built-UI archive with a complete SHA-256 manifest."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"README.md", "AGENTS.md", "AI_HANDOFF.md", "START_HERE.md", "START_APP.cmd", "REVIEW_THIS_PROJECT.md", "PACKAGE_VERIFY.md", "THIRD_PARTY_NOTICES.md", "LICENSE", ".gitignore", ".gitattributes", ".env.example", "PACKAGE_STATUS.json"}
PREFIXES = {"backend", "frontend", "docs", "infra", "scripts", "artifacts", "prep", ".github"}
EXCLUDED = {"node_modules", "runtime", "__pycache__", ".pytest_cache", ".venv", ".aws-sam"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected_files():
    result = []
    for folder, directories, filenames in os.walk(ROOT):
        directories[:] = [name for name in directories if name not in EXCLUDED and (Path(folder) != ROOT or name in PREFIXES)]
        for filename in filenames:
            path = Path(folder) / filename
            relative = path.relative_to(ROOT)
            if len(relative.parts) == 1 and relative.name not in ROOT_FILES:
                continue
            if relative.name.startswith(".env") and relative.name != ".env.example":
                continue
            if path.suffix in {".pyc", ".db", ".sqlite", ".sqlite3", ".zip", ".log"}:
                continue
            if path.is_symlink():
                raise RuntimeError(f"Do not archive symlinks: {relative}")
            result.append(path)
    return sorted(result, key=lambda path: path.relative_to(ROOT).as_posix())


def main():
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise SystemExit("Build the frontend before packaging.")
    if json.loads((ROOT / "PACKAGE_STATUS.json").read_text(encoding="utf-8-sig"))["package_kind"] != "WORKING_LOCAL_SIMULATED_PROTOTYPE":
        raise SystemExit("Update actual package status before packaging.")
    files = selected_files()
    manifest = {"schema_version": 2, "hash_algorithm": "SHA-256", "scope": "Every archive entry except this manifest", "files": []}
    for path in files:
        data = path.read_bytes()
        manifest["files"].append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": digest(data)})
    encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (ROOT / "PACKAGE_FILES.json").write_bytes(encoded)
    destination = ROOT / "deliverables/JalRakshak-App-2026-10-02.zip"
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("PACKAGE_FILES.json", encoded)
    from verify_archive import verify
    result = verify(destination)
    result.update(archive=destination.name, archive_bytes=destination.stat().st_size, archive_sha256=digest(destination.read_bytes()))
    destination.with_suffix(".sha256").write_text(f"{result['archive_sha256']}  {destination.name}\n", encoding="utf-8")
    (destination.parent / "JalRakshak-App-2026-10-02-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
