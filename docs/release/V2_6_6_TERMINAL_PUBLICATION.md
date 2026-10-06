# V2.6.6 — Governed public release and live updater activation

Status: **COMPLETE + NORMALIZED — TERMINAL V2 CLOSURE**

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

At V2.6.6 entry, live production metadata was Root v2 / Targets v8 / Snapshot v10 /
Timestamp v10, Snapshot/Timestamp were expired and fail closed, and no public stable
`v1.1.0` tag or GitHub Release yet existed. That observation is retained as historical
pre-transition input; the terminal production state is recorded below.

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

## Terminal production publication and live closure

The preparatory state above is historical entry-state truth. The terminal V2.6.6 state is now:

- production TUF: Root v2 / Targets v9 / Snapshot v11 / Timestamp v11;
- public stable tag `v1.1.0` -> `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- public GitHub Release `Kodepoia 1.1.0` (ID `404195689`), published and non-prerelease;
- exactly one public `KodepoiaSetup.exe`, 38,834,833 bytes, SHA-256 `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- stable target exact-source/hash/length binding preserved with `authenticode_policy=allow-unsigned`;
- production Authenticode remains unsigned and no signing trust is claimed;
- WinGet remains OUT.

Terminal read-only closure PR `#574` qualified 47/47 exact-head workflows on `1e176b613695d2b7b5302a1acc2b60e45cce4d48` and merged as `fdede7f5eab314e322c9f97521652114ea194309`.

`V2.6.6 Live Updater Closure` run `37473587610` succeeded on that exact `main`. Artifact ID `11418815205` contains `V2_6_6_LIVE_UPDATER_CLOSURE.json`, which records 9/9 PASS, `critical_veto=false`, `go_no_go=GO`, `summary.failed=[]`, `public_network_proof=true`, TUF 2/9/11/11, `production_metadata_mutated=false`, `public_release_mutated=false`, `winget_submission=false`, and logical evidence SHA-256 `614a3f564b0897b5f4a0eb32e295b408d0f225b6152190247434afccd99a51ed`.

The workflow proved the real public installed updater sequence `v1.1.0-rc8 -> 1.1.0`, exact stable transport verification, real installer upgrade/relaunch, installed `DisplayVersion=1.1.0`, custom install-directory preservation, a subsequent live `up-to-date` result, packaged smoke and uninstall.

V2.6.6 is **COMPLETE + NORMALIZED**. This is the terminal V2 closure; V2 is completely finished and no V2.7 is authorized.
