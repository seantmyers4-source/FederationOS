# FREP-001 QA Re-certification Test Plan

**Record:** OSF-ENG-TP-FREP-001-002  
**Diagnostic contract:** `engineering/tests/diagnostic-contract.json`

The executable suite contains two positive tests and twenty-two negative tests. Each negative test introduces one bounded defect, expects exit code `1`, and asserts the diagnostic category associated with that defect.

Positive coverage:

1. Valid baseline candidate.
2. Valid cross-OS reference, verified Source Authority, valid consumer binding, and authorized public-safe content.

Negative coverage:

- Missing file and directory
- Malformed JSON
- Missing required field
- Invalid type, enumeration, and constant
- Invalid, missing, and unresolved Source Authority
- Duplicate identifier
- Broken cross-record reference
- Invalid supersession
- Empty required value
- Unexpected property
- Incorrect schema version
- Nested/alternate-path invalid record
- Invalid consumer binding
- Prohibited canonical copy
- Representative secret and prohibited content
- Broken documentation link

The expected category and exit code for every negative case are machine-readable in the diagnostic contract. QA should confirm each case fails for the asserted reason and that both positive cases pass.
