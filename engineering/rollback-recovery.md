# Rollback and Recovery

Before merge, rollback is closing the pull request and deleting the remediation branch only after preserving review evidence under Custody direction. The initializer on `main` remains because it is the technical prerequisite for branch/PR operation.

After an authorized merge, revert through a new governed pull request referencing the original merge and reason; do not rewrite history. Recovery relies on Git history and GitHub availability until Records & Evidence Custody establishes independently verified backups and immutable evidence. No such backup is asserted today.
