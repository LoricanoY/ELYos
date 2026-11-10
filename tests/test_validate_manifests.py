#!/usr/bin/env python3
"""
tests/test_validate_manifests.py

Unit tests for tools/validate_manifests.py.
"""

import sys
import unittest
from pathlib import Path

# Add repo root to sys.path so we can import tools
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.validate_manifests import (
    is_valid_module_id,
    is_valid_semver,
    is_valid_url,
    validate_manifest,
)


class TestManifestValidator(unittest.TestCase):
    def setUp(self):
        self.valid_data = {
            "module": {
                "id": "org.example.gaming-system",
                "name": "Example Gaming System",
                "description": "Community system module for testing",
                "version": "1.0.0",
            },
            "repository": {
                "type": "git",
                "url": "https://github.com/example/gaming-system",
                "branch": "main",
                "tag": "v1.0.0",
            },
            "compatibility": {
                "minimum_core_version": "0.1.0",
                "architecture": ["x86_64"],
            },
            "metadata": {
                "developer": "Example Developer",
                "license": "MIT",
                "status": "unverified",
            },
        }

    def test_valid_manifest(self):
        seen_ids = {}
        errors = validate_manifest(
            self.valid_data, Path("test.toml"), seen_ids=seen_ids
        )
        self.assertEqual(errors, [])
        self.assertIn("org.example.gaming-system", seen_ids)

    def test_missing_sections(self):
        data = {"module": {"id": "org.example.test"}}
        errors = validate_manifest(data, Path("test.toml"), seen_ids={})
        self.assertGreaterEqual(len(errors), 3)
        fields = [e.field for e in errors]
        self.assertIn("[repository]", fields)
        self.assertIn("[compatibility]", fields)
        self.assertIn("[metadata]", fields)

    def test_semver_validation(self):
        # Valid SemVer
        self.assertTrue(is_valid_semver("0.1.0"))
        self.assertTrue(is_valid_semver("1.0.0"))
        self.assertTrue(is_valid_semver("2.1.3-alpha.1"))
        self.assertTrue(is_valid_semver("1.0.0+20261111"))

        # Invalid SemVer
        self.assertFalse(is_valid_semver("1"))
        self.assertFalse(is_valid_semver("1.0"))
        self.assertFalse(is_valid_semver("v1.0.0"))
        self.assertFalse(is_valid_semver("1.0.0.0"))
        self.assertFalse(is_valid_semver("latest"))

    def test_module_id_validation(self):
        # Valid IDs (reverse-domain)
        self.assertTrue(is_valid_module_id("org.elyos.arch"))
        self.assertTrue(is_valid_module_id("com.developer.module"))
        self.assertTrue(is_valid_module_id("io.github.user.my-mod"))

        # Invalid IDs
        self.assertFalse(is_valid_module_id("singleword"))
        self.assertFalse(is_valid_module_id("MyModule"))
        self.assertFalse(is_valid_module_id("org..invalid"))
        self.assertFalse(is_valid_module_id("org/invalid"))

    def test_duplicate_module_id(self):
        seen_ids = {"org.example.gaming-system": "existing.toml"}
        errors = validate_manifest(
            self.valid_data, Path("duplicate.toml"), seen_ids=seen_ids
        )
        duplicate_errors = [e for e in errors if "Duplicate module ID" in e.message]
        self.assertEqual(len(duplicate_errors), 1)

    def test_mutable_branch_without_immutable_tag_rejected(self):
        data = dict(self.valid_data)
        data["repository"] = {
            "type": "git",
            "url": "https://github.com/example/gaming-system",
            "branch": "main",
            # No tag or commit
        }
        errors = validate_manifest(data, Path("test.toml"), seen_ids={})
        tag_errors = [e for e in errors if e.field == "repository.tag"]
        self.assertTrue(len(tag_errors) >= 1)
        self.assertIn("mutable branch", tag_errors[0].message.lower())

    def test_commit_hash_accepted_as_immutable_reference(self):
        data = dict(self.valid_data)
        data["repository"] = {
            "type": "git",
            "url": "https://github.com/example/gaming-system",
            "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
        }
        errors = validate_manifest(data, Path("test.toml"), seen_ids={})
        self.assertEqual(errors, [])

    def test_forbidden_self_assigned_status(self):
        data = dict(self.valid_data)
        data["metadata"] = dict(data["metadata"])
        data["metadata"]["status"] = "official"

        errors = validate_manifest(
            data, Path("test.toml"), seen_ids={}, allow_privileged_status=False
        )
        status_errors = [e for e in errors if e.field == "metadata.status"]
        self.assertEqual(len(status_errors), 1)
        self.assertIn("cannot self-assign status", status_errors[0].message)

        # But with allow_privileged_status=True, it passes
        errors_privileged = validate_manifest(
            data, Path("test.toml"), seen_ids={}, allow_privileged_status=True
        )
        self.assertEqual(errors_privileged, [])

    def test_architecture_validation(self):
        data = dict(self.valid_data)
        data["compatibility"] = dict(data["compatibility"])
        data["compatibility"]["architecture"] = ["invalid-arch-123"]

        errors = validate_manifest(data, Path("test.toml"), seen_ids={})
        arch_errors = [
            e for e in errors if "compatibility.architecture" in e.field
        ]
        self.assertEqual(len(arch_errors), 1)
        self.assertIn("Unsupported architecture", arch_errors[0].message)

    def test_url_validation(self):
        self.assertTrue(is_valid_url("https://github.com/example/repo"))
        self.assertTrue(is_valid_url("git://gitlab.com/example/repo.git"))
        self.assertFalse(is_valid_url("ftp://example.com/repo"))
        self.assertFalse(is_valid_url("not a url"))


if __name__ == "__main__":
    unittest.main()
