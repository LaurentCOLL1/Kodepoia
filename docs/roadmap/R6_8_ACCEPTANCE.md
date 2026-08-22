# R6.8 — KodeCI + KodeBuild foundation — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** CONDITIONAL — **NOT TRIGGERED**

## Accepted implementation identity

- starting normalized main: `fc7bd4d5803c451b4d343d08bcc212868ad24412`;
- implementation branch: `feature/r6-8-ci-build`;
- accepted implementation head: `d632669b93fda7b8397b9c3de43d78ca8726323f`;
- implementation PR: #47;
- implementation merge: `d570a3930ee63802882b8682e4532004d4fd81d6`;
- post-merge normalization PR: #48;
- normalized main merge: `92effbde1e432a8fcb6c794038d77367d034bcb0`.

## Acceptance matrix

| Gate | Required | Result |
| --- | --- | --- |
| Stable CI check IDs | yes | PASS |
| queued/in-progress/pass/fail/cancelled/skipped/unknown semantics | yes | PASS |
| required skipped/cancelled never PASS | yes | PASS |
| CI exact source-SHA binding | yes | PASS |
| CI derived counts/blockers + evidence hash | yes | PASS |
| CI R6.3 adapter | yes | PASS |
| `.kodepoia/workflows/` confinement | yes | PASS |
| Build source SHA/platform/Python/backend identity | yes | PASS |
| source-input SHA-256 | yes | PASS |
| dependency-input SHA-256 | yes | PASS |
| artifact name/size/SHA-256 | yes | PASS |
| wheel structural validation | yes | PASS |
| sdist structural validation | yes | PASS |
| missing/invalid required artifact blocks | yes | PASS |
| recursive secret redaction | yes | PASS |
| build derived fields + evidence hash | yes | PASS |
| `.kodepoia/releases/` confinement | yes | PASS |
| Health `build` adapter | yes | PASS |
| stable R6.3 build cases | yes | PASS |
| CI/build JSON Schemas | yes | PASS |
| existing R0/Python/UI semantics preserved | yes | PASS |
| package build on Ubuntu hosted | yes | PASS |
| package build on Windows hosted | yes | PASS |
| package/evidence upload on both platforms | yes | PASS |
| hosted artifacts inspected | yes | PASS |
| conditional local Windows gate explicitly evaluated | yes | PASS — NOT TRIGGERED |
| R0 final head Windows+Ubuntu | yes | PASS |
| Python Core final head Windows+Ubuntu | yes | PASS |
| KodeStudio UI Smoke final head | yes | PASS |
| implementation PR merge | yes | PASS |
| post-merge normalization | yes | PASS — PR #48 merge `92effbde1e432a8fcb6c794038d77367d034bcb0` |

## Final hosted CI evidence — exact implementation head

Accepted head: `d632669b93fda7b8397b9c3de43d78ca8726323f`.

- R0 Repository Guard `32571710663` / #783 — SUCCESS Windows + Ubuntu;
- Python Core `32571710718` / #757 — SUCCESS;
  - `python-core-ubuntu-latest` — SUCCESS;
  - `python-core-windows-latest` — SUCCESS including PowerShell acceptance-runner syntax;
  - integrated `kodestudio-ui-windows` — SUCCESS;
  - `package-build-ubuntu-latest` — SUCCESS;
  - `package-build-windows-latest` — SUCCESS;
- KodeStudio UI Smoke `32571710650` / #724 — SUCCESS Windows.

Both package jobs explicitly checked out the same exact evidence source SHA `d632669b93fda7b8397b9c3de43d78ca8726323f`, not the pull-request synthetic merge ref.

## Ubuntu package evidence

Environment:

- runner: Ubuntu 24.04.4 (`ubuntu-24.04`);
- Python: `3.12.14`;
- source SHA: `d632669b93fda7b8397b9c3de43d78ca8726323f`;
- build backend: `hatchling.build`.

Validated package evidence:

- wheel `kodepoia-0.1.0a4-py3-none-any.whl` — 168,238 bytes — SHA-256 `35489ed602a9ade3816a4562f5cd751fbfb8924cd8ad780fba5bc7aa26a2a095` — validated;
- sdist `kodepoia-0.1.0a4.tar.gz` — 247,776 bytes — SHA-256 `b803d3f316f46ea461af853240ba8ab8bf3f867e0cff8e88e70f87bf678c1a78` — validated;
- source-input digest SHA-256 `350d3ca254e75f8e34f9d020df82b9a1e0165a409119dd51c3d7e0ed4fce12ba`;
- build evidence SHA-256 `57e11b0a66e1f40d9984ae7aeacbe3874df5ce7b005657a72e6e603a63f983d8`;
- CI evidence SHA-256 `1a9f0e6dc0c099d5a7d9336d97a1e53ec40563cce90ba2a8c56e80b2eeb58869`;
- build status PASS, CI status PASS, zero blockers;
- GitHub Actions artifact `kodepoia-build-ubuntu-latest`, ID `9475481332`, 411,396 bytes, artifact ZIP SHA-256 `cdeef82ace3e0ca2ef0275b3111bf6d2c8f50213b20e777ddb436477e48261d8`.

