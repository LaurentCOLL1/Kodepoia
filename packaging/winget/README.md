# Kodepoia WinGet readiness (R18.9)

This directory documents the governed Windows Package Manager readiness surface.
Generated manifests are emitted by `python -m kodepoia.release.winget`; generated files are evidence artifacts and are not committed as release authority.

## Manifest set

R18.9 emits the current multi-file shape using `ManifestVersion: 1.12.0`:

- `LaurentCOLL1.Kodepoia.yaml` (`version`)
- `LaurentCOLL1.Kodepoia.installer.yaml` (`installer`)
- `LaurentCOLL1.Kodepoia.locale.fr-FR.yaml` (`defaultLocale`)
- `LaurentCOLL1.Kodepoia.locale.en-US.yaml` (`locale`)

The installer contract is `inno`, `x64`, user scope, `UpgradeBehavior: install`, with explicit Inno silent switches consistent with `packaging/windows/Kodepoia.iss`.

## Readiness versus publication

Ordinary R18.9 CI generates an explicitly non-publishable preview. The preview uses the reserved `.invalid` host and carries the exact SHA-256 of the installer that was tested. It must never be submitted to the public WinGet repository.

A manifest may be marked publishable only when all of these independent facts are explicitly verified:

1. the public Kodepoia GitHub Release exists;
2. that release is verified immutable;
3. the installer URL is exactly the version-specific Kodepoia release asset URL;
4. the exact installer SHA-256 is bound;
5. production signing is verified.

The generator has no public-submission implementation and always reports `public_submission_performed=false`.

## Local validation

When `winget` is available, validate the generated multi-file directory without interaction:

```powershell
winget validate --manifest <manifest-directory> --disable-interactivity
```

The R18.9 acceptance workflow attempts this command on the Windows runner. If the runner does not expose `winget`, the report records `UNAVAILABLE`; it does not fabricate a PASS. Internal mapping/schema consistency tests remain mandatory either way.

Public submission to `microsoft/winget-pkgs` is a separate effect boundary and is **CONDITIONAL / NOT TRIGGERED** in ordinary R18.9 acceptance. No WinGetCreate/YAMLCreate auto-submit path is used.
