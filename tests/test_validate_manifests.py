#!/usr/bin/env python3
"""
tests/test_validate_manifests.py

Unit tests for tools/validate_manifests.py.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add repo root to sys.path so we can import tools
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.validate_manifests import (
    is_valid_commit_hash,
    is_valid_module_id,
    is_valid_semver,
    is_valid_url,
    scan_and_validate,
    validate_manifest,
)


class TestManifestValidator(unittest.TestCase):
    def setUp(self):
        # Canonical valid community manifest:
        # Mandatory: commit SHA (40-hex), no status field
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
                "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
                "tag": "v1.0.0",
            },
            "compatibility": {
                "minimum_core_version": "0.1.0",
                "architecture": ["x86_64"],
            },
            "metadata": {
                "developer": "Example Developer",
                "license": "MIT",
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

    def test_duplicate_module_id_cross_registry(self):
        seen_ids = {"org.example.gaming-system": "community-system-modules/sys.toml"}
        errors = validate_manifest(
            self.valid_data, Path("community-modules/mod.toml"), seen_ids=seen_ids
        )
        duplicate_errors = [e for e in errors if "Duplicate module ID" in e.message]
        self.assertEqual(len(duplicate_errors), 1)

    def test_missing_commit_hash_rejected_even_with_tag(self):
        """A tag alone is not cryptographic proof of immutability; commit is mandatory."""
        data = dict(self.valid_data)
        data["repository"] = {
            "type": "git",
            "url": "https://github.com/example/gaming-system",
            "tag": "v1.0.0",
            # commit is deliberately omitted
        }
        errors = validate_manifest(data, Path("test.toml"), seen_ids={})
        commit_errors = [e for e in errors if e.field == "repository.commit"]
        self.assertEqual(len(commit_errors), 1)
        self.assertIn("Missing required field 'commit'", commit_errors[0].message)

    def test_commit_hash_validation(self):
        # 40-char SHA-1
        self.assertTrue(is_valid_commit_hash("a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"))
        # 64-char SHA-256
        self.assertTrue(
            is_valid_commit_hash(
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            )
        )
        # Invalid short or non-hex
        self.assertFalse(is_valid_commit_hash("short123"))
        self.assertFalse(is_valid_commit_hash("g" * 40))  # 'g' is not hex
        self.assertFalse(is_valid_commit_hash("main"))

    def test_branch_name_used_as_tag_rejected(self):
        data = dict(self.valid_data)
        data["repository"] = dict(data["repository"])
        data["repository"]["tag"] = "main"

        errors = validate_manifest(data, Path("test.toml"), seen_ids={})
        tag_errors = [e for e in errors if e.field == "repository.tag"]
        self.assertEqual(len(tag_errors), 1)
        self.assertIn("mutable branch name", tag_errors[0].message.lower())

    def test_status_field_strictly_prohibited(self):
        # Community developers must never assign their own status
        for forbidden_status in ["official", "community-reviewed", "unverified", "problematic"]:
            data = dict(self.valid_data)
            data["metadata"] = dict(data["metadata"])
            data["metadata"]["status"] = forbidden_status

            errors = validate_manifest(data, Path("test.toml"), seen_ids={})
            status_errors = [e for e in errors if e.field == "metadata.status"]
            self.assertEqual(
                len(status_errors),
                1,
                msg=f"Failed to reject status '{forbidden_status}'",
            )
            self.assertIn("strictly prohibited", status_errors[0].message)

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
        self.assertFalse(is_valid_url("http://localhost:8080/repo"))
        self.assertFalse(is_valid_url("http://127.0.0.1/repo"))
        self.assertFalse(is_valid_url("not a url"))

    def test_fixtures_system_module_and_extension_accepted_and_rejected(self):
        """
        Verify both community registries using temporary test fixtures:
        - A valid community system module (.toml)
        - A valid community extension (.toml)
        Both are accepted when valid and rejected when invalid.
        No fictitious modules are left registered in the repo.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            sys_reg = tmp_root / "community-system-modules"
            mod_reg = tmp_root / "community-modules"
            sys_reg.mkdir()
            mod_reg.mkdir()

            # 1. Test empty registries produce valid result
            count, errors = scan_and_validate(tmp_root)
            self.assertEqual(count, 0)
            self.assertEqual(errors, [])

            # 2. Create valid system module manifest fixture
            sys_manifest_content = """
[module]
id = "org.community.arch-hardened"
name = "Arch Linux Hardened"
description = "Community hardened kernel system module"
version = "1.0.0"

[repository]
type = "git"
url = "https://github.com/community/arch-hardened"
commit = "1111222233334444555566667777888899990000"
tag = "v1.0.0"

[compatibility]
minimum_core_version = "0.1.0"
architecture = ["x86_64"]

[metadata]
developer = "Security Team"
license = "GPL-3.0"
"""
            # Create valid community extension manifest fixture
            ext_manifest_content = """
[module]
id = "org.community.battery-saver"
name = "Battery Optimizer"
description = "Aggressive power management module"
version = "0.2.1"

[repository]
type = "git"
url = "https://github.com/community/battery-saver"
commit = "aaaabbbbccccddddeeeeffff0000111122223333"
tag = "v0.2.1"

[compatibility]
minimum_core_version = "0.1.0"
architecture = ["x86_64", "aarch64"]

[metadata]
developer = "Power Hacker"
license = "MIT"
"""
            (sys_reg / "arch-hardened.toml").write_text(
                sys_manifest_content, encoding="utf-8"
            )
            (mod_reg / "battery-saver.toml").write_text(
                ext_manifest_content, encoding="utf-8"
            )

            # Validate both fixtures are scanned and accepted
            count, errors = scan_and_validate(tmp_root)
            self.assertEqual(count, 2)
            self.assertEqual(errors, [])

            # 3. Test invalid fixtures:
            # - sys module missing commit
            # - ext module with self-assigned status
            bad_sys_content = sys_manifest_content.replace(
                'commit = "1111222233334444555566667777888899990000"', ""
            )
            bad_ext_content = ext_manifest_content + '\nstatus = "official"\n'

            (sys_reg / "arch-hardened.toml").write_text(
                bad_sys_content, encoding="utf-8"
            )
            (mod_reg / "battery-saver.toml").write_text(
                bad_ext_content, encoding="utf-8"
            )

            count, errors = scan_and_validate(tmp_root)
            self.assertEqual(count, 2)
            self.assertEqual(len(errors), 2)
            err_fields = [e.field for e in errors]
            self.assertIn("repository.commit", err_fields)
            self.assertIn("metadata.status", err_fields)


if __name__ == "__main__":
    unittest.main()
