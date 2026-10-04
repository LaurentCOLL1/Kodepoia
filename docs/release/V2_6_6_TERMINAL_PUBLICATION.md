# V2.6.6 — Governed public release and live updater activation

Status: **IMPLEMENTATION — OFFLINE TARGETS AUTHORITY PREPARATION**

V2.6.6 is the terminal V2 release subdivision. Its frozen public inputs are:

- version/tag: `1.1.0` / `v1.1.0`;
- exact candidate source: `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- installer: `KodepoiaSetup.exe`;
- installer size: `38,834,833` bytes;
- installer SHA-256: `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- stable target:
  `channels/stable/windows-x86_64/1.1.0/46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe`;
- target policy: `authenticode_policy=allow-unsigned`;
- accepted V2.6.4 transition request:
  `a44914e80fb2fafb6b03f2a9847a78805b1ccb2a87fafedae9199f66c88bacea`;
- accepted V2.6.5 publication-input digest:
  `7c0085dcce704fe19c54f4f175b28518ec86c38888f0b87c063add908c53d416`.

The current live production metadata remains Root v2 / Targets v8 / Snapshot v10 /
Timestamp v10. Root and Targets remain within their authority lifetime; Snapshot and Timestamp
remain expired and fail closed. The public stable target is not yet authorized. No public
`v1.1.0` tag or GitHub Release exists at the start of V2.6.6.

## Split signing boundary

Targets authority is intentionally offline and must never be moved into GitHub Actions or serialized
into repository content. Snapshot/Timestamp are separate low-authority online signers held in the
GitHub environment `tuf-production-signing`.

V2.6.6 therefore uses two distinct signing phases.

### Phase A — offline Targets preparation

The accepted ceremony runner supports `--offline-targets-only`. This mode:

- verifies the existing Root/Targets/Snapshot/Timestamp chain before mutation;
- requires the existing authorized Targets custody and its passphrase;
- verifies the exact frozen candidate size and SHA-256;
- preserves every existing target;
- adds exactly the stable `1.1.0` target and increments Targets v8 -> v9;
- signs Targets with the existing authorized offline role;
- stages only public `targets.json`;
- does not resolve Snapshot/Timestamp secrets;
- does not modify repository metadata;
- rejects combination with `--apply`;
- emits a shareable report containing no private material or key path.

This is the first unavoidable manual operator boundary of V2.6.6.

### Phase B — governed online/public transition

Phase B is not authorized to consume an arbitrary or unsigned Targets file. It must first verify the
Phase-A public Targets v9 against Root v2 and against the exact frozen transition request.

Only after that verification may the approved `tuf-production-signing` environment create fresh,
monotonic Snapshot v11 / Timestamp v11 bound to Targets v9. Public release/tag/asset publication,
metadata merge, public re-fetch, live rc8 -> stable updater proof, post-upgrade stable-current proof
and terminal closure must remain fail-closed and exact-source bound.

## Effect boundary of this preparatory change

The repository change that introduces Phase A performs no live effect. It does not:

- sign production Targets during PR CI;
- consume any private Targets material in CI;
- consume Snapshot/Timestamp GitHub secrets;
- create or repoint `v1.1.0`;
- create a GitHub Release;
- upload a public asset;
- modify production TUF metadata;
- activate the live updater;
- claim Authenticode trust;
- submit WinGet.

V2.6.6 remains incomplete until the manual Phase-A public output is returned, verified, and the
subsequent governed live transition and installed updater validation succeed.