The downloaded artifact was inspected and contained exactly the expected four evidence/package files: wheel, sdist, `.kodepoia/releases/ubuntu-latest/latest.json`, and `.kodepoia/workflows/r6-8-package-build/latest.json`.

## Windows package evidence

Environment:

- runner: Microsoft Windows Server 2025 10.0.26100 (`windows-2025-vs2026` hosted image);
- Python: `3.12.10`;
- source SHA: `d632669b93fda7b8397b9c3de43d78ca8726323f`;
- build backend: `hatchling.build`.

Validated package evidence:

- wheel `kodepoia-0.1.0a4-py3-none-any.whl` — 169,444 bytes — SHA-256 `1406f5a2f180b56c611fb3a0cd8a9d23436682903405f52dadc26257c5b676fb` — validated;
- sdist `kodepoia-0.1.0a4.tar.gz` — 249,797 bytes — SHA-256 `42e63403069e61235cefa71ebbc4099b5e717e1528a6eae54ef0673f20e69edd` — validated;
- source-input digest SHA-256 `427ffd8f815dac4972b894752c36ca048957aad72556f7a25ac482d4d1672090`;
- build evidence SHA-256 `248d49db9badfea775d18ca4087eb56ba053c961f888d5641dc42e62c6d8f419`;
- CI evidence SHA-256 `47ffad9f7f1d2c7af14efdc0f71e065b6b556046404069f2f02ef8b353024160`;
- build status PASS, CI status PASS, zero blockers;
- GitHub Actions artifact `kodepoia-build-windows-latest`, ID `9475485133`, 414,597 bytes, artifact ZIP SHA-256 `aae159bd0d8a04ee4cec6c65f7a20f104c4679a9081432640419c4a6e74ccbe5`.

The downloaded artifact was inspected and contained exactly the expected four evidence/package files: wheel, sdist, `.kodepoia/releases/windows-latest/latest.json`, and `.kodepoia/workflows/r6-8-package-build/latest.json`.

## Reproducibility interpretation

R6.8 intentionally does not claim byte-identical Windows/Ubuntu archives. The runner Python versions, archive metadata and checkout text representation may legitimately differ across platform images. Exact immutable source identity is the accepted Git SHA; the source/dependency-input digests capture the bytes seen by each build environment, and each resulting artifact receives its own SHA-256. Cross-platform digest differences are therefore recorded evidence rather than silently normalized or mislabeled as a build regression.

No SLSA level is claimed. GitHub artifact attestations were reviewed as provenance context but were not made a mandatory frequent-PR-build gate.

## Conditional manual gate — final decision

**NOT TRIGGERED.**

Hosted Windows on the exact final implementation head successfully:

1. checked out the exact source SHA;
2. installed the declared build frontend/backend inputs;
3. built wheel + sdist;
4. structurally validated both archives;
5. recorded source/dependency/artifact hashes;
6. emitted build and CI PASS reports with zero blockers;
7. uploaded the package/evidence bundle;
8. allowed the uploaded bundle to be downloaded and independently inspected.

There is therefore no acceptance-critical Windows behavior left unproven by hosted CI, and requesting a user-local run would add no evidence required by the accepted R6.8 plan.

## Failure recovery / anti-regression

- Required `skipped` or `cancelled` checks must never become PASS.
- Missing wheel/sdist or failed archive validation remains blocking.
- Do not require cross-platform byte identity unless a later explicit reproducible-build contract defines normalized inputs/toolchains.
- Do not persist secrets merely to enrich build provenance.
- Do not remove/narrow R0, Python Core or UI checks to keep package builds green.
- The package collector must not expose arbitrary model-supplied commands, executables, cwd or output paths.
- Package-build checkout must remain bound to the same source SHA recorded in build/CI evidence.

## Post-merge normalization evidence

PR #48 head `0580f930d6dfaa387c1eda1cf8ad56de79cc42b9` passed:

- R0 #790 `32572054011` — SUCCESS;
- Python Core #764 `32572054001` — SUCCESS including both core OS jobs, integrated UI and both package-build jobs;
- KodeStudio UI Smoke #731 `32572054015` — SUCCESS;
- merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`.

## Completion record

R6.8 implementation accepted and merged as PR #47 / `d570a3930ee63802882b8682e4532004d4fd81d6`. Post-merge normalization PR #48 is also accepted and merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`. **R6.8 is COMPLETE and R6.9 is NEXT / NOT STARTED.**
