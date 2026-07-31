#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "engineering/scripts/validate_bootstrap.py"


class ValidatorRegressionTests(unittest.TestCase):
    maxDiff = None

    def candidate(self):
        temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(temp.name) / "repo"
        shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__"))
        self.addCleanup(temp.cleanup)
        return root

    def run_validator(self, root, expected=1, contains=None):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(root)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        if contains:
            self.assertIn(contains, result.stdout + result.stderr)
        return result

    @staticmethod
    def write(root, path, data):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data), encoding="utf-8")

    def valid_relationships(self, root, prefix="QA"):
        authority = f"{prefix}-AUTH-001"
        provenance = f"{prefix}-PROV-001"
        reference = f"{prefix}-XREF-001"
        binding = f"{prefix}-BIND-001"
        self.write(root, f"references/{prefix.lower()}.source-authority.json", {
            "schema_version": "0.1", "record_id": authority,
            "authority_name": "QA Fixture Source Authority",
            "operating_system": "FixtureOS", "status": "verified",
        })
        self.write(root, f"references/{prefix.lower()}.provenance.json", {
            "record_id": provenance, "artifact_id": f"{prefix}-ART-001",
            "owning_authority": authority, "source": "public-safe QA fixture",
            "history": [{"event": "created", "timestamp": "2026-07-31T00:00:00Z", "authority": authority}],
        })
        self.write(root, f"references/{prefix.lower()}.cross-os-reference.json", {
            "record_id": reference, "source_os": "FixtureOS",
            "source_artifact": f"{prefix}-ART-001", "source_authority": authority,
            "reference_type": "reference", "canonical_copy": False,
            "provenance_reference": provenance, "consumer_bindings": [binding],
        })
        self.write(root, f"references/{prefix.lower()}.consumer-binding.json", {
            "record_id": binding, "consumer": "FederationOS",
            "source_reference": reference, "binding_version": "1.0",
            "creates_ownership": False,
        })
        return authority, provenance, reference, binding

    def test_valid_baseline_candidate(self):
        self.run_validator(self.candidate(), expected=0, contains="validation PASSED")

    def test_valid_cross_os_reference_consumer_binding_and_public_content(self):
        root = self.candidate()
        self.valid_relationships(root)
        (root / "docs/public-safe-fixture.md").write_text("# Public-safe fixture\nAuthorized test content.\n")
        self.run_validator(root, expected=0, contains="validation PASSED")

    def test_missing_required_file(self):
        root = self.candidate(); (root / "SECURITY.md").unlink()
        self.run_validator(root, contains="REQUIRED_FILE missing: SECURITY.md")

    def test_missing_required_directory(self):
        root = self.candidate(); shutil.rmtree(root / "runtime")
        self.run_validator(root, contains="REQUIRED_DIRECTORY missing: runtime")

    def test_malformed_json(self):
        root = self.candidate(); (root / "governance/repository-identity.json").write_text("{")
        self.run_validator(root, contains="JSON_PARSE governance/repository-identity.json")

    def test_missing_required_field(self):
        root = self.candidate(); path = root / "governance/repository-identity.json"
        data = json.loads(path.read_text()); del data["owner"]; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE governance/repository-identity.json#$")

    def test_invalid_type(self):
        root = self.candidate(); path = root / "governance/repository-identity.json"
        data = json.loads(path.read_text()); data["repository_id"] = "bad"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE governance/repository-identity.json#repository_id")

    def test_invalid_enumeration(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.source-authority.json"
        data = json.loads(path.read_text()); data["status"] = "invalid"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE references/qa.source-authority.json#status")

    def test_invalid_constant(self):
        root = self.candidate(); path = root / "governance/repository-identity.json"
        data = json.loads(path.read_text()); data["canonical_status"] = "canonical"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE governance/repository-identity.json#canonical_status")

    def test_invalid_source_authority_type(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.source-authority.json"
        data = json.loads(path.read_text()); data["authority_name"] = 7; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE references/qa.source-authority.json#authority_name")

    def test_missing_source_authority(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.cross-os-reference.json"
        data = json.loads(path.read_text()); del data["source_authority"]; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SOURCE_AUTHORITY_MISSING references/qa.cross-os-reference.json")

    def test_unresolved_source_authority(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.cross-os-reference.json"
        data = json.loads(path.read_text()); data["source_authority"] = "UNKNOWN"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SOURCE_AUTHORITY_UNRESOLVED references/qa.cross-os-reference.json")

    def test_duplicate_identifier(self):
        root = self.candidate(); self.valid_relationships(root)
        self.write(root, "references/duplicate.source-authority.json", {
            "schema_version": "0.1", "record_id": "QA-AUTH-001",
            "authority_name": "Duplicate", "operating_system": "FixtureOS", "status": "verified",
        })
        self.run_validator(root, contains="DUPLICATE_RECORD_ID 'QA-AUTH-001'")

    def test_broken_cross_record_reference(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.cross-os-reference.json"
        data = json.loads(path.read_text()); data["provenance_reference"] = "MISSING"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="CROSS_RECORD_BROKEN references/qa.cross-os-reference.json")

    def test_invalid_supersession(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.source-authority.json"
        data = json.loads(path.read_text()); data["supersedes"] = ["MISSING"]; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SUPERSESSION_INVALID references/qa.source-authority.json")

    def test_empty_required_value(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.consumer-binding.json"
        data = json.loads(path.read_text()); data["consumer"] = ""; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE references/qa.consumer-binding.json#consumer")

    def test_unexpected_property_behavior(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.consumer-binding.json"
        data = json.loads(path.read_text()); data["unexpected"] = True; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE references/qa.consumer-binding.json#$")

    def test_incorrect_schema_version(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.source-authority.json"
        data = json.loads(path.read_text()); data["schema_version"] = "9.9"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE references/qa.source-authority.json#schema_version")

    def test_nested_or_alternate_path_record_is_bound(self):
        root = self.candidate()
        self.write(root, "docs/nested/alternate.consumer-binding.json", {
            "record_id": "ALT-BIND-001", "consumer": "FederationOS",
            "source_reference": "MISSING", "binding_version": "1.0", "creates_ownership": False,
        })
        self.run_validator(root, contains="CONSUMER_BINDING_INVALID docs/nested/alternate.consumer-binding.json")

    def test_invalid_consumer_binding(self):
        root = self.candidate()
        self.write(root, "references/bad.consumer-binding.json", {
            "record_id": "CB-1", "consumer": "RuntimeOS", "source_reference": "UNKNOWN",
            "binding_version": "1", "creates_ownership": False,
        })
        self.run_validator(root, contains="CONSUMER_BINDING_INVALID references/bad.consumer-binding.json")

    def test_prohibited_canonical_copy(self):
        root = self.candidate(); self.valid_relationships(root); path = root / "references/qa.cross-os-reference.json"
        data = json.loads(path.read_text()); data["canonical_copy"] = True; path.write_text(json.dumps(data))
        self.run_validator(root, contains="PROHIBITED_CANONICAL_COPY references/qa.cross-os-reference.json")

    def test_representative_secret_pattern(self):
        root = self.candidate(); (root / "docs/leak.txt").write_text("ghp_" + "A" * 30)
        self.run_validator(root, contains="SECRET_PATTERN docs/leak.txt")

    def test_representative_prohibited_content(self):
        root = self.candidate(); (root / "docs/restricted.txt").write_text("social security number")
        self.run_validator(root, contains="PROHIBITED_CONTENT docs/restricted.txt")

    def test_broken_documentation_link(self):
        root = self.candidate(); (root / "docs/broken.md").write_text("[missing](does-not-exist.md)")
        self.run_validator(root, contains="DOCUMENTATION_LINK docs/broken.md")


if __name__ == "__main__":
    unittest.main(verbosity=2)
