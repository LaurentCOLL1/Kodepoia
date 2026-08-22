# Kodepoia — R7.7 acceptance

**Subdivision:** R7.7 — Local STT + frame extraction/analysis hooks  
**Status:** COMPLETE  
**Accepted implementation head:** `04cef94c82fdacafe7313d27c8cf516e8e765295`  
**Implementation PR:** #72  
**Implementation merge:** `8f296c383a28be0055a72a67587422318257aefc`  
**Manual:** REQUIRED — SATISFIED

## Exact-head hosted CI evidence

All hosted gates ran against exact implementation head `04cef94c82fdacafe7313d27c8cf516e8e765295`:

- R0 Repository Guard #997 / run `32594549119`: **SUCCESS**;
- Python Core #971 / run `32594549136`: **SUCCESS**, 5/5 jobs;
- authoritative Ubuntu suite: **443 passed / 4 skipped / 46 warnings**;
- Python Core Windows test job: **SUCCESS**;
- package-build Ubuntu: **SUCCESS**;
- package-build Windows: **SUCCESS**;
- embedded KodeStudio UI job: **SUCCESS**;
- KodeStudio UI Smoke #938 / run `32594549125`: **SUCCESS**.

The additional hosted skip is intentional because the REQUIRED local-media evidence files do not exist on hosted runners. Hosted evidence alone did not close R7.7.

## REQUIRED local Windows evidence

The accepted Windows machine checked out exact head `04cef94c82fdacafe7313d27c8cf516e8e765295` and executed the three commands frozen in `R7_7_DESIGN.md`.

### Doctor

`python -m kodepoia.cli research-media-doctor --json .kodepoia/research/r7_7_media_doctor.json`

Result:
- `ready=true`;
- `source_sha=04cef94c82fdacafe7313d27c8cf516e8e765295`;
- FFmpeg `4.2.3` READY, executable SHA-256 `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`;
- whisper.cpp `1.9.1` READY, executable SHA-256 `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`;
- project-local `ggml-base.en.bin` READY, SHA-256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`, 147,964,211 bytes;
- vision status remains explicit `UNAVAILABLE` because no accepted local vision provider is configured.

Returned doctor JSON evidence file SHA-256: `463c0de4ad477baabc711a2b89fc1c7ad0b7735c6bdfc2ecfdde457a9f8f86e1`.

### Local media acceptance

`python -m kodepoia.cli research-media-acceptance --fixture tests/fixtures/research/r7_7_media_fixture.mp4 --output .kodepoia/research/r7_7_local_acceptance.json`

Result:
- `status=PASS`;
- exact source SHA matched;
- fixture size 12,112 bytes;
- fixture SHA-256 `8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7`;
- audio extraction PASS;
- transcript segment `1, 2, 3, 4.` with valid timestamps;
- bounded semantic fixture check PASS;
- 3 deterministic frame extractions at 500/1500/2500 ms;
- all three frame hashes distinct;
- each frame 320x180;
- temporary disk budget PASS;
- temporary cleanup PASS;
- `cleanup_passed=true`;
- CPU/RAM measurement states remain explicit `UNKNOWN`, not fabricated values.

Accepted frame SHA-256 values:
1. `2266ee5bd266840e71df9d719925e44f058691c26b71c374b007d8b9c06929bb` at 500 ms;
2. `977ae9f38102b7f5a18357a50b4e16b31c9ea9bff11b001ce0f83aa1ab1937ce` at 1500 ms;
3. `29088d0039a1164b5810dbba09d494f12458337c6cb19cacfe5dc8fbcbe015da` at 2500 ms.

Returned acceptance JSON evidence file SHA-256: `33e52eb43ed448dd02766b823c3b22bfb08301a9f4dc3f24f336269f1ab76283`.

### Authoritative local pytest

`python -m pytest -q tests/test_r7_7_media_local_acceptance.py`

Result: **PASS (1 passed, not skipped)**.

## Accepted capability

R7.7 provides:

- deterministic local FFmpeg capability discovery and bounded execution;
- whisper.cpp local STT capability discovery and CPU/no-GPU acceptance path;
- project-confined local model resolution and content hashing;
- bounded 16 kHz mono PCM audio extraction;
- timestamped whisper.cpp JSON transcript ingestion;
- deterministic single-frame extraction with timestamp, SHA-256 and dimensions;
- a `FrameAnalysisProvider` hook that reports `UNAVAILABLE` unless a real accepted vision provider exists;
- input, temporary-disk, timeout, frame-width and pixel budgets;
- ProcessSandbox/KillSwitch and Guardian PROCESS_EXECUTE governance;
- temporary workspace cleanup and explicit resource-measurement states;
- CLI doctor/acceptance commands and versioned schemas.

## Rejected-candidate evidence retained

R7.7 deliberately retained failures as evidence instead of rewriting them as PASS:

- `29fe060739cea5c8b5c39287d2cfb09354ee1a6e`: hosted fixture validation rejected a truncated monolithic Base64 payload;
- `80610cfa8e029e0b611c0b38d9e48388953651d6`: real Windows run rejected literal token matching and exposed FFmpeg 4.2.3 incompatibility with `-fps_mode`;
- `14369842b083dcd6f7f438fa4c9fb6bd9da1fd65`: actual media pipeline PASS, but local authority test still duplicated the stale literal-token rule and was rejected.

The final head corrected those issues without weakening fixture hashing, exact-head binding, process governance or cleanup checks.

## Security / architecture invariants accepted

- no arbitrary model-supplied executable, argv, cwd, environment or model download exists;
- local media paths remain `WorkspaceBoundary` confined;
- external helpers run only through governed process execution;
- no helper/model/driver is auto-installed;
- acceptance CPU path is fixed with whisper.cpp `--no-gpu`/`-ng` semantics;
- media bytes are treated as data and never executed;
- vision interpretation is never fabricated when provider capability is absent;
- missing/failed helpers or models remain explicit UNAVAILABLE/FAIL states;
- temporary artifacts are removed after success or failure;
- real local evidence, not hosted simulation, satisfied the REQUIRED gate.

## Rollback

Rollback is repository-local: remove/disable the R7.7 media adapter, CLI commands, schemas, fixture fragments and tests. Project-local STT model files and locally installed FFmpeg/whisper.cpp remain user-managed external artifacts and are not deleted by rollback.
