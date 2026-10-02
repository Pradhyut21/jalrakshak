"""Inventory installed dependency metadata and preserve direct-dependency notices.

Run with the application's Python environment. No registry/network requests or
dependency installation occur. Metadata evidence is not a blanket legal opinion.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import sys

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


LICENSE_FILENAME = re.compile(r"(?:licen[sc]e|notice|copying|copyright)", re.I)
PYTHON_ROOT_FILES = {
    "runtime": "backend/requirements.txt",
    "development": "backend/requirements-dev.txt",
    "infrastructure_validation": "infra/requirements-validation.txt",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def requirements_from(path: Path) -> list[Requirement]:
    if not path.exists():
        return []
    output = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "-")):
            output.append(Requirement(line))
    return output


def text_license_hint(text: str) -> str | None:
    if "ISC License" in text:
        return "ISC; preserve complete text including any bundled notices"
    if "Apache License" in text and "Version 2.0" in text:
        return "Apache-2.0 text observed"
    if "MIT License" in text or "Permission is hereby granted, free of charge" in text:
        return "MIT-style text observed"
    if "Mozilla Public License" in text:
        return "Mozilla Public License text observed"
    return None


def copy_notice(root: Path, ecosystem: str, name: str, version: str,
                source_name: str, data: bytes) -> str:
    destination = root / "docs" / "licenses" / f"{ecosystem}-{safe_name(name)}-{safe_name(version)}"
    destination.mkdir(parents=True, exist_ok=True)
    # Path separators become part of the filename, preserving duplicate basename notices.
    target = destination / safe_name(source_name)
    target.write_bytes(data)
    return target.relative_to(root).as_posix()


def python_inventory(root: Path) -> dict:
    roles: dict[str, set[str]] = defaultdict(set)
    direct: dict[str, set[str]] = defaultdict(set)
    roots: dict[str, list[Requirement]] = {
        role: requirements_from(root / path) for role, path in PYTHON_ROOT_FILES.items()
    }
    declared = {}
    missing = []
    edges = []
    visited: set[tuple[str, str, tuple[str, ...]]] = set()
    queue = deque()
    for role, requirements in roots.items():
        for requirement in requirements:
            name = canonicalize_name(requirement.name)
            direct[name].add(role)
            declared[name] = str(requirement)
            queue.append((requirement, role))
    while queue:
        requirement, role = queue.popleft()
        name = canonicalize_name(requirement.name)
        extras = tuple(sorted(requirement.extras))
        key = (name, role, extras)
        if key in visited:
            continue
        visited.add(key)
        roles[name].add(role)
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            missing.append({"name": name, "role": role, "requirement": str(requirement)})
            continue
        for raw in distribution.requires or []:
            child = Requirement(raw)
            if child.marker and not any(child.marker.evaluate({"extra": extra}) for extra in ("", *extras)):
                continue
            edges.append({"from": name, "to": canonicalize_name(child.name), "requirement": raw, "role": role})
            queue.append((child, role))

    lock = root / "backend" / "requirements-lock.txt"
    locked_requirements = {
        canonicalize_name(requirement.name): str(requirement)
        for requirement in requirements_from(lock)
    }
    locked_names = set(locked_requirements)
    for name in locked_names - roles.keys():
        roles[name].add("locked_unmapped")

    packages = []
    for name in sorted(roles):
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            if name in locked_requirements and not any(item["name"] == name for item in missing):
                missing.append({"name": name, "role": "locked", "requirement": locked_requirements[name]})
            continue
        item = {
            "name": distribution.metadata.get("Name", name),
            "canonical_name": name,
            "installed_version": distribution.version,
            "roles": sorted(roles[name]),
            "direct_roles": sorted(direct[name]),
            "declared_requirement": declared.get(name),
            "installed_matches_direct_requirement": None,
            "locked_requirement": locked_requirements.get(name),
            "installed_matches_lock": None,
            "license_expression": distribution.metadata.get("License-Expression"),
            "license_field": distribution.metadata.get("License"),
            "license_classifiers": [c for c in distribution.metadata.get_all("Classifier", []) if c.startswith("License ::")],
            "project_urls": distribution.metadata.get_all("Project-URL", []),
            "license_files": [],
        }
        if name in declared:
            item["installed_matches_direct_requirement"] = distribution.version in Requirement(declared[name]).specifier
        if name in locked_requirements:
            item["installed_matches_lock"] = distribution.version in Requirement(locked_requirements[name]).specifier
        for path in distribution.files or []:
            if not LICENSE_FILENAME.search(path.name):
                continue
            actual = distribution.locate_file(path)
            if not actual.is_file():
                continue
            data = actual.read_bytes()
            evidence = {"distribution_path": str(path).replace("\\", "/"), "bytes": len(data), "sha256": digest(data)}
            hint = text_license_hint(data.decode("utf-8", errors="replace"))
            if hint:
                evidence["text_hint"] = hint
            if direct[name]:
                evidence["included_notice"] = copy_notice(root, "python", name, distribution.version, str(path), data)
            item["license_files"].append(evidence)
        item["evidence_status"] = "TEXT_AND_METADATA" if item["license_files"] and (item["license_expression"] or item["license_field"] or item["license_classifiers"]) else (
            "TEXT_ONLY" if item["license_files"] else ("METADATA_ONLY" if item["license_expression"] or item["license_field"] or item["license_classifiers"] else "UNRESOLVED")
        )
        packages.append(item)
    return {
        "source_requirements": PYTHON_ROOT_FILES,
        "observed_lockfile": lock.relative_to(root).as_posix() if lock.is_file() else None,
        "lockfile_sha256": digest(lock.read_bytes()) if lock.is_file() else None,
        "packages": packages,
        "active_dependency_edges": edges,
        "missing_dependencies": missing,
        "marker_environment": "Current interpreter and platform; optional extras only when declared. Not a Linux Lambda inventory.",
    }


def node_inventory(root: Path) -> dict:
    frontend = root / "frontend"
    manifest = json.loads((frontend / "package.json").read_text(encoding="utf-8-sig"))
    lock_path = frontend / "package-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
    direct_runtime = set(manifest.get("dependencies", {}))
    direct_dev = set(manifest.get("devDependencies", {}))
    items, unobserved = [], []
    for package_path, locked in sorted(lock.get("packages", {}).items()):
        if not package_path:
            continue
        directory = frontend / package_path
        package_json = directory / "package.json"
        if not package_json.is_file():
            unobserved.append({"lock_path": package_path, "locked_version": locked.get("version"), "optional": locked.get("optional", False), "os": locked.get("os"), "cpu": locked.get("cpu")})
            continue
        package = json.loads(package_json.read_text(encoding="utf-8-sig"))
        name, version = package["name"], package["version"]
        at_manifest_root = package_path == f"node_modules/{name}"
        is_direct_runtime = at_manifest_root and name in direct_runtime
        is_direct_dev = at_manifest_root and name in direct_dev
        item = {
            "name": name, "installed_version": version,
            "lock_path": package_path, "locked_version": locked.get("version"),
            "installed_matches_lock": version == locked.get("version"),
            "direct_runtime": is_direct_runtime, "direct_development": is_direct_dev,
            "lock_development_flag": locked.get("dev", False),
            "optional": locked.get("optional", False),
            "license_field": package.get("license", package.get("licenses")),
            "license_in_lock": locked.get("license"),
            "repository": package.get("repository"),
            "resolved_archive": locked.get("resolved"),
            "integrity": locked.get("integrity"),
            "license_files": [],
        }
        # Published notices normally live at package root. Deep bundled notices are
        # represented when the package supplies a root ThirdPartyNotices/LICENSE.
        for actual in sorted(directory.iterdir()):
            if not actual.is_file() or not LICENSE_FILENAME.search(actual.name):
                continue
            data = actual.read_bytes()
            evidence = {"package_path": actual.relative_to(directory).as_posix(), "bytes": len(data), "sha256": digest(data)}
            if is_direct_runtime or is_direct_dev:
                evidence["included_notice"] = copy_notice(root, "npm", name, version, actual.name, data)
            item["license_files"].append(evidence)
        item["evidence_status"] = "TEXT_AND_METADATA" if item["license_files"] and item["license_field"] else (
            "TEXT_ONLY" if item["license_files"] else ("METADATA_ONLY" if item["license_field"] else "UNRESOLVED")
        )
        items.append(item)
    observed = {item["name"] for item in items if item["direct_runtime"] or item["direct_development"]}
    return {
        "manifest": "frontend/package.json", "lockfile": "frontend/package-lock.json",
        "lockfile_sha256": digest(lock_path.read_bytes()), "lockfile_version": lock.get("lockfileVersion"),
        "packages": items, "lock_entries_not_installed_here": unobserved,
        "missing_direct_dependencies": sorted((direct_runtime | direct_dev) - observed),
        "license_scan_scope": "Package-root license/notice files and package.json metadata; not an exhaustive bundled-code or browser-binary audit.",
    }


def build(root: Path) -> dict:
    python = python_inventory(root)
    node = node_inventory(root)
    gaps = []
    for ecosystem, packages in (("python", python["packages"]), ("npm", node["packages"])):
        for package in packages:
            if package["evidence_status"] in {"UNRESOLVED", "METADATA_ONLY"}:
                gaps.append({"ecosystem": ecosystem, "name": package["name"], "version": package["installed_version"], "status": package["evidence_status"]})
    return {
        "schema_version": 1,
        "generated_at_ist": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "inventory_kind": "OBSERVED_INSTALLED_DEPENDENCIES_NOT_LEGAL_CERTIFICATION",
        "python_version": platform.python_version(), "platform": platform.system(),
        "python_environment": "Run with the app's .venv interpreter; metadata is from that process, not inferred from requirements alone.",
        "python": python, "npm": node, "license_evidence_gaps": gaps,
        "not_used": ["Strands Agents SDK", "OpenAI API", "Bedrock model", "WNTR", "EPANET", "copied reference-project source"],
        "limits": [
            "Metadata and observed text are evidence, not a legal determination or security audit.",
            "Current Windows installation differs from Linux Lambda/native npm optional packages; audit the built Linux artifact separately.",
            "Unavailable npm optional/OS-specific lock entries are listed, not claimed installed or text-audited.",
            "Direct dependency license/notice files are copied verbatim; transitive file hashes/paths are recorded but their full texts are not all bundled here.",
            "Embedded third-party notices may cover additional bundled code; package-root scanning cannot certify every embedded asset or browser binary.",
        ],
    }


def write_notice_index(root: Path, result: dict) -> None:
    index = root / "docs" / "licenses" / "INDEX.md"
    lines = [
        "# Preserved installed-dependency notices", "",
        "Generated by `scripts/license_inventory.py` from the application's installed environment. Texts are copied verbatim; hashes and source paths are in [the inventory](../../artifacts/dependency-licenses.json).", "",
        "These are observed direct-dependency notices, including bundled notices supplied by their distributions. This is not an exhaustive license archive for every transitive package, browser binary or future Linux build.", "",
    ]
    for ecosystem in ("python", "npm"):
        lines.extend([f"## {ecosystem.upper()}", ""])
        for package in result[ecosystem]["packages"]:
            notices = [item["included_notice"] for item in package["license_files"] if item.get("included_notice")]
            if not notices:
                continue
            lines.append(f"- {package['name']} {package['installed_version']}:")
            for notice in notices:
                relative = Path(notice).relative_to("docs/licenses").as_posix()
                lines.append(f"  - [{Path(notice).name}]({relative})")
        lines.append("")
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "artifacts" / "dependency-licenses.json"
    result = build(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_notice_index(root, result)
    summary = {
        "inventory": output.relative_to(root).as_posix(),
        "python_packages": len(result["python"]["packages"]),
        "npm_installed_packages": len(result["npm"]["packages"]),
        "npm_unobserved_lock_entries": len(result["npm"]["lock_entries_not_installed_here"]),
        "license_evidence_gaps": result["license_evidence_gaps"],
        "python_missing": result["python"]["missing_dependencies"],
        "npm_missing_direct": result["npm"]["missing_direct_dependencies"],
        "version_mismatches": [
            {"ecosystem": ecosystem, "name": package["name"], "version": package["installed_version"]}
            for ecosystem, packages in (("python", result["python"]["packages"]), ("npm", result["npm"]["packages"]))
            for package in packages
            if package.get("installed_matches_lock") is False or package.get("installed_matches_direct_requirement") is False
        ],
    }
    print(json.dumps(summary, indent=2))
    return int(bool(summary["python_missing"] or summary["npm_missing_direct"] or summary["version_mismatches"]))


if __name__ == "__main__":
    sys.exit(main())
