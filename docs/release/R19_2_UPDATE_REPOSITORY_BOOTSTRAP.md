# R19.2 — Production/Beta Update Repository Bootstrap

## Status

**COMPLETE candidate — real public trust bootstrap active.**

R19.2 establishes the public TUF trust and repository contract required by R19.3. R19.3 is not
started by this subdivision.

## Canonical public endpoints

Metadata is published from the repository over HTTPS:

```text
https://raw.githubusercontent.com/LaurentCOLL1/Kodepoia/main/update-repository/metadata/
```

The fixed top-level metadata names are:

```text
root.json
targets.json
snapshot.json
timestamp.json
```

Installer payloads remain GitHub Release assets:

```text
https://github.com/LaurentCOLL1/Kodepoia/releases/download/v<public_version>/KodepoiaSetup.exe
```

TUF metadata is the authorization source. Hosting a release asset on GitHub never authorizes it by
itself.

The logical target path remains:

```text
channels/<channel>/windows-x86_64/<public_version>/<source_sha>/KodepoiaSetup.exe
```

Future authorized target entries must carry length, SHA-256, exact source SHA, channel, public
version, release-note summary, signing status, provenance status, withdrawal state, and canonical
HTTPS payload URL.

## Active Root v1

The real public Root is packaged at:

```text
src/kodepoia/update/trusted_root.production.json
```

and published identically at:

```text
update-repository/metadata/root.json
```

Pinned identity:

```text
version: 1
sha256: a036c2aac78092f8d46893cc18954bb64f2b998375ff230f996dc4b85157e9ed
root threshold: 2 of 3
consistent_snapshot: false
```

Root key IDs:

```text
a9d16a369682d8b98b1f4a0ad3d3eef5687ef12d8b52ae5e7317a706febe8fc7
ed932929711cebd1f0c2cda9083882c8318b01d8b5d56c7f168182780234406f
0dba49064092a4d21ca06d849467de7411df25fd5d3092a1ee718b5aee619df4
```

Role keys are distinct:

```text
targets:   0a7da4beb6c0173915126a7b5329822fd56554210240296c395dd6e5605ebe35
snapshot:  a5ecff64981b447026163cd232a01b33f5699490067dbe9b49cd30a0f5177a8f
timestamp: 1c08b09dc0cb5216bf3c0f81f34154a2de583eaae97bbe88d9071741c9b45fc5
```

All repository and package material contains public keys only. No private TUF key is permitted in
Git, packages, logs, Actions artifacts, release assets, roadmap files, or continuity files.

## Trust-anchor separation

The R18 acceptance resource remains:

```text
src/kodepoia/update/trusted_root.synthetic.json
```

It is still acceptance-only and still requires explicit synthetic opt-in. Production/beta loading
uses `load_production_packaged_root()` and rejects a Root whose bytes or SHA-256 match the
synthetic Root.

The active production manifest records Root v1 and its exact SHA-256 and explicitly states that no
private key material is persisted.

## Initial signed repository state

The supplied public bootstrap was independently checked before publication:

- Root: 3 valid Ed25519 signatures; threshold 2;
- Targets: valid Targets-role signature;
- Snapshot: valid Snapshot-role signature;
- Timestamp: valid Timestamp-role signature;
- Snapshot reference to Targets: exact version, length, and SHA-256 match;
- Timestamp reference to Snapshot: exact version, length, and SHA-256 match;
- packaged Root bytes equal published `root.json` bytes;
- no private-key PEM, seed, secret, or private-key field was present in the supplied public bundle.

Initial `targets.json` intentionally contains no installer target. R19.5 will publish the corrective
RC target only after its exact release artifact exists and has passed release acceptance.

## Role and expiry policy

| Role | Threshold | Storage policy | Metadata expiry policy | Planned rotation |
| --- | ---: | --- | ---: | ---: |
| Root | 2 | offline | 365 days | 180 days |
| Targets | 1 | offline | 365 days | 180 days |
| Snapshot | 1 | online, separate key | 1 day | 90 days |
| Timestamp | 1 | online, separate key | 1 day | 30 days |

The initial signed Root and Targets expire on `2027-09-07T19:02:56Z`. The initial Snapshot and
Timestamp expire on `2026-09-08T19:02:56Z`. Snapshot/Timestamp therefore require renewal before
that instant. A short Timestamp lifetime is deliberate: clients can detect stale/frozen metadata
quickly. Renewal must increment metadata versions as required and preserve anti-rollback state.

Root and Targets private keys remain offline. Snapshot and Timestamp may be automated later, but
only through approved secret storage; their private material is never repository content.

## Publication sequence for future releases

1. build and accept the exact-head release artifact;
2. publish or stage the immutable GitHub Release asset under `v<public_version>`;
3. compute exact installer SHA-256 and length;
4. create the canonical TUF target path and required custom bindings;
5. sign and publish a newer Targets version;
6. sign and publish Snapshot referencing that exact Targets metadata;
7. sign and publish Timestamp referencing that exact Snapshot metadata;
8. retain Root history required for safe sequential Root rotation.

GitHub's `releases/latest` endpoint is not an authority for Kodepoia beta/RC discovery because it
selects the latest non-prerelease, non-draft release. TUF Targets metadata remains the channel
authority.

## Rotation and compromise recovery

Root rotation must be sequential and satisfy both the old and new Root trust requirements. Role
key replacement is authorized through a newly signed Root, followed by reissue of affected
metadata.

If a Timestamp, Snapshot, or Targets key is suspected compromised:

1. stop publication with that key;
2. preserve incident evidence without copying private material into Git or CI;
3. rotate the role through a new Root;
4. increment and re-sign affected metadata;
5. publish only after threshold and linkage verification;
6. rerun update security acceptance before resuming normal publication.

If fewer than the Root threshold keys remain trustworthy, recovery requires an independently
trusted out-of-band Root distribution through a trusted Kodepoia client release or equivalent
channel.

## R19.2 acceptance boundary

The manual key-generation boundary has been satisfied by receiving **public signed material only**.
R19.2 does not generate, import, persist, or use private production keys in repository automation.

R19.2 is accepted only when exact-head CI proves:

- the production Root loads and is digest-pinned;
- Root self-signature threshold is satisfied;
- Targets/Snapshot/Timestamp signatures verify under that Root;
- Snapshot→Targets and Timestamp→Snapshot hash/length/version bindings verify;
- production and synthetic Roots differ;
- role key scopes are separate and Root is 2-of-3;
- the deterministic repository contract is active and HTTPS-only;
- the wheel embeds the exact production Root and active manifest;
- no private key material enters repository-safe files;
- R19.3 has not been started in the same subdivision.

After R19.2 merge, perform the single continuity-only normalization required by R19 governance
before beginning R19.3.
