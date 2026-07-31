# FREP-001 Positive Test Evidence

**Evidence ID:** OSF-ENG-EVI-FREP-001-POS-001  
**Candidate implementation:** `18995eca88537e23fc7569eaabbe51e635204387`

The positive test is `ValidatorRegressionTests.test_positive_candidate`. It copies the immutable candidate to a disposable directory, executes the same validator entry point used by CI, and requires exit code `0` plus `FREP-001 validation PASSED`.

The direct positive workflow step independently executes the validator against the checked-out candidate head before running the regression suite. Final run identity and conclusion are recorded in the QA re-certification handoff after GitHub Actions completes.

No repository setting, approval, merge authorization, or certification is inferred from a pass.
