#!/usr/bin/env python3
"""
tools/validate_manifests.py

Validates ELYos community TOML manifests located in:
  - community-system-modules/
  - community-modules/

Ensures required sections, fields, formats (SemVer, reverse-domain IDs),
and security constraints (immutable references, no self-assigned verification status).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Use Python 3.11+ tomllib, with fallback to tomli if ever available
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # Handled in parser


# --- Validation Regexes & Constants ---

# Semantic Versioning 2.0.0 specification regex
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# Reverse-domain identifier regex (e.g., org.elyos.arch, com.developer.gaming-mod)
ID_REGEX = re.compile(r"^[a-z0-9]+(\.[a-z0-9_-]+)+$")

# URL validation regex (http, https, git protocols)
URL_REGEX = re.compile(r"^(https?|git)://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

SUPPORTED_REPO_TYPES = {"git"}

SUPPORTED_ARCHITECTURES = {
    "x86_64",
    "aarch64",
    "armv7",
    "armv8",
    "riscv64",
    "x86",
    "all",
}

VALID_STATUSES = {
    "official",
    "community-reviewed",
    "unverified",
    "problematic",
}

# Developers submitting community manifests are strictly forbidden from self-assigning these tiers
RESTRICTED_STATUSES = {
    "official",
    "community-reviewed",
}


class ValidationError:
    """Represents a single validation error with file and field attribution."""

    def __init__(self, file_path: str, field: str, message: str):
        self.file_path = file_path
        self.field = field
        self.message = message

    def __str__(self) -> str:
        return f"[{self.file_path}] {self.field}: {self.message}"


def is_valid_semver(version: str) -> bool:
    """Check if version string matches SemVer 2.0.0."""
    return bool(SEMVER_REGEX.match(version.strip()))


def is_valid_module_id(module_id: str) -> bool:
    """Check if module id matches reverse-domain format."""
    return bool(ID_REGEX.match(module_id.strip()))


def is_valid_url(url: str) -> bool:
    """Check if repository URL is a valid http/https/git URL."""
    return bool(URL_REGEX.match(url.strip()))


def parse_toml(file_path: Path) -> Tuple[Dict[str, Any] | None, str | None]:
    """Parse a TOML file and return (data, error_message)."""
    if tomllib is None:
        return None, (
            "Python 'tomllib' is unavailable. Please run on Python 3.11+ "
            "or install 'tomli'."
        )

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        return data, None
    except Exception as exc:
        return None, f"TOML parse error: {exc}"


def validate_manifest(
    data: Dict[str, Any],
    file_path: Path,
    seen_ids: Dict[str, str],
    allow_privileged_status: bool = False,
) -> List[ValidationError]:
    """Validate a parsed manifest dictionary against ELYos specifications."""
    errors: List[ValidationError] = []
    path_str = str(file_path)

    # 1. Required Top-Level Sections
    required_sections = ["module", "repository", "compatibility", "metadata"]
    for section in required_sections:
        if section not in data:
            errors.append(
                ValidationError(
                    path_str, f"[{section}]", f"Missing required section '[{section}]'"
                )
            )
        elif not isinstance(data[section], dict):
            errors.append(
                ValidationError(
                    path_str,
                    f"[{section}]",
                    f"Section '[{section}]' must be a TOML table/dictionary",
                )
            )

    if errors:
        # Cannot proceed reliably without required tables
        return errors

    module_sec = data["module"]
    repo_sec = data["repository"]
    compat_sec = data["compatibility"]
    meta_sec = data["metadata"]

    # 2. Validate [module] section
    # Required fields: id, name, description, version
    mod_id = module_sec.get("id")
    if mod_id is None:
        errors.append(ValidationError(path_str, "module.id", "Missing required field 'id'"))
    elif not isinstance(mod_id, str) or not mod_id.strip():
        errors.append(
            ValidationError(path_str, "module.id", "Field 'id' must be a non-empty string")
        )
    else:
        mod_id = mod_id.strip()
        if not is_valid_module_id(mod_id):
            errors.append(
                ValidationError(
                    path_str,
                    "module.id",
                    f"Identifier '{mod_id}' is invalid. Must follow reverse-domain format (e.g. 'org.elyos.arch' or 'com.developer.module')",
                )
            )
        else:
            # Check for duplicate IDs across all manifests
            if mod_id in seen_ids and seen_ids[mod_id] != path_str:
                errors.append(
                    ValidationError(
                        path_str,
                        "module.id",
                        f"Duplicate module ID '{mod_id}' already registered in '{seen_ids[mod_id]}'",
                    )
                )
            else:
                seen_ids[mod_id] = path_str

    mod_name = module_sec.get("name")
    if mod_name is None:
        errors.append(ValidationError(path_str, "module.name", "Missing required field 'name'"))
    elif not isinstance(mod_name, str) or not mod_name.strip():
        errors.append(
            ValidationError(path_str, "module.name", "Field 'name' must be a non-empty string")
        )

    mod_desc = module_sec.get("description")
    if mod_desc is None:
        errors.append(
            ValidationError(path_str, "module.description", "Missing required field 'description'")
        )
    elif not isinstance(mod_desc, str) or not mod_desc.strip():
        errors.append(
            ValidationError(
                path_str,
                "module.description",
                "Field 'description' must be a non-empty string",
            )
        )

    mod_ver = module_sec.get("version")
    if mod_ver is None:
        errors.append(ValidationError(path_str, "module.version", "Missing required field 'version'"))
    elif not isinstance(mod_ver, str) or not mod_ver.strip():
        errors.append(
            ValidationError(
                path_str, "module.version", "Field 'version' must be a non-empty string"
            )
        )
    elif not is_valid_semver(mod_ver):
        errors.append(
            ValidationError(
                path_str,
                "module.version",
                f"Version '{mod_ver}' is not valid Semantic Versioning (SemVer 2.0.0, e.g. '1.0.0' or '0.1.0-alpha.1')",
            )
        )

    # 3. Validate [repository] section
    # Required fields: type, url
    repo_type = repo_sec.get("type")
    if repo_type is None:
        errors.append(
            ValidationError(path_str, "repository.type", "Missing required field 'type'")
        )
    elif not isinstance(repo_type, str) or not repo_type.strip():
        errors.append(
            ValidationError(
                path_str, "repository.type", "Field 'type' must be a non-empty string"
            )
        )
    elif repo_type.strip().lower() not in SUPPORTED_REPO_TYPES:
        errors.append(
            ValidationError(
                path_str,
                "repository.type",
                f"Repository type '{repo_type}' is unsupported. Allowed: {sorted(SUPPORTED_REPO_TYPES)}",
            )
        )

    repo_url = repo_sec.get("url")
    if repo_url is None:
        errors.append(
            ValidationError(path_str, "repository.url", "Missing required field 'url'")
        )
    elif not isinstance(repo_url, str) or not repo_url.strip():
        errors.append(
            ValidationError(
                path_str, "repository.url", "Field 'url' must be a non-empty string"
            )
        )
    elif not is_valid_url(repo_url):
        errors.append(
            ValidationError(
                path_str,
                "repository.url",
                f"Repository URL '{repo_url}' is invalid. Must begin with https://, http://, or git://",
            )
        )

    # Security rule: Git branch (such as main) is not an immutable release reference.
    # Releases must specify an immutable release tag or commit hash.
    repo_tag = repo_sec.get("tag")
    repo_commit = repo_sec.get("commit")
    repo_branch = repo_sec.get("branch")

    if not repo_tag and not repo_commit:
        if repo_branch:
            errors.append(
                ValidationError(
                    path_str,
                    "repository.tag",
                    f"A mutable branch reference ('{repo_branch}') alone is not allowed as an immutable release reference. Manifests must specify an immutable 'tag' or 'commit'.",
                )
            )
        else:
            errors.append(
                ValidationError(
                    path_str,
                    "repository.tag",
                    "Manifests must specify an immutable 'tag' or 'commit' reference for releases.",
                )
            )

    # 4. Validate [compatibility] section
    # Required fields: minimum_core_version, architecture
    min_core = compat_sec.get("minimum_core_version")
    if min_core is None:
        errors.append(
            ValidationError(
                path_str,
                "compatibility.minimum_core_version",
                "Missing required field 'minimum_core_version'",
            )
        )
    elif not isinstance(min_core, str) or not min_core.strip():
        errors.append(
            ValidationError(
                path_str,
                "compatibility.minimum_core_version",
                "Field 'minimum_core_version' must be a non-empty string",
            )
        )
    elif not is_valid_semver(min_core):
        errors.append(
            ValidationError(
                path_str,
                "compatibility.minimum_core_version",
                f"Version '{min_core}' is not valid Semantic Versioning (SemVer 2.0.0)",
            )
        )

    archs = compat_sec.get("architecture")
    if archs is None:
        errors.append(
            ValidationError(
                path_str,
                "compatibility.architecture",
                "Missing required field 'architecture'",
            )
        )
    elif not isinstance(archs, list) or len(archs) == 0:
        errors.append(
            ValidationError(
                path_str,
                "compatibility.architecture",
                "Field 'architecture' must be a non-empty list of supported architectures",
            )
        )
    else:
        for idx, a in enumerate(archs):
            if not isinstance(a, str) or not a.strip():
                errors.append(
                    ValidationError(
                        path_str,
                        f"compatibility.architecture[{idx}]",
                        "Architecture entries must be non-empty strings",
                    )
                )
            elif a.strip().lower() not in SUPPORTED_ARCHITECTURES:
                errors.append(
                    ValidationError(
                        path_str,
                        f"compatibility.architecture[{idx}]",
                        f"Unsupported architecture '{a}'. Allowed: {sorted(SUPPORTED_ARCHITECTURES)}",
                    )
                )

    # 5. Validate [metadata] section
    # Required fields: developer, license
    dev = meta_sec.get("developer")
    if dev is None:
        errors.append(
            ValidationError(path_str, "metadata.developer", "Missing required field 'developer'")
        )
    elif not isinstance(dev, str) or not dev.strip():
        errors.append(
            ValidationError(
                path_str, "metadata.developer", "Field 'developer' must be a non-empty string"
            )
        )

    lic = meta_sec.get("license")
    if lic is None:
        errors.append(
            ValidationError(path_str, "metadata.license", "Missing required field 'license'")
        )
    elif not isinstance(lic, str) or not lic.strip():
        errors.append(
            ValidationError(
                path_str, "metadata.license", "Field 'license' must be a non-empty string"
            )
        )

    # Security and trust rule:
    # Developers must NOT be allowed to self-assign verification status ('official' or 'community-reviewed').
    status = meta_sec.get("status")
    if status is not None:
        if not isinstance(status, str) or not status.strip():
            errors.append(
                ValidationError(
                    path_str, "metadata.status", "Field 'status' must be a non-empty string"
                )
            )
        else:
            status_clean = status.strip().lower()
            if status_clean not in VALID_STATUSES:
                errors.append(
                    ValidationError(
                        path_str,
                        "metadata.status",
                        f"Invalid verification status '{status}'. Allowed: {sorted(VALID_STATUSES)}",
                    )
                )
            elif not allow_privileged_status and status_clean in RESTRICTED_STATUSES:
                errors.append(
                    ValidationError(
                        path_str,
                        "metadata.status",
                        f"Security policy violation: Developers cannot self-assign status '{status}'. Verification status is strictly assigned by ELYos repository maintainers. Community manifests must specify 'unverified'.",
                    )
                )

    return errors


def scan_and_validate(
    repo_root: Path,
    registry_dirs: List[str] | None = None,
    allow_privileged_status: bool = False,
) -> Tuple[int, List[ValidationError]]:
    """Scan registry directories and validate all TOML manifest files."""
    if registry_dirs is None:
        registry_dirs = ["community-system-modules", "community-modules"]

    all_errors: List[ValidationError] = []
    seen_ids: Dict[str, str] = {}
    manifest_count = 0

    for rel_dir in registry_dirs:
        dir_path = repo_root / rel_dir
        if not dir_path.exists() or not dir_path.is_dir():
            all_errors.append(
                ValidationError(
                    rel_dir,
                    "directory",
                    f"Registry directory '{rel_dir}' does not exist",
                )
            )
            continue

        for item in sorted(dir_path.iterdir()):
            # Ignore hidden files like .gitkeep or .DS_Store
            if item.name.startswith("."):
                continue

            # Verify that manifest files have .toml extension
            if not item.name.endswith(".toml"):
                all_errors.append(
                    ValidationError(
                        str(item.relative_to(repo_root)),
                        "file_extension",
                        f"File '{item.name}' does not have the mandatory '.toml' extension.",
                    )
                )
                continue

            if not item.is_file():
                all_errors.append(
                    ValidationError(
                        str(item.relative_to(repo_root)),
                        "file_type",
                        f"'{item.name}' is a directory. Community registry directories must only contain manifest files.",
                    )
                )
                continue

            manifest_count += 1
            data, parse_err = parse_toml(item)
            rel_file_str = str(item.relative_to(repo_root))

            if parse_err:
                all_errors.append(ValidationError(rel_file_str, "syntax", parse_err))
                continue

            assert data is not None
            errs = validate_manifest(
                data,
                item.relative_to(repo_root),
                seen_ids=seen_ids,
                allow_privileged_status=allow_privileged_status,
            )
            all_errors.extend(errs)

    return manifest_count, all_errors


def main(argv: List[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Validate ELYos community TOML manifests."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to repository root (defaults to parent of tools/).",
    )
    parser.add_argument(
        "--allow-privileged-status",
        action="store_true",
        help="Allow official/community-reviewed status (for maintainer toolchains).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    print("=" * 60)
    print("ELYos Community Manifest Validator")
    print(f"Repository Root: {repo_root}")
    print("=" * 60)

    count, errors = scan_and_validate(
        repo_root, allow_privileged_status=args.allow_privileged_status
    )

    print(f"Scanned {count} community manifest(s).")

    if errors:
        print(f"\n[FAILED] Found {len(errors)} validation error(s):")
        for err in errors:
            print(f"  ERROR: {err}")
        print("\nPlease fix the above errors before submitting your manifest.")
        return 1

    print("\n[SUCCESS] All community manifests are valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
