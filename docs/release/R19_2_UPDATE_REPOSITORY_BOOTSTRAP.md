# R19.2 — Production/Beta Update Repository Bootstrap

## Status

Repository-safe bootstrap: **implemented**.

Real beta/release trust anchor: **pending manual real-key bootstrap**.

R19.3 is not started by this subdivision.

## Canonical public endpoints

Kodepoia uses a repository-backed HTTPS metadata endpoint:

```text
https://raw.githubusercontent.com/LaurentCOLL1/Kodepoia/main/update-repository/metadata/
```

The four top-level TUF metadata files are published at fixed names:

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

TUF metadata is the authorization source. GitHub Release hosting alone does not authorize an
installer.

The logical TUF target path is:

```text
channels/<channel>/windows-x86_64/<public_version>/<source_sha>/KodepoiaSetup.exe
```

Each target binding carries:

- target length;
- SHA-256;
- exact source SHA;
- channel;
- public version;
- release-note summary;
- signing status;
- provenance status;
- withdrawal state;
- canonical HTTPS payload URL.

## Top-level roles and key policy

| Role | Threshold | Storage policy | Metadata expiry | Planned rotation |
| --- | ---: | --- | ---: | ---: |
| Root | 2 | offline | 365 days | 180 days |
| Targets | 1 | offline | 365 days | 180 days |
| Snapshot | 1 | online, separate key | 1 day | 90 days |
| Timestamp | 1 | online, separate key | 1 day | 30 days |

Every role uses a distinct key scope. Root and Targets keys must remain outside the online
repository workflow. Snapshot and Timestamp may be automated, but their private keys must still
be held in an approved secret store and must never be committed, uploaded as release assets, or
included in CI artifacts.

The initial production Root should use at least three independent Root keys with a 2-of-3
threshold. That gives operational room to lose one Root key without reducing the required
threshold.

## Compatibility policy

R19.2 sets `consistent_snapshot` to `false`.

The R18 update/discovery clients already fetch the fixed metadata names `root.json`,
`timestamp.json`, `snapshot.json`, and `targets.json`. R19.2 preserves that established client
contract. A later change to consistent-snapshot naming would require an explicit client migration
and Root metadata update; it is not silently introduced here.

## Trust-anchor separation

The R18 resource:

```text
src/kodepoia/update/trusted_root.synthetic.json
```

remains **synthetic acceptance only**.

Production uses a different resource name:

```text
src/kodepoia/update/trusted_root.production.json
```

That file intentionally does not exist during the repository-safe phase. The packaged production
manifest is in state `pending-real-key-bootstrap`, and `load_production_packaged_root()` fails
closed until an active, self-consistent, real-key Root is supplied.

The production loader also refuses a Root whose bytes or SHA-256 equal the synthetic R18 Root.

## Repository layout

Before real signing, only repository-safe policy and documentation are versioned:

```text
update-repository/
  README.md
  metadata/
    README.md
```

After the manual trust bootstrap, the public metadata directory will contain:

```text
update-repository/
  metadata/
    root.json
    targets.json
    snapshot.json
    timestamp.json
```

No private key file belongs anywhere under `update-repository/`.

## Publication sequence

For each beta/release update:

1. build and verify the exact-head release artifact;
2. publish or stage the immutable GitHub Release asset under `v<public_version>`;
3. compute the exact installer SHA-256 and length;
4. create the canonical TUF target path with source/channel/version/status bindings;
5. sign and publish Targets metadata;
6. sign and publish Snapshot metadata that references the exact Targets metadata;
7. sign and publish Timestamp metadata that references the exact Snapshot metadata;
8. retain the current and required historical Root metadata needed for safe sequential rotation.

Clients continue to verify TUF metadata and target bytes before installer execution.

## Expiry and rotation

Metadata must be renewed before expiration. The configured intervals are upper bounds, not a
reason to postpone an urgent rotation.

Planned key rotation:

- Root: prepare a sequential Root version signed to satisfy both the old and new Root thresholds;
- Targets: replace the Targets public key in a newly signed Root, then reissue Targets metadata;
- Snapshot: replace its public key in a newly signed Root, then reissue Snapshot and Timestamp;
- Timestamp: replace its public key in a newly signed Root, then immediately reissue Timestamp.

Every rotation increments the relevant metadata versions and preserves anti-rollback semantics.

## Compromise and recovery

If a Timestamp, Snapshot, or Targets key is suspected compromised:

1. stop metadata publication using that key;
2. preserve incident evidence without copying private-key material into Git or CI artifacts;
3. rotate the compromised role key through a new Root;
4. increment and re-sign affected metadata;
5. publish the replacement metadata only after threshold verification;
6. run the update security acceptance matrix before resuming normal publication.

If fewer than the Root threshold keys remain trustworthy, the repository is no longer sufficient
to repair trust. A new Root must be distributed out of band through a trusted Kodepoia client
release or another independently authenticated recovery channel.

Encrypted backup copies of offline keys must live outside GitHub repository contents, GitHub
Release assets, Actions artifacts/logs, roadmap/continuity files, and ordinary developer
workspaces.

## Manual boundary

The remaining R19.2 step requires real private keys. It must not be automated from repository-safe
fixtures.

Before R19.2 can be marked complete, the operator must:

1. create three independent Ed25519 Root keys for a 2-of-3 Root threshold;
2. create distinct Ed25519 Targets, Snapshot, and Timestamp keys;
3. store Root and Targets private material offline and encrypted;
4. place Snapshot and Timestamp private material only in an approved secret store used by the
   release signing environment;
5. export **public keys only** for repository bootstrap;
6. construct Root v1 with the configured role thresholds and expirations;
7. sign Root v1 with at least two independent Root keys;
8. return only the signed public `root.json` plus public key identifiers/fingerprints for
   verification;
9. never paste, upload, or commit any private key or recovery secret.

Once that material exists, the production manifest can be activated with the exact Root version
and SHA-256, the signed metadata set can be created, and R19.2 can be finalized.
