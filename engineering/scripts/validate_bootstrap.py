#!/usr/bin/env python3
"""Deterministic FREP-001 candidate validator (Python 3.12)."""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import sys
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

REPOSITORY = "seantmyers4-source/FederationOS"
REQUIRED_FILES = (
    "README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE", ".gitignore",
    ".github/CODEOWNERS", ".github/pull_request_template.md",
    "governance/repository-identity.json", "governance/repository-governance.json",
    "governance/authority-ownership-map.json", "governance/directory-ownership-map.json",
    "archive/archive-manifest.json",
)
REQUIRED_DIRS = (
    "governance", "architecture", "registry", "engineering", "qa", "pmo",
    "runtime", "references", "templates", "docs", "archive",
)
SCHEMA_BINDINGS = {
    "governance/repository-identity.json": "registry/schemas/repository-identity.schema.json",
    "templates/cross-os-reference.json": "registry/schemas/cross-os-reference.schema.json",
}
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


def rel(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def load_json(path: pathlib.Path, root: pathlib.Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"JSON_PARSE {rel(path, root)}: {exc}")
        return None


def validate_schema(instance, schema, instance_path: str, schema_path: str, errors: list[str]):
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        errors.append(f"SCHEMA_DEFINITION {schema_path}: {exc.message}")
        return
    for error in sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.absolute_path)):
        location = "/".join(map(str, error.absolute_path)) or "$"
        errors.append(f"SCHEMA_CONFORMANCE {instance_path}#{location}: {error.message}")


def validate(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for item in REQUIRED_FILES:
        if not (root / item).is_file():
            errors.append(f"REQUIRED_FILE missing: {item}")
    for item in REQUIRED_DIRS:
        if not (root / item).is_dir():
            errors.append(f"REQUIRED_DIRECTORY missing: {item}")

    documents = {}
    for path in sorted(root.rglob("*.json")):
        if ".git" in path.parts:
            continue
        documents[rel(path, root)] = load_json(path, root, errors)

    schemas = {}
    for path, data in documents.items():
        if path.endswith(".schema.json") and data is not None:
            try:
                Draft202012Validator.check_schema(data)
                schemas[path] = data
            except SchemaError as exc:
                errors.append(f"SCHEMA_DEFINITION {path}: {exc.message}")

    dynamic = dict(SCHEMA_BINDINGS)
    for path in documents:
        if path.endswith(".provenance.json"):
            dynamic[path] = "registry/schemas/provenance.schema.json"
        elif "consumer-binding" in pathlib.PurePosixPath(path).name and not path.endswith(".schema.json"):
            dynamic[path] = "registry/schemas/consumer-binding.schema.json"
        elif "cross-os-reference" in pathlib.PurePosixPath(path).name and not path.endswith(".schema.json"):
            dynamic[path] = "registry/schemas/cross-os-reference.schema.json"
    for instance_path, schema_path in sorted(dynamic.items()):
        instance, schema = documents.get(instance_path), schemas.get(schema_path)
        if instance is None:
            if (root / instance_path).exists():
                continue
            errors.append(f"SCHEMA_INSTANCE missing: {instance_path}")
        elif schema is None:
            errors.append(f"SCHEMA_REQUIRED missing or invalid: {schema_path}")
        else:
            validate_schema(instance, schema, instance_path, schema_path, errors)

    identity = documents.get("governance/repository-identity.json") or {}
    governance = documents.get("governance/repository-governance.json") or {}
    if identity.get("repository") != REPOSITORY:
        errors.append("SEMANTIC_MANIFEST repository identity does not match FREP-001 boundary")
    if identity.get("canonical_status") != "candidate-not-designated":
        errors.append("SEMANTIC_MANIFEST candidate must remain candidate-not-designated")
    if governance.get("repository") != identity.get("repository"):
        errors.append("CROSS_RECORD repository governance and identity disagree")
    if governance.get("canonical_status") != "not-designated":
        errors.append("CROSS_RECORD governance must preserve non-canonical status")

    record_ids = {data.get("record_id") for data in documents.values() if isinstance(data, dict) and data.get("record_id")}
    cross_refs = {data.get("record_id") for path, data in documents.items() if "cross-os-reference" in pathlib.PurePosixPath(path).name and not path.endswith(".schema.json") and isinstance(data, dict)}
    for path, data in sorted(documents.items()):
        if not isinstance(data, dict):
            continue
        if data.get("canonical_copy") is True:
            errors.append(f"PROHIBITED_CANONICAL_COPY {path}")
        if path.endswith(".provenance.json"):
            if not data.get("source") or not data.get("owning_authority") or not data.get("history"):
                errors.append(f"PROVENANCE_INVALID {path}: source, owning_authority, and non-empty history required")
        if "cross-os-reference" in pathlib.PurePosixPath(path).name and not path.endswith(".schema.json"):
            if not data.get("source_authority") or not data.get("provenance_reference"):
                errors.append(f"CROSS_OS_REFERENCE_INVALID {path}: source authority and provenance reference required")
        if "consumer-binding" in pathlib.PurePosixPath(path).name and not path.endswith(".schema.json"):
            source = data.get("source_reference")
            if source not in cross_refs:
                errors.append(f"CONSUMER_BINDING_INVALID {path}: unresolved source_reference {source!r}")
            if data.get("creates_ownership") is not False:
                errors.append(f"CONSUMER_BINDING_INVALID {path}: creates_ownership must be false")
        for key in ("supersedes", "provenance_reference"):
            value = data.get(key)
            values = value if isinstance(value, list) else [value] if value else []
            for reference in values:
                if reference != "TBD" and reference not in record_ids:
                    errors.append(f"CROSS_RECORD {path}: unresolved {key} {reference!r}")

    validator_source = pathlib.Path(__file__).resolve()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if any(part in SKIP_SCAN_PARTS for part in path.parts) or path.resolve() == validator_source:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"SECRET_PATTERN {rel(path, root)}: representative {name}")
        for name, pattern in PROHIBITED_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"PROHIBITED_CONTENT {rel(path, root)}: {name}")
        if path.suffix.lower() == ".md":
            for target in MD_LINK.findall(text):
                clean = target.split("#", 1)[0].strip().strip("<>")
                if not clean or re.match(r"^(?:https?|mailto):", clean):
                    continue
                candidate = (path.parent / clean).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    errors.append(f"DOCUMENTATION_LINK {rel(path, root)}: link escapes repository: {target}")
                    continue
                if not candidate.exists():
                    errors.append(f"DOCUMENTATION_LINK {rel(path, root)}: broken link: {target}")
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
