#!/usr/bin/env python3
"""
tools/validate_structure.py

Validates the top-level repository structure, required documentation files,
and official vs. community component boundaries for ELYos.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Required top-level directories
EXPECTED_DIRECTORIES = [
    "core",
    "system-modules",
    "community-system-modules",
    "modules",
    "community-modules",
    "sdk",
    "tools",
    "tests",
    "docs",
]

# Required documentation files
REQUIRED_DOCS = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "docs/MANIFESTO.md",
    "docs/TECHNICAL_SPECIFICATION.md",
]

# Forbidden source code or archive extensions inside community registry directories
# Community module source code must strictly remain in developers' own repositories.
FORBIDDEN_REGISTRY_EXTENSIONS = {
    ".rs",
    ".py",
    ".c",
    ".cpp",
    ".cc",
    ".h",
    ".hpp",
    ".go",
    ".js",
    ".ts",
    ".sh",
    ".bash",
    ".bat",
    ".ps1",
    ".exe",
    ".bin",
    ".elf",
    ".so",
    ".dll",
    ".dylib",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".zst",
    ".7z",
    ".elyossysmod",
    ".elyosmod",
    ".iso",
    ".img",
    ".vmdk",
    ".qcow2",
    ".vdi",
}

COMMUNITY_REGISTRY_DIRS = [
    "community-system-modules",
    "community-modules",
]


class StructureValidationError:
    """Represents a structural or architectural violation."""

    def __init__(self, target: str, message: str):
        self.target = target
        self.message = message

    def __str__(self) -> str:
        return f"[{self.target}] {self.message}"


def validate_repository_structure(repo_root: Path) -> List[StructureValidationError]:
    """Validate repository directories, required files, and registry boundaries."""
    errors: List[StructureValidationError] = []

    # 1. Verify expected top-level directories
    for dir_name in EXPECTED_DIRECTORIES:
        target_dir = repo_root / dir_name
        if not target_dir.exists():
            errors.append(
                StructureValidationError(
                    dir_name,
                    f"Expected top-level directory '{dir_name}' does not exist.",
                )
            )
        elif not target_dir.is_dir():
            errors.append(
                StructureValidationError(
                    dir_name,
                    f"Target '{dir_name}' exists but is not a directory.",
                )
            )

    # 2. Verify required documentation files
    for doc_rel in REQUIRED_DOCS:
        target_file = repo_root / doc_rel
        if not target_file.exists():
            errors.append(
                StructureValidationError(
                    doc_rel,
                    f"Required documentation file '{doc_rel}' is missing.",
                )
            )
        elif not target_file.is_file():
            errors.append(
                StructureValidationError(
                    doc_rel,
                    f"Target '{doc_rel}' exists but is not a file.",
                )
            )
        elif target_file.stat().st_size == 0:
            errors.append(
                StructureValidationError(
                    doc_rel,
                    f"Required documentation file '{doc_rel}' is unexpectedly empty.",
                )
            )

    # 3. Verify separation between official components and community registries
    for reg_dir_name in COMMUNITY_REGISTRY_DIRS:
        reg_path = repo_root / reg_dir_name
        if not reg_path.exists() or not reg_path.is_dir():
            continue

        for item in reg_path.iterdir():
            # Allow hidden files like .gitkeep or .gitignore
            if item.name.startswith("."):
                continue

            # Allow documentation files like README.md inside registries
            if item.name.lower() in ("readme.md", "license.md", "license"):
                continue

            # Registries should strictly hold TOML manifests, not subdirectories or source trees
            if item.is_dir():
                errors.append(
                    StructureValidationError(
                        f"{reg_dir_name}/{item.name}",
                        f"Directories are not permitted inside '{reg_dir_name}'. "
                        "Community registries must only contain individual TOML manifest files.",
                    )
                )
                continue

            # Check for forbidden source code or archive formats
            ext = item.suffix.lower()
            if ext in FORBIDDEN_REGISTRY_EXTENSIONS:
                errors.append(
                    StructureValidationError(
                        f"{reg_dir_name}/{item.name}",
                        f"Forbidden source code or archive file '{item.name}' found in registry. "
                        "Community module source code must strictly remain in the developer's external repository.",
                    )
                )

            # Files must end with .toml
            if ext != ".toml":
                errors.append(
                    StructureValidationError(
                        f"{reg_dir_name}/{item.name}",
                        f"Non-manifest file '{item.name}' found. Files in '{reg_dir_name}' must have a '.toml' extension.",
                    )
                )

    return errors


def main(argv: List[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Validate ELYos repository structure and architectural boundaries."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to repository root (defaults to parent of tools/).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    print("=" * 60)
    print("ELYos Repository Structure Validator")
    print(f"Repository Root: {repo_root}")
    print("=" * 60)

    errors = validate_repository_structure(repo_root)

    if errors:
        print(f"\n[FAILED] Found {len(errors)} structural violation(s):")
        for err in errors:
            print(f"  VIOLATION: {err}")
        return 1

    print("\n[SUCCESS] Repository structure and architectural boundaries are valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
