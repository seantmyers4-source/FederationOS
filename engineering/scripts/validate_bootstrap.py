#!/usr/bin/env python3
"""Deterministic FREP-001 candidate validator (Python 3.12)."""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import sys
from collections import Counter

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

REPOSITORY = "seantmyers4-source/FederationOS"
BINDING_MANIFEST = "registry/schema-binding-manifest.json"
REQUIRED_FILES = (
    "README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE", ".gitignore",
    ".github/CODEOWNERS", ".github/pull_request_template.md",
    "governance/repository-identity.json", "governance/repository-governance.json",
    "governance/authority-ownership-map.json", "governance/directory-ownership-map.json",
    "archive/archive-manifest.json", BINDING_MANIFEST,
)
REQUIRED_DIRS = (
    "governance", "architecture", "registry", "engineering", "qa", "pmo",
    "runtime", "references", "templates", "docs", "archive",
)
SECRET_PATTERNS = {
    "GitHub token": re.compile(r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
PROHIBITED_PATTERNS = {
    "medical record": re.compile(r"\bmedical record\b", re.I),
    "social security number": re.compile(r"\bsocial security number\b", re.I),
    "bank account number": re.compile(r"\bbank account number\b", re.I),
}
SKIP_SCAN_PARTS = {".git", ".pytest_cache", "__pycache__", "tests"}
MD_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def relative(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def load_json(path: pathlib.Path, root: pathlib.Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"JSON_PARSE {relative(path, root)}: {exc}")
        return None


def schema_errors(instance, schema, instance_path: str, errors: list[str]) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(instance), key=lambda e: (list(e.absolute_path), e.message)):
        location = "/".join(map(str, error.absolute_path)) or "$"
        errors.append(f"SCHEMA_CONFORMANCE {instance_path}#{location}: {error.message}")


def binding_targets(manifest: dict, documents: dict[str, object], errors: list[str]) -> dict[str, str]:
    bound: dict[str, str] = {}
    for binding in manifest.get("bindings", []):
        schema = binding.get("schema")
        role = binding.get("role")
        if role not in {"record", "template"}:
            errors.append(f"SCHEMA_BINDING_INVALID {BINDING_MANIFEST}: unsupported role {role!r}")
            continue
        matches: list[str] = []
        if "path" in binding and binding["path"] in documents:
            matches = [binding["path"]]
        elif "glob" in binding:
            matches = sorted(path for path in documents if fnmatch.fnmatch(path, binding["glob"]))
        if binding.get("required") and not matches:
            errors.append(f"SCHEMA_BINDING_MISSING {BINDING_MANIFEST}: {binding.get('path') or binding.get('glob')}")
        for path in matches:
            if path.endswith(".schema.json"):
                errors.append(f"SCHEMA_BINDING_INVALID {BINDING_MANIFEST}: schema document bound as instance {path}")
            elif path in bound and bound[path] != schema:
                errors.append(f"SCHEMA_BINDING_AMBIGUOUS {BINDING_MANIFEST}: {path}")
            else:
                bound[path] = schema
    return bound


def find_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str, trail: list[str]) -> list[str] | None:
        if node in visiting:
            return trail[trail.index(node):] + [node]
        if node in visited:
            return None
        visiting.add(node)
        for target in edges.get(node, []):
            cycle = walk(target, trail + [target])
            if cycle:
                return cycle
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(edges):
        cycle = walk(node, [node])
        if cycle:
            return cycle
    return None


def validate(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for item in REQUIRED_FILES:
        if not (root / item).is_file():
            errors.append(f"REQUIRED_FILE missing: {item}")
    for item in REQUIRED_DIRS:
        if not (root / item).is_dir():
            errors.append(f"REQUIRED_DIRECTORY missing: {item}")

    documents: dict[str, object] = {}
    for path in sorted(root.rglob("*.json")):
        if ".git" not in path.parts and "tests" not in path.parts:
            documents[relative(path, root)] = load_json(path, root, errors)

    schemas: dict[str, dict] = {}
    for path, data in documents.items():
        if path.endswith(".schema.json") and isinstance(data, dict):
            try:
                Draft202012Validator.check_schema(data)
                schemas[path] = data
            except SchemaError as exc:
                errors.append(f"SCHEMA_DEFINITION {path}: {exc.message}")

    manifest = documents.get(BINDING_MANIFEST)
    if not isinstance(manifest, dict):
        errors.append(f"SCHEMA_BINDING_INVALID {BINDING_MANIFEST}: object required")
        manifest = {}
    manifest_schema = schemas.get("registry/schemas/schema-binding-manifest.schema.json")
    if manifest_schema:
        schema_errors(manifest, manifest_schema, BINDING_MANIFEST, errors)
    else:
        errors.append("SCHEMA_REQUIRED missing or invalid: registry/schemas/schema-binding-manifest.schema.json")

    bindings = binding_targets(manifest, documents, errors)
    for instance_path, schema_path in sorted(bindings.items()):
        instance, schema = documents.get(instance_path), schemas.get(schema_path)
        if instance is None:
            continue
        if schema is None:
            errors.append(f"SCHEMA_REQUIRED missing or invalid: {schema_path}")
        else:
            schema_errors(instance, schema, instance_path, errors)

    identity = documents.get("governance/repository-identity.json") or {}
    governance = documents.get("governance/repository-governance.json") or {}
    if isinstance(identity, dict) and identity.get("repository") != REPOSITORY:
        errors.append("SEMANTIC_MANIFEST repository identity does not match FREP-001 boundary")
    if isinstance(identity, dict) and identity.get("canonical_status") != "candidate-not-designated":
        errors.append("SEMANTIC_MANIFEST candidate must remain candidate-not-designated")
    if isinstance(governance, dict) and isinstance(identity, dict):
        if governance.get("repository") != identity.get("repository"):
            errors.append("CROSS_RECORD repository governance and identity disagree")
        if governance.get("canonical_status") != "not-designated":
            errors.append("CROSS_RECORD governance must preserve non-canonical status")

    template_paths = {
        binding.get("path") for binding in manifest.get("bindings", [])
        if binding.get("role") == "template" and binding.get("path")
    }
    record_locations: dict[str, list[str]] = {}
    for path, data in documents.items():
        if (
            path not in template_paths
            and not path.endswith(".schema.json")
            and isinstance(data, dict)
            and isinstance(data.get("record_id"), str)
            and data.get("record_id") != "TBD"
        ):
            record_locations.setdefault(data["record_id"], []).append(path)
    for record_id, paths in sorted(record_locations.items()):
        if len(paths) > 1:
            errors.append(f"DUPLICATE_RECORD_ID {record_id!r}: {', '.join(sorted(paths))}")
    record_ids = set(record_locations)

    authority_ids = {
        data["record_id"] for path, data in documents.items()
        if path.endswith(".source-authority.json") and isinstance(data, dict)
        and data.get("status") == "verified"
    }
    cross_reference_ids = {
        data["record_id"] for path, data in documents.items()
        if path.endswith(".cross-os-reference.json") and isinstance(data, dict)
    }
    supersession_edges: dict[str, list[str]] = {}
    for path, data in sorted(documents.items()):
        if not isinstance(data, dict) or path.endswith(".schema.json"):
            continue
        record_id = data.get("record_id")
        if data.get("canonical_copy") is True:
            errors.append(f"PROHIBITED_CANONICAL_COPY {path}")
        if path.endswith(".provenance.json") and (
            not data.get("source") or not data.get("owning_authority") or not data.get("history")
        ):
            errors.append(f"PROVENANCE_INVALID {path}: source, owning_authority, and non-empty history required")
        if path.endswith(".cross-os-reference.json"):
            source_authority = data.get("source_authority")
            if not source_authority:
                errors.append(f"SOURCE_AUTHORITY_MISSING {path}")
            elif source_authority not in authority_ids:
                errors.append(f"SOURCE_AUTHORITY_UNRESOLVED {path}: {source_authority!r}")
            provenance = data.get("provenance_reference")
            if provenance and provenance not in record_ids:
                errors.append(f"CROSS_RECORD_BROKEN {path}: unresolved provenance_reference {provenance!r}")
        if path.endswith(".consumer-binding.json"):
            source = data.get("source_reference")
            if source not in cross_reference_ids:
                errors.append(f"CONSUMER_BINDING_INVALID {path}: unresolved source_reference {source!r}")
            if data.get("creates_ownership") is not False:
                errors.append(f"CONSUMER_BINDING_INVALID {path}: creates_ownership must be false")
        supersedes = data.get("supersedes", [])
        if isinstance(supersedes, str):
            supersedes = [supersedes]
        if isinstance(record_id, str) and isinstance(supersedes, list):
            supersession_edges[record_id] = []
            for target in supersedes:
                if target not in record_ids:
                    errors.append(f"SUPERSESSION_INVALID {path}: unresolved supersedes {target!r}")
                elif target == record_id:
                    errors.append(f"SUPERSESSION_INVALID {path}: record cannot supersede itself")
                else:
                    supersession_edges[record_id].append(target)
    cycle = find_cycle(supersession_edges)
    if cycle:
        errors.append(f"SUPERSESSION_INVALID cycle: {' -> '.join(cycle)}")

    validator_source = pathlib.Path(__file__).resolve()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if any(part in SKIP_SCAN_PARTS for part in path.parts):
            continue
        if path.resolve() == validator_source or relative(path, root) == "engineering/scripts/validate_bootstrap.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"SECRET_PATTERN {relative(path, root)}: representative {name}")
        for name, pattern in PROHIBITED_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"PROHIBITED_CONTENT {relative(path, root)}: {name}")
        if path.suffix.lower() == ".md":
            for target in MD_LINK.findall(text):
                clean = target.split("#", 1)[0].strip().strip("<>")
                if not clean or re.match(r"^(?:https?|mailto):", clean):
                    continue
                candidate = (path.parent / clean).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    errors.append(f"DOCUMENTATION_LINK {relative(path, root)}: link escapes repository: {target}")
                    continue
                if not candidate.exists():
                    errors.append(f"DOCUMENTATION_LINK {relative(path, root)}: broken link: {target}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        print("FREP-001 validation FAILED")
        print("\n".join(errors))
        return 1
    print("FREP-001 validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
