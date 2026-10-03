# V2.6.3 — Exact-source Windows release candidate, SBOM, provenance and signing truth

Status: **IMPLEMENTATION / QUALIFICATION — NO PUBLICATION AUTHORITY**

V2.6.3 converts the already frozen terminal identity into an exact-source candidate.
It is release packaging and release evidence only. It does not add product capability.

## Identity boundary

The source candidate uses the V2.6.1 successor identity:

- product: `Kodepoia`;
- public/installer version: `1.1.0`;
- PEP 440 version: `1.1.0`;
- channel: `stable`;
- build type: `release`;
- tag identity: `v1.1.0`;
- source binding: `exact-head`.

The last public distribution remains `v1.1.0-rc8` until V2.6.6 publication succeeds.
Promoting the source identity in V2.6.3 is not a public release effect.

## Candidate evidence

The exact PR head is the candidate source authority. The Windows qualification must:

1. build `KodepoiaSetup.exe` from that exact SHA;
2. record installer SHA-256 and byte length in the installer manifest;
3. generate SPDX 2.3 SBOM and release provenance for the same SHA;
4. build an evidence-bound release ZIP with the existing R18 bundle contract;
5. build a second installer/bundle and run the existing R18.2 two-build comparison;
6. inspect Authenticode truth without provisioning production signing secrets;
7. perform clean custom-directory install, packaged smoke and uninstall;
8. create a staged R18.5 GitHub-release description bound to the exact evidence;
9. emit a V2.6.3 candidate report that freezes the candidate source SHA.

Binary equality is measured, not assumed. The existing R18 contract requires semantic
equivalence and reports installer/archive binary equality independently.

## Authenticode and attestation truth

Production Authenticode signing is still not verified and secret provisioning is not
authorized. The mandatory pull-request candidate therefore records the observed unsigned
state. Test-signing evidence remains a separate historical R18.4 capability proof and must
never be converted into a production trust claim.

GitHub artifact-attestation verification is used only where the execution context can
truthfully provide it. Pull-request staging uses the existing `synthetic-offline`
attestation receipt semantics and records `live_verified=false`. It does not fabricate a
live GitHub attestation.

## Staging boundary

The staged release description must be:

- state `staged`;
- tag `v1.1.0`;
- target commit equal to the exact candidate SHA;
- draft-only;
- bound to the candidate bundle, signing evidence and attestation receipt;
- bound to a snapshot stating that the public tag/release is not being reused;
- `publication_triggered=false`.

The workflow has read-only repository contents permission and performs no GitHub Release
write.

## Production TUF boundary

V2.6.3 does not create a stable target in the live production update repository. The
observed expired snapshot/timestamp metadata remains fail-closed. Production TUF
transition preparation belongs to V2.6.4.

## Definition of done

V2.6.3 is complete only after:

- exact-head synthetic acceptance passes on Ubuntu and Windows;
- the dedicated Windows candidate workflow produces the real candidate evidence;
- installer, bundle, SBOM, provenance and signing evidence all bind the same SHA;
- the two-build comparison passes the accepted R18 semantic contract;
- clean install, packaged smoke and uninstall pass;
- staged release evidence is exact-source and non-publishing;
- all pull-request workflows on the unchanged head succeed;
- the implementation PR merges with `expected_head_sha`;
- post-merge normalization freezes that exact PR head as the V2.6.3 candidate source and authorizes V2.6.4 only.

No GitHub Release, public tag, public asset, production TUF mutation, live updater activation,
signing-secret provisioning or WinGet submission is authorized by V2.6.3.
