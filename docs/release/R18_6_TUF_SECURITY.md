# R18.6 — TUF-secured update repository and metadata lifecycle

## Scope

R18.6 adds a fail-closed TUF trust layer and a product-level update trust adapter. It does not publish a GitHub Release, sign production artifacts, submit anything to WinGet, silently install software or claim that synthetic acceptance keys are production trust anchors.

The implementation uses maintained Python packages:

- `tuf>=7,<8` for TUF metadata parsing and verification primitives;
- `securesystemslib[crypto]>=1.4,<2` for isolated Ed25519 acceptance signing.

`src/kodepoia/release/tuf_security.py` owns the cryptographic metadata verification primitive. `src/kodepoia/update/trust.py` owns channel/platform target selection, transport isolation, bootstrap pinning, verified-candidate caching and non-blocking offline behavior. `src/kodepoia/update/bootstrap.py` owns fail-closed loading of the embedded synthetic trust-anchor resource.

## TUF top-level roles

Synthetic repositories contain the four required TUF top-level roles:

- `root.json` — trusted keys and signature thresholds;
- `targets.json` — authorized target path, length and SHA-256;
- `snapshot.json` — version/hash/length binding for `targets.json`;
- `timestamp.json` — freshness plus version/hash/length binding for `snapshot.json`.

The verifier persists trusted root/timestamp/snapshot/targets metadata plus compact trusted state. A restarted verifier restores this state before evaluating a new repository view.

## Fail-closed verification order

`TufUpdateVerifier` performs all checks before replacing trusted state:

1. load an explicit bootstrap root or already persisted root;
2. reject root rollback, changed same-version root, or non-sequential root updates;
3. require a new root to satisfy the previous root threshold;
4. require the candidate root to satisfy its own threshold;
5. verify timestamp, snapshot and targets roles against the candidate root;
6. evaluate metadata expiration against the injected UTC verification clock;
7. reject timestamp, snapshot or targets rollback against persisted state;
8. require timestamp → snapshot version/hash/length agreement;
9. require snapshot → targets version/hash/length agreement;
10. require the selected target to be explicitly authorized in targets metadata;
11. verify target length and SHA-256;
12. atomically persist trusted metadata/state only after every check succeeds.

A failed refresh never promotes candidate metadata or target bytes into trusted state.

## Product update trust contract

`UpdateTargetSpec` binds an update to all of:

- release channel (`stable`, `beta`, or `nightly`);
- platform identifier;
- public release version;
- exact 40-character source commit SHA;
- target filename.

The resulting target path is therefore channel/platform/version/source specific. A target authorized for one channel is not silently reused for another channel.

`UpdateTransport` is treated as untrusted. `MemoryUpdateTransport` is the deterministic acceptance implementation; its metadata and target responses are not accepted until TUF verification completes.

`UpdateClient` persists only the last verified candidate. On network/transport unavailability it returns `offline-cached` when a previous verified candidate exists, or `offline-no-cache` otherwise. Verification failures are reported separately and do not replace the trusted candidate.

## Root rotation

Root updates are sequential. A rotated root must be signed by the threshold of the previously trusted root and by the threshold of the new root. The positive rotation test creates a version 2 root with new root keys and signatures from both old and new threshold sets; the verifier advances trusted root state only when both checks pass.

## Packaged trust-anchor evidence

The source package contains `trusted_root.synthetic.json` plus `trusted_root.synthetic.manifest.json`. The embedded root is version 1, uses a 2-of-2 root threshold, and is digest-pinned to:

`885bc87c3a5e9fe8b378cac85eb89fc37f99fcd8ba0bc7c494ee1e407da96670`

`load_synthetic_packaged_root()` refuses to load this resource unless `allow_synthetic=True` is explicitly supplied. On opt-in it validates the manifest schema/purpose, root version, SHA-256, root metadata type and root self-signature threshold.

The anchor is explicitly `synthetic-acceptance-only`:

- no production trust claim is made;
- private acceptance keys are not persisted;
- production key custody/hosting is outside core R18.6 acceptance;
- runtime code must not silently treat a synthetic root as a production trust anchor.

The acceptance workflow also generates a fresh independent synthetic root as evidence that isolated repository keys can be produced without persisting private keys.

A production root, if later provisioned, must be distributed out-of-band as trusted application/package data, ideally from a read-only application/system location, and must retain the same fail-closed version/digest semantics. It must not be sourced from the writable metadata cache.

## Acceptance matrix

### Core TUF cases

| Case | Expected |
| --- | --- |
| valid update from trusted state | PASS |
| rollback of `timestamp` | REFUSED |
| rollback of `snapshot` | REFUSED |
| freeze with expired metadata | REFUSED |
| `targets.json` referenced by a wrong digest | REFUSED |
| new `root` without its required signature threshold | REFUSED |
| trusted state restored after verifier restart | PASS |

### Product update cases

| Case | Expected |
| --- | --- |
| channel/platform/source-bound installer refresh | PASS |
| compromised mirror target payload | REFUSED |
| target requested from wrong channel | REFUSED |
| root-key rotation satisfying old + new thresholds | PASS |
| offline check returns last verified candidate | PASS |
| repository bootstrapped from a different packaged root pin | REFUSED |
| embedded synthetic root resource loads only with explicit opt-in | PASS |

The focused unit suite additionally covers offline-without-cache, embedded-root default refusal and a bad timestamp → snapshot hash/length reference.

## Deterministic time

Acceptance uses the fixed UTC verification instant `2026-09-05T12:00:00+00:00`, so expiry verdicts do not depend on a CI runner wall clock.

## CI evidence

`.github/workflows/r18-6-tuf-acceptance.yml` runs on Ubuntu and Windows and checks out the exact evidence SHA. It compiles and lints the focused cryptographic/update sources, executes all focused R18.6 test modules, emits fresh synthetic-root evidence and emits `artifacts/r18_6/tuf-acceptance.json`.

The workflow requires:

- 7/7 core TUF cases;
- 7/7 product update cases;
- embedded root version/digest/purpose validation;
- trusted-state persistence;
- channel/platform binding;
- non-blocking offline cache behavior;
- synthetic packaged-root evidence with no production-trust claim;
- no network requirement for synthetic acceptance;
- no persisted production/private acceptance keys;
- no public GitHub Release, production signing or public WinGet submission.

## Completion gates

R18.6 is not complete from the focused workflow alone. The exact END head must also pass:

- R18.6 specialized acceptance on Ubuntu and Windows;
- R0 Repository Guard;
- full Python Core;
- KodeStudio UI Smoke;
- R16.9 supply-chain governance after registering the R18.6 workflow as immutable authority.

Only after those exact-head gates may the END-sync be recorded and revalidated, PR #393 merge with exact-head protection, and the unique post-merge continuity normalization run. R18.7 must not start before that normalization is green.
