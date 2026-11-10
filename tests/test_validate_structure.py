#!/usr/bin/env python3
"""
tests/test_validate_structure.py

Unit tests for tools/validate_structure.py.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add repo root to sys.path so we can import tools
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.validate_structure import (
    EXPECTED_DIRECTORIES,
    REQUIRED_DOCS,
    validate_repository_structure,
)


class TestStructureValidator(unittest.TestCase):
    def test_current_repository_structure(self):
        """Current real repository should pass with 0 errors."""
        errors = validate_repository_structure(REPO_ROOT)
        self.assertEqual(
            errors,
            [],
            msg=f"Real repo structure validation failed: {[str(e) for e in errors]}",
        )

    def test_missing_directory_detected(self):
        """A simulated repo missing 'core' should produce an error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create all except 'core'
            for d in EXPECTED_DIRECTORIES:
                if d != "core":
                    (tmp_path / d).mkdir(parents=True, exist_ok=True)

            # Create dummy required docs
            for doc in REQUIRED_DOCS:
                doc_path = tmp_path / doc
                doc_path.parent.mkdir(parents=True, exist_ok=True)
                doc_path.write_text("Test doc content", encoding="utf-8")

            errors = validate_repository_structure(tmp_path)
            core_errors = [e for e in errors if e.target == "core"]
            self.assertEqual(len(core_errors), 1)

    def test_missing_required_doc_detected(self):
        """A simulated repo missing 'docs/MANIFESTO.md' should produce an error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create all directories
            for d in EXPECTED_DIRECTORIES:
                (tmp_path / d).mkdir(parents=True, exist_ok=True)

            # Create dummy required docs EXCEPT docs/MANIFESTO.md
            for doc in REQUIRED_DOCS:
                if doc != "docs/MANIFESTO.md":
                    doc_path = tmp_path / doc
                    doc_path.parent.mkdir(parents=True, exist_ok=True)
                    doc_path.write_text("Test doc content", encoding="utf-8")

            errors = validate_repository_structure(tmp_path)
            doc_errors = [e for e in errors if "MANIFESTO.md" in e.target]
            self.assertEqual(len(doc_errors), 1)

    def test_forbidden_source_code_in_registry_detected(self):
        """Committing source code into community-system-modules must fail."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            for d in EXPECTED_DIRECTORIES:
                (tmp_path / d).mkdir(parents=True, exist_ok=True)

            for doc in REQUIRED_DOCS:
                doc_path = tmp_path / doc
                doc_path.parent.mkdir(parents=True, exist_ok=True)
                doc_path.write_text("Test doc content", encoding="utf-8")

            # Place a forbidden Rust source file in community-system-modules
            bad_file = tmp_path / "community-system-modules" / "main.rs"
            bad_file.write_text("fn main() {}", encoding="utf-8")

            errors = validate_repository_structure(tmp_path)
            bad_errors = [
                e for e in errors if "community-system-modules/main.rs" in e.target
            ]
            self.assertTrue(len(bad_errors) >= 1)
            self.assertIn("Forbidden source code", bad_errors[0].message)


if __name__ == "__main__":
    unittest.main()
