# FREP-001 Validator Design Update

**Record:** OSF-ENG-VDU-FREP-001-001  
**Runtime:** CPython 3.12  
**Dependency:** `jsonschema==4.23.0`  
**Entry point:** `python engineering/scripts/validate_bootstrap.py`

## Design goals

The validator is deterministic, read-only, fail-closed, repository-root aware, and suitable for independent execution. Findings are sorted and de-duplicated so identical inputs produce stable output and exit status.

## Validation pipeline

1. Confirm required files and directories.
2. Parse every JSON document.
3. validate every JSON Schema against Draft 2020-12 meta-schema rules.
4. Bind governed instances to schemas and enforce required fields, types, enumerations, and constants.
5. Enforce semantic manifest rules for repository identity and non-canonical candidate status.
6. Build a record-ID index and resolve governed cross-record references.
7. Enforce provenance completeness and non-empty history.
8. Enforce cross-OS source authority, provenance reference, and `canonical_copy=false`.
9. Enforce consumer-binding source resolution and `creates_ownership=false`.
10. Scan governed content for representative secret and prohibited-content patterns.
11. Validate internal Markdown link targets and prevent repository-escape links.

## Schema bindings

| Instance class | Schema | Selection |
|---|---|---|
| Repository identity | `repository-identity.schema.json` | Exact governed path |
| Cross-OS reference | `cross-os-reference.schema.json` | Filename convention plus template path |
| Provenance | `provenance.schema.json` | `*.provenance.json` |
| Consumer binding | `consumer-binding.schema.json` | Filename containing `consumer-binding` except schema |

## Scan boundary

The content scanner covers repository files except Git internals, interpreter caches, and `engineering/tests`. Test source is excluded because it must contain representative negative-test strings. The negative suite proves those same patterns are detected when placed in governed content. This exclusion does not cover governance, documentation, templates, references, evidence, or implementation source outside the test directory.

## Error contract

- Exit `0`: `FREP-001 validation PASSED`.
- Exit `1`: `FREP-001 validation FAILED` followed by stable category/path messages.
- Error prefixes identify the failed layer, including `SCHEMA_CONFORMANCE`, `SEMANTIC_MANIFEST`, `CROSS_RECORD`, `PROVENANCE_INVALID`, `CROSS_OS_REFERENCE_INVALID`, `CONSUMER_BINDING_INVALID`, `PROHIBITED_CANONICAL_COPY`, `SECRET_PATTERN`, `PROHIBITED_CONTENT`, and `DOCUMENTATION_LINK`.

## Regression preservation

The original validator defect remains immutable at commit `f0a5b9e5b78dec14e252d59285f2c95788e1d9ea`, with workflow runs `30591017023` (failed) and `30591075868` (passed after the narrow correction). The new regression suite prevents recurrence and expands coverage beyond those defects.

## Corrective workflow regression

Run `30592862411` revealed that prohibited-pattern definitions self-triggered and that `tee` masked nonzero exit codes. The validator now excludes only its exact implementation path (including disposable-copy equivalents), while governed content remains scanned; the workflow invokes commands directly so failures propagate. Run `30592968662` verifies both corrections.
