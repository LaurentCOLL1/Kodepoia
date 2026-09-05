# Kodepoia release candidate notes

> This template is release metadata for the deterministic R18.2 bundle. It does not publish a
> GitHub Release and it does not authorize production signing or WinGet submission.

## Release identity

- Product: `${product}`
- Public version: `${public_version}`
- Channel: `${channel}`
- Exact source SHA: `${source_sha}`

## Summary

Describe the user-visible changes included in this release candidate.

## Validation evidence

Record the evidence produced from the exact source SHA:

- release bundle manifest SHA-256;
- release bundle semantic SHA-256;
- installer SHA-256 and byte size;
- GitHub Actions workflow/run identifiers;
- two-build comparison outcome;
- clean install, packaged UI smoke, and uninstall outcome.

## Known limitations

Record platform-controlled non-determinism separately from the deterministic unsigned payload boundary.
Installer binary equality is measured and reported; it is never assumed.

## Distribution status

- Production signing: **NOT TRIGGERED**
- Public GitHub Release publication: **NOT TRIGGERED**
- Public WinGet submission: **NOT TRIGGERED**

Those actions belong to later governed R18 subdivisions.
