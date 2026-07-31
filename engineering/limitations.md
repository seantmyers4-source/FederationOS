# Connector Limitations and Unimplemented Controls

The available GitHub connector can read repository metadata and create branches, commits, files, and pull requests. It does not expose configuration or authoritative verification for branch protection/rulesets, required reviewers, force-push restrictions, deletion restrictions, administrative bypass, native secret scanning, environments, or backup continuity.

Required future administrative actions: enable and independently verify a protected `main`, required pull requests, independent CODEOWNERS approval, required `bootstrap-validation` check, force-push/deletion prohibition, controlled merge method, bypass attribution, native secret and dependency scanning, and recovery backups.

Compensating controls: preserve this candidate unmerged; make no substantive direct changes to `main`; use explicit public classification and automated basic checks. Residual risk remains high until platform controls and independent reviewers are established.
