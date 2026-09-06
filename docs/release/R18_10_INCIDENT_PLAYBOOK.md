# R18.10 — Release/update incident response playbook

This playbook defines the **authoritative synthetic drill boundary** for R18.10. It does not authorize a real certificate revocation, a production TUF key rotation, a GitHub release/tag/asset deletion, an attestation deletion, or a public WinGet submission.

## Principles

1. Fail closed at every trust boundary. A release or update with compromised signing evidence, stale/rolled-back TUF metadata, expired metadata, a withdrawn/superseded directive, or mismatched payload bytes is not installable.
2. Preserve normal Kodepoia project work. Update/release incident handling must not modify workspaces, Project DNA, user assets, local model data or unrelated application state.
3. Preserve a last-known-good recovery path. A failed or rejected update must not erase the previously accepted installer reference needed for recovery.
4. Separate local evidence from provider-side effects. Synthetic CI records what a production incident operator would need to do, but reports those actions as `NOT_EXECUTED`.
5. Never treat provenance as a security verdict by itself. Build/release attestations remain provenance/integrity evidence and must be combined with signing, release, TUF and payload verification.

## Incident classes and required local verdicts

| Incident | Local authoritative verdict | Recovery/effect boundary |
| --- | --- | --- |
| Signing certificate/thumbprint declared compromised | BLOCK | Provider certificate revocation is conditional and not executed by core drills. |
| Valid sequential TUF Root rotation | ALLOW | New Root must satisfy old and new trust requirements; production key custody is external. |
| Root/Timestamp/Snapshot/Targets rollback | BLOCK | Persist the previously trusted state. |
| Expired Timestamp or other TUF metadata freeze | BLOCK | Continue normal application work; do not silently accept stale metadata. |
| Trusted release marked withdrawn | BLOCK | Keep last-known-good recovery available. |
| Trusted incident directive supersedes a release | BLOCK old candidate | Surface `update-superseded`; require the replacement to pass the normal trusted update path independently. |
| Hosted release asset differs from TUF-authorized bytes | BLOCK | Delete/re-publish provider assets only through a separately authorized incident action. |
| Candidate install/handoff fails | RECOVER | Preserve the previous installer/version reference and project data. |

## TUF key compromise procedure

TUF defines Root, Targets, Snapshot and Timestamp as the required top-level roles. Metadata is signed, versioned and expiring. If a Timestamp, Snapshot, Targets or Root key is compromised, repository maintainers replace the affected key through newly signed Root metadata. If enough Root keys are compromised to meet the Root threshold, the new Root must be re-issued out of band. R18.10 simulates these cases only with synthetic in-memory keys and repositories.

Official references rechecked for R18.10 START:

- https://theupdateframework.io/docs/faq/
- https://theupdateframework.io/docs/security/
- https://theupdateframework.io/docs/metadata/

## Windows signing compromise procedure

R18.4 remains authoritative for Authenticode truth. R18.10 adds a local deny policy over already structured signing evidence so a thumbprint declared compromised is blocked even when a historical synthetic signature record was otherwise valid. Microsoft documents that `SignTool verify` determines whether the signing certificate chains to a trusted authority and whether it has been revoked.

Official reference:

- https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool

A real CA revocation request, certificate replacement or production timestamp/signing action is a provider-side operation and is not executed by the synthetic drill runner.

## GitHub release and attestation incident procedure

A published immutable GitHub release locks its associated tag and release assets. Deleting an immutable release can later permit deletion of the tag, but the same tag name cannot be reused. Immutable releases also create release attestations binding tag, commit and assets. GitHub separately supports lifecycle management of artifact attestations, including deleting attestations for artifacts consumers should no longer trust.

Official references:

- https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
- https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/manage-attestations

R18.10 records the following possible provider actions but keeps them `NOT_EXECUTED`: withdraw/delete a public release, delete a public tag/asset where platform rules permit it, delete an obsolete/untrusted artifact attestation, and publish a corrected superseding release.

## WinGet incident boundary

R18.9 remains the WinGet readiness authority. A bad package must be superseded/withdrawn according to the public repository's current process only after explicit authorization. R18.10 never opens a public `microsoft/winget-pkgs` pull request automatically.

## User communication evidence

A production incident record should identify the affected version, release channel, source SHA, installer digest, signing identity, TUF metadata versions, incident classification, safe replacement/recovery version and whether users must take action. No secret, certificate private key, token, password or unredacted credential belongs in this evidence.

## Acceptance evidence

`scripts/r18_10_acceptance.py` emits a deterministic JSON report containing exact source SHA, scenario IDs, expected/actual verdicts, critical bypass count, provider-effect count and report digest. Authoritative acceptance requires:

- `status == PASS`;
- `critical_bypass_count == 0`;
- `provider_effect_count == 0`;
- `project_data_mutation == false`;
- all provider-side actions recorded as `NOT_EXECUTED`;
- last-known-good recovery available after the synthetic failed-update scenario.

Any unexpected critical acceptance keeps R18.10 incomplete.
