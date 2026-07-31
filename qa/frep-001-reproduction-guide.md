# FREP-001 Independent QA Reproduction Guide

**Record:** OSF-ENG-QARG-FREP-001-001  
**Candidate implementation commit:** `042e898211ef6f0e8c897e36a70bca0d82d3fcbb`

## Supported runtime and tools

- Clean Linux, macOS, or Windows environment capable of running CPython 3.12.
- Git for immutable checkout.
- Network access only to obtain the repository and the pinned Python package; execution itself is local and read-only.
- No GitHub administrative permission is required.

## Clean-environment procedure

```bash
git clone https://github.com/seantmyers4-source/FederationOS.git
cd FederationOS
git checkout 042e898211ef6f0e8c897e36a70bca0d82d3fcbb
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --disable-pip-version-check -r engineering/requirements-validation.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Positive validation

```bash
python engineering/scripts/validate_bootstrap.py
```

Expected output and status:

```text
FREP-001 validation PASSED
```

Exit code: `0`.

## Positive and negative regression suite

```bash
python -m unittest -v engineering/tests/test_validator.py
```

Expected result: twelve tests run and `OK`. The suite creates disposable candidate copies, applies one controlled defect per negative test, and verifies the expected fail-closed category. It does not alter the checkout.

## Negative-test procedure

For manual confirmation, copy the checkout to a disposable directory, introduce exactly one defect, and run:

```bash
python engineering/scripts/validate_bootstrap.py --root /absolute/path/to/disposable-copy
```

Expected output begins `FREP-001 validation FAILED`, identifies the error category and path, and exits `1`. Never introduce negative fixtures into the governed branch.

## GitHub Actions procedure

The `bootstrap-validation` workflow runs on pull-request heads, non-`main` branch heads, and manual dispatch. Confirm that both `Positive candidate validation` and `Positive and negative regression tests` execute and succeed against the exact candidate SHA. A passing run is evidence, not merge authorization or repository-setting enforcement.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| Python version differs | Use CPython 3.12; do not infer compatibility from another major/minor version |
| `jsonschema` unavailable | Install only from `engineering/requirements-validation.txt` |
| Schema definition failure | Validate the named schema itself before changing any instance |
| Cross-record failure | Confirm the referenced record ID is present in the same candidate |
| Content-pattern failure | Remove the prohibited content from governed files; do not weaken patterns to obtain a pass |
| Link failure | Correct the relative target and keep it inside the repository |
| CI differs from local | Verify the exact checked-out SHA, Python version, dependency version, and complete workflow step log |

## Authority boundary

QA owns independent test design, execution, interpretation, finding disposition, and certification. This guide does not authorize merge, canonical designation, Registry publication, release, or runtime activation.
