# Kodepoia v1.0.0rc1 — Security and Operations Runbook

## Secure defaults

The R16.17 migration fixture preserves three explicit defaults: network access is `off`, unknown plugin trust is denied, and production publication is disabled. Release-readiness evidence must not widen these defaults. Production credentials are not required or consumed by core RC acceptance, and publication/signing/provider-domain cutover remain conditional manual actions.

## Backup, migration and rollback

Before a supported release-state migration, create a repository-owned backup with `BackupManager` and verify its manifest, paths, sizes and SHA-256 values. R16.17 migrates only the declared prior fixture (`0.1.0a4`, schema 1) to `1.0.0rc1` (schema 2). The write is atomic. If a migration fails after the state write, restore the verified pre-migration archive and verify that the prior state returns byte-for-byte. Do not promote a partially migrated state.

## Incident response

If release evidence, a package checksum, migration state, workflow provenance, BOM binding, or repository authority is inconsistent, stop promotion and treat the candidate as non-authoritative. Preserve the failing exact SHA and evidence, revoke or quarantine any affected candidate artifact, restore from a verified backup where state changed, and re-run the relevant exact-head authority after repair. Never reuse a PASS from a different SHA.

If a credential or plugin is suspected to be compromised, disable or revoke the corresponding external credential/plugin authority outside the RC artifact, invalidate cached authorization where applicable, and re-run the repository security/provenance gates. Do not write live credential values into release reports, manifests, logs, command lines, documentation, or fixtures.

## Publication and signing

Core R16.17 produces an unsigned candidate only. Production signing, store submission, public registry publication, production credentials, and provider/domain cutover require explicit authorization. If any is requested, R16.17 manual state becomes triggered and completion must stop until the exact signing/publication target, credential scope, resulting artifact identity, provenance, and verification evidence are recorded.

## Recovery and operator checks

Verify the exact source SHA, package SHA-256 values, build-manifest evidence digest, BOM evidence digest, supply-chain evidence digest, migration backup verification, rollback result, and release documentation hashes before promotion. Public publication must never be inferred from artifact upload to GitHub Actions: Actions artifacts are acceptance evidence, not a release channel.
