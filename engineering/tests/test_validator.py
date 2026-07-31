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

    def test_positive_candidate(self):
        self.run_validator(self.candidate(), expected=0, contains="validation PASSED")

    def test_missing_required_file(self):
        root = self.candidate(); (root / "SECURITY.md").unlink()
        self.run_validator(root, contains="REQUIRED_FILE missing: SECURITY.md")

    def test_missing_required_directory(self):
        root = self.candidate(); shutil.rmtree(root / "runtime")
        self.run_validator(root, contains="REQUIRED_DIRECTORY missing: runtime")

    def test_malformed_json(self):
        root = self.candidate(); (root / "governance/repository-identity.json").write_text("{")
        self.run_validator(root, contains="JSON_PARSE governance/repository-identity.json")

    def test_schema_invalid_json(self):
        root = self.candidate(); path = root / "governance/repository-identity.json"
        data = json.loads(path.read_text()); data["repository_id"] = "not-an-integer"; path.write_text(json.dumps(data))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE governance/repository-identity.json#repository_id")

    def test_invalid_provenance(self):
        root = self.candidate(); path = root / "references/bad.provenance.json"
        path.write_text(json.dumps({"record_id":"P-1","artifact_id":"A-1","owning_authority":"X","source":"Y","history":[]}))
        self.run_validator(root, contains="SCHEMA_CONFORMANCE references/bad.provenance.json#history")

    def test_invalid_cross_os_reference(self):
        root = self.candidate(); path = root / "templates/cross-os-reference.json"
        data = json.loads(path.read_text()); data["canonical_copy"] = True; path.write_text(json.dumps(data))
        self.run_validator(root, contains="PROHIBITED_CANONICAL_COPY templates/cross-os-reference.json")

    def test_invalid_consumer_binding(self):
        root = self.candidate(); path = root / "references/example.consumer-binding.json"
        path.write_text(json.dumps({"record_id":"CB-1","consumer":"RuntimeOS","source_reference":"UNKNOWN","binding_version":"1","creates_ownership":False}))
        self.run_validator(root, contains="CONSUMER_BINDING_INVALID references/example.consumer-binding.json")

    def test_prohibited_canonical_copy(self):
        root = self.candidate(); path = root / "references/copied-artifact.json"
        path.write_text(json.dumps({"record_id":"COPY-1","canonical_copy":True}))
        self.run_validator(root, contains="PROHIBITED_CANONICAL_COPY references/copied-artifact.json")

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
