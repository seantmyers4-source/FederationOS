# FREP-001 Positive Test Evidence

**Evidence ID:** OSF-ENG-EVI-FREP-001-POS-001  
**Candidate implementation:** `042e898211ef6f0e8c897e36a70bca0d82d3fcbb`

The positive test is `ValidatorRegressionTests.test_positive_candidate`. It copies the immutable candidate to a disposable directory, executes the same validator entry point used by CI, and requires exit code `0` plus `FREP-001 validation PASSED`.

The direct positive workflow step independently executes the validator against the checked-out candidate head before running the regression suite. Final run identity and conclusion are recorded in the QA re-certification handoff after GitHub Actions completes.

No repository setting, approval, merge authorization, or certification is inferred from a pass.

## Verified execution

GitHub Actions run `30592968662`, job `91039029410`, executed against PR #2 at technical head `042e898211ef6f0e8c897e36a70bca0d82d3fcbb`. The direct validator step printed `FREP-001 validation PASSED` and completed successfully under CPython 3.12.13.
