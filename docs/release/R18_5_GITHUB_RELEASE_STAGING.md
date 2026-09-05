# R18.5 — Immutable GitHub Release staging and promotion

R18.5 defines a fail-closed, exact-source GitHub Release staging boundary. It does **not**
publish a GitHub Release during normal acceptance and it does **not** enable repository
immutability settings.

## Contract

The staging authority binds all of the following before any GitHub write is prepared:

- canonical R18.1 release identity and tag (`v<public_version>`);
- exact 40-hex source commit;
- R18.2 verified release bundle, manifest, payload and semantic digests;
- embedded R18.3 SBOM/provenance evidence;
- an external artifact-attestation verification receipt;
- truthful R18.4 Windows signing evidence;
- exactly one approved public asset: the verified release archive;
- an observed tag/release state proving that the canonical tag and release do not already exist.

The canonical staged document is SHA-256 integrity-bound by `stage_digest`.
Any material change invalidates promotion approval.

## States and effect boundaries

`draft`
: GitHub-side construction state. Assets may be assembled only before public publication.

`staged`
: repository-controlled, offline-verifiable candidate. This is the default R18.5 state.

`published`
: read-only verification state for a release snapshot that already exists. R18.5 acceptance
  does not create this state.

The `prepare-draft` command produces only a **request description** for creation of a draft
release. It performs no HTTP request. The exact `stage_digest` must be supplied again as the
approval token before even that request description is emitted.

Public publication is a separate explicit effect boundary. R18.5 never interprets branch
merge, staging success, draft preparation, a prerelease channel, or an available GitHub API
token as authorization to publish.

## GitHub immutable releases

When repository immutable releases are enabled and a release is published, GitHub locks the
release tag and release assets. R18.5 does not assume that this repository setting is present.
A post-publication snapshot must therefore report the actual `immutable` state. If immutable
publication is required by the promotion decision and the snapshot is mutable, verification
fails closed.

For an authorized future public release, the intended sequence is:

1. create an unpublished draft bound to the exact source SHA;
2. upload only the staged/approved release archive;
3. re-check asset SHA-256 and size;
4. publish only after separate explicit authorization;
5. verify the published release/tag/assets and, when required, immutable status;
6. use GitHub release/asset verification primitives as independent post-publication evidence.

An immutable published release is never edited to replace artifacts. A faulty release must be
superseded and the withdrawal/revocation documented.

## Commands

Stage a verified archive using read-only evidence snapshots:

```text
python scripts/github_release_promotion.py stage \
  --bundle <release.zip> \
  --source-sha <40-hex-sha> \
  --signing-evidence <signing.json> \
  --attestation-receipt <attestation-verification.json> \
  --tag-state <tag-state.json> \
  --output <staged.json>
```

Prepare a draft-only request description from the exact staged candidate:

```text
python scripts/github_release_promotion.py prepare-draft \
  --staged <staged.json> \
  --approved-stage-digest <sha256> \
  --output <draft-request.json>
```

Verify a read-only API snapshot after an explicitly authorized publication:

```text
python scripts/github_release_promotion.py verify-published \
  --staged <staged.json> \
  --release-snapshot <release.json> \
  --require-immutable \
  --output <verification.json>
```

## Acceptance boundary

The dedicated workflow runs on Ubuntu and Windows with `contents: read` only. It compiles and
lints the new sources, runs focused tests, emits 12 deterministic synthetic acceptance cases,
and asserts:

- exact-source staging succeeds;
- source drift fails;
- absent R18.3 evidence fails;
- contradictory signing claims fail;
- missing attestation verification fails;
- unexpected assets fail;
- existing tag/release reuse fails;
- exact stage-digest approval produces only a draft request;
- wrong approval and staged-document tamper fail;
- an immutable published snapshot can be verified;
- required immutability fails closed when absent;
- GitHub API write count remains zero.

Synthetic attestation verification is explicitly labelled `synthetic-offline`; it is not
laundered into a live GitHub attestation claim. Production signing, public GitHub Release
publication, repository immutable-release configuration and WinGet publication remain
conditional and are not triggered by R18.5 core acceptance.
