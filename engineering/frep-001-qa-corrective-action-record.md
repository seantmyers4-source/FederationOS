# FREP-001 Engineering Corrective Action Record

**Record:** OSF-ENG-CAR-FREP-001-001  
**Consultation:** OSF-QA-CONS-FREP-001-001  
**Consultation disposition:** QA Certification Granted with Conditions  
**Reviewed boundary:** `f0a5b9e5b78dec14e252d59285f2c95788e1d9ea`  
**Superseding implementation candidate:** `042e898211ef6f0e8c897e36a70bca0d82d3fcbb`  
**Branch:** `engineering/frep-001-qa-corrective-001`  
**Repository:** `seantmyers4-source/FederationOS`

## Engineering assessment

The reviewed validator parsed JSON but did not enforce the repository schemas, systematic cross-record rules, provenance requirements, binding integrity, or a reproducible test suite. Engineering preserved the reviewed commit and implemented the corrections on a new branch.

The authoritative consultation body and its exact Engineering finding identifiers are not present in the repository or supplied with this directive. Engineering has not invented identifiers. The register below maps every Engineering requirement stated in the controlling corrective directive; QA must reconcile the pending identifiers during re-certification.

## Engineering Findings Response Register

| QA finding identifier | Engineering assessment | Corrective action | Status | Evidence | Remaining dependency | Closure recommendation |
|---|---|---|---|---|---|---|
| Pending authoritative QA record — schema conformance | Parser-only behavior was insufficient | Draft 2020-12 schema validation and schema self-validation | Implemented | `validate_bootstrap.py`; schema files; regression suite | QA independent execution | Reassess |
| Pending authoritative QA record — required fields/types/enums/constants | Requirements were not enforced | Strengthened four schemas and bound instances deterministically | Implemented | schema files; negative schema test | QA independent execution | Reassess |
| Pending authoritative QA record — semantic manifests | Candidate and authority semantics were narrow | Added repository identity, non-canonical state, and governance consistency rules | Implemented | validator; positive test | QA independent execution | Reassess |
| Pending authoritative QA record — cross-record validation | No general reference resolution | Added record-ID index and controlled reference resolution | Implemented | validator; regression suite | Registry interpretation remains independent | Reassess Engineering portion |
| Pending authoritative QA record — provenance | Schema was permissive and not applied to instances | Tightened schema; dynamic instance validation; semantic completeness rule | Implemented | provenance schema; negative provenance test | Custody approval | Reassess Engineering portion |
| Pending authoritative QA record — cross-OS references | Only `canonical_copy` was checked | Enforced complete reference schema, source authority, provenance reference, and no canonical copies | Implemented | cross-OS schema; two negative tests | Registry verification | Reassess Engineering portion |
| Pending authoritative QA record — consumer bindings | Schema was not executed | Added dynamic schema validation, source resolution, and no-ownership rule | Implemented | consumer-binding schema; negative binding test | Registry verification | Reassess Engineering portion |
| Pending authoritative QA record — positive/negative coverage | No executable test suite | Added one positive and eleven negative regression tests | Implemented | `engineering/tests/test_validator.py` | QA independent execution | Reassess |
| Pending authoritative QA record — reproducibility | No independent clean-environment procedure | Added pinned runtime dependency and QA reproduction guide | Implemented | requirements file; reproduction guide | QA execution environment | Reassess |
| Pending authoritative QA record — workflow integrity | Reusable actions were mutable tags; only one validation command | Pinned reusable actions, added branch-head/manual triggers, positive validation and regression steps | Implemented | workflow; workflow runs | Required-check enforcement is Repository authority | Reassess Engineering portion |

## External Dependency Register

| Dependency ID | Condition | Owner | Engineering treatment | Status | Blocking effect |
|---|---|---|---|---|---|
| FREP-EXT-001 | Authoritative QA consultation body and exact finding IDs | QA & Certification / evidence source | Recorded missing; no identifiers inferred | Open | Blocks exact finding-ID closure mapping, not technical implementation |
| FREP-EXT-002 | Repository rules, protected `main`, required checks, review and bypass controls | Repository & Platform Authority | Workflow/check names documented; settings unchanged | Open | Blocks merge authorization |
| FREP-EXT-003 | Native secret scanning and push protection | Security Governance / Repository authority | Engineering scanner retained and regression-tested | Open | Independent platform/security condition |
| FREP-EXT-004 | Cross-OS and consumer-binding policy verification | Registry & Metadata | Engineering enforcement implemented without redefining policy | Open | Blocks Registry concurrence |
| FREP-EXT-005 | Immutable evidence custody and retention | Records & Evidence Custody | Public evidence paths and immutable Git commits supplied | Open | Blocks custody acceptance |
| FREP-EXT-006 | Release authorization | PMO & Release Governance | No release action taken | Open | Blocks release |
| FREP-EXT-007 | Runtime consultation or activation | Runtime Operations | No runtime action taken | Open | Blocks activation |

## Repository Change Summary

- Replaced parser-only validation with deterministic schema and semantic validation.
- Tightened repository identity, provenance, cross-OS reference, and consumer-binding schemas.
- Added positive and negative regression tests covering every required failure class.
- Added a pinned validator dependency and candidate-head validation workflow.
- Pinned `actions/checkout` and `actions/setup-python` to immutable commit SHAs.
- Replaced third-party Markdown-link validation with deterministic internal-link validation in the repository validator.
- Preserved the original failing/passing runs as regression history; no history was rewritten.
- Did not modify repository settings, `main`, or Draft PR #1.

## Engineering decision

**ENGINEERING CORRECTIVE PACKAGE COMPLETE WITH EXTERNAL DEPENDENCIES**

Engineering-controlled corrective implementation is complete at the stated superseding implementation commit. The external conditions above remain open and are not closed by this record.
