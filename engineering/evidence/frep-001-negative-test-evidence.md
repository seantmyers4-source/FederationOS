# FREP-001 Negative Test Evidence

**Evidence ID:** OSF-ENG-EVI-FREP-001-NEG-001  
**Candidate implementation:** `18995eca88537e23fc7569eaabbe51e635204387`

| Test | Injected defect | Required fail-closed evidence |
|---|---|---|
| Missing file | Delete `SECURITY.md` in disposable copy | `REQUIRED_FILE` |
| Missing directory | Delete `runtime/` in disposable copy | `REQUIRED_DIRECTORY` |
| Malformed JSON | Truncate repository identity | `JSON_PARSE` |
| Schema-invalid JSON | Replace numeric repository ID with text | `SCHEMA_CONFORMANCE` |
| Invalid provenance | Empty history in a provenance instance | `SCHEMA_CONFORMANCE` |
| Invalid cross-OS reference | Set `canonical_copy=true` | `PROHIBITED_CANONICAL_COPY` |
| Invalid consumer binding | Reference an unknown cross-OS record | `CONSUMER_BINDING_INVALID` |
| Prohibited canonical copy | Add a copied-artifact manifest | `PROHIBITED_CANONICAL_COPY` |
| Representative credential pattern | Add a synthetic token-shaped value | `SECRET_PATTERN` |
| Representative restricted-content pattern | Add a synthetic restricted identifier phrase | `PROHIBITED_CONTENT` |
| Broken documentation link | Add a nonexistent relative Markdown target | `DOCUMENTATION_LINK` |

Each test requires exit code `1` and its specific error category. The suite operates only on temporary copies and leaves the governed candidate unchanged. Final workflow run identity and conclusion are recorded in the QA handoff.
