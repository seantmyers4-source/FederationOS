# FREP-001 QA Re-certification Execution Evidence

**Record:** OSF-ENG-EXE-FREP-001-002  
**Workflow:** `bootstrap-validation`  
**Run:** `30595027111`  
**Verified evidence head:** `71fe2a1e9b8b4c7da1215c540d9ef474750feec9`  
**Immutable technical candidate:** `e5e11e8aa429cca4b0638ad1527726e918f224c9`

## Results

| Boundary | Job | Checkout | Baseline | Tests | Result |
|---|---:|---|---|---:|---|
| Pull-request head | `91045445397` | `71fe2a1e9b8b4c7da1215c540d9ef474750feec9` | Passed | 24 passed | Success |
| PR merge result | `91045445445` | GitHub merge ref `refs/pull/3/merge` | Passed | 24 passed | Success |
| Direct head | — | Not applicable to PR event | Skipped by explicit event condition | — | Expected |

The workflow used CPython 3.12.13, `jsonschema==4.23.0`, read-only repository permissions, and immutable action SHAs. No validation or test step was skipped in either applicable job.

## Interpretation

The pull-request head and merge result were separately checked out and validated. Both positive cases and all twenty-two negative cases passed. The direct-head path remains separately executable on non-`main` pushes and manual dispatch; its event-specific skip does not substitute for or mask either PR validation.

This evidence supports Engineering completion only. It does not establish QA certification, platform enforcement, evidence custody, canonical designation, Registry publication, release authorization, or Runtime activation.
