# Kodepoia — R7.7 design: local STT + frame extraction/analysis hooks

**Phase:** R7.7  
**Status:** IMPLEMENTATION CANDIDATE — REQUIRED LOCAL GATE NOT YET SATISFIED  
**Architecture:** v1.0 frozen  
**Depends on:** accepted R7.6 + accepted R5 process/media baseline

## Objective

R7.7 adds a governed, local-only media fallback for research when hosted transcripts are missing or visual evidence must be sampled. It does not add a browser, media player, downloader, cloud STT/vision dependency or general subprocess surface.

The authoritative completion gate remains a real Windows/local-tool run. Hosted CI proves the contracts, parsing, fixed argv construction, failure semantics, schemas and regressions; it cannot mark R7.7 COMPLETE.

## Supported baseline

### Media helper: FFmpeg

The supported baseline helper is `ffmpeg`, discovered from `PATH` and version-probed with the fixed command `ffmpeg -version`. All production invocations are issued through `KodeGuardian` + `Capability.PROCESS_EXECUTE` + `ProcessSandbox`; the executable basename must be `ffmpeg` or `ffmpeg.exe`.

R7.7 uses FFmpeg only for:

- decoding a validated local source into mono 16-bit PCM WAV at 16 kHz;
- extracting one PNG frame at each deterministic requested timestamp;
- scaling frames to a bounded width before Pillow validation.

No model-supplied codec, filter string, output path, executable, cwd or environment is accepted.

Reference used for implementation verification: <https://ffmpeg.org/ffmpeg.html> and <https://ffmpeg.org/ffmpeg-filters.html>.

### Local STT: whisper.cpp

The supported R7.7 STT baseline is `whisper-cli` from the upstream `ggml-org/whisper.cpp` project. The project documents Windows support, CPU inference and optional GPU backends; R7.7 intentionally uses the CPU path (`-ng` / `--no-gpu`) for the authoritative acceptance so completion does not depend on CUDA, Vulkan, ROCm or a particular driver stack.

The capability detector requires the installed CLI to expose the documented JSON/full-JSON/output-file/no-GPU contract before it reports READY. The fixed transcription template is equivalent to:

```text
whisper-cli -m <project-model> -f <temporary-wav> -l en -ng -np -oj -ojf -of <temporary-output-base>
```

`<project-model>` is never arbitrary host input. It resolves through `WorkspaceBoundary` and must remain inside the Kodepoia project. The default is:

```text
.kodepoia/models/stt/ggml-base.en.bin
```

A different project-relative path may be supplied with `KODEPOIA_WHISPER_MODEL`. No model download occurs in R7.7, and Kodepoia never installs or changes GPU drivers.

Upstream references used for the contract:

- <https://github.com/ggml-org/whisper.cpp>
- <https://github.com/ggml-org/whisper.cpp/tree/master/examples/cli>

## Fixture and provenance

The repository stores the generated acceptance MP4 as four strict Base64 fragments:

```text
tests/fixtures/research/r7_7_media_fixture.mp4.b64.001
tests/fixtures/research/r7_7_media_fixture.mp4.b64.002
tests/fixtures/research/r7_7_media_fixture.mp4.b64.003
tests/fixtures/research/r7_7_media_fixture.mp4.b64.004
```

The first three fragments are 4,096 ASCII characters and the final fragment is 3,864 characters. Each fragment is Base64-aligned. The acceptance-only materializer concatenates the fragments in numeric order, applies strict `base64(validate=True)`, enforces the media byte budget, and writes the decoded MP4 only under `.kodepoia/research/tmp/`.

The decoded media is a tiny generated 4-second MP4 containing synthetic test video and the spoken words:

```text
one two three four
```

The logical fixture used by the CLI remains:

```text
tests/fixtures/research/r7_7_media_fixture.mp4
```

If an actual project-relative file with that logical name exists, normal local-media processing uses it directly. Otherwise the acceptance fixture materializer uses the four repository fragments, processes the temporary decoded file, then removes the outer fixture directory and the inner processing directory. Multipart assembly is deliberately separated from the generic `LocalMediaAcceptance` implementation so production local-media processing does not depend on test-fixture packaging.

Expected decoded fixture SHA-256:

```text
8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7
```

The decoded fixture is 12,112 bytes. It is generated test material, not third-party copyrighted media.

The first PR candidate used one monolithic Base64 file and was rejected by hosted Python Core because the stored payload was three characters short. That candidate is not acceptance evidence. The multipart representation preserves strict decoding instead of weakening validation.

## Process and security boundary

Every real helper invocation passes through the existing R5 process boundary:

1. `KodeGuardian` authorizes `ActionType.EXECUTE` with `Capability.PROCESS_EXECUTE`.
2. Only the basenames `ffmpeg`, `ffmpeg.exe`, `whisper-cli`, `whisper-cli.exe` are allowlisted.
3. `ProcessSandbox` confines cwd to the project and integrates the global KillSwitch.
4. `ProcessSandbox.run()` drains stdout/stderr through `communicate()` and applies a bounded timeout.
5. R7.7 supplies fixed argv templates from typed constants and validated paths only.

There is no shell, no `shell=True`, no arbitrary argv field exposed to the model and no automatic retry after timeout/cancellation.

## Budgets

Default R7.7 bounds:

- input media: 32 MiB maximum;
- temporary media: 96 MiB maximum;
- FFmpeg invocation timeout: 60 seconds;
- whisper.cpp invocation timeout: 180 seconds;
- frame timestamps: 500, 1500 and 2500 ms;
- frame width: 320 pixels;
- validated frame: at most 4,000,000 pixels.

Elapsed time, input bytes and observed temporary peak bytes are recorded. Portable CPU and RAM measurements are not yet collected by this adapter, therefore their report status is explicitly `UNKNOWN`; they are not fabricated from process duration or file size.

## Timestamped STT evidence

R7.7 requests whisper.cpp full JSON output. Transcript records preserve text and `offsets.from` / `offsets.to` as millisecond start/end anchors. A confidence value is preserved only if the provider emitted a numeric value in `[0, 1]`; absence remains `null`.

For the generated acceptance fixture, the semantic success condition is deliberately tolerant of segmentation: the combined transcript must contain `one`, `two`, `three`, `four`. R7.7 does not require one particular punctuation or segment boundary.

## Frame evidence

Frames are sampled at the three frozen timestamps. Each output is validated by Pillow, bounded by pixel count, and represented by:

- requested timestamp in milliseconds;
- SHA-256 of the PNG bytes;
- width and height.

The acceptance requires three frames and three distinct frame hashes. The hash proves the extracted evidence bytes; it is not a semantic interpretation.

## FrameAnalysisProvider

`FrameAnalysisProvider` is an explicit extension hook for a future accepted local vision-capable model. The R7.7 baseline installs `UnavailableFrameAnalysisProvider`, which returns:

```text
status = UNAVAILABLE
reason = no_accepted_local_vision_provider_configured
```

`UNAVAILABLE` is an accepted capability state for semantic vision in R7.7. It must never be converted to READY merely because frames were successfully extracted.

## Failure and cleanup semantics

Timeout, cancellation, non-zero helper exit, malformed whisper JSON, missing model/tool, malformed or incomplete Base64 fixture parts, fixture hash mismatch, malformed image, size-budget overflow or temporary-disk overflow fails closed. A failed run still attempts to delete only its own `.kodepoia/research/tmp/r7_7_*` and `r7_7_fixture_*` directories.

No source media, model, helper binary or unrelated workspace content is deleted or modified.

## Schemas and evidence

Versioned schemas:

- `schemas/research-media-doctor-v1.schema.json`
- `schemas/research-media-acceptance-v1.schema.json`

Reports:

- `.kodepoia/research/r7_7_media_doctor.json`
- `.kodepoia/research/r7_7_local_acceptance.json`

The doctor records exact executable hashes/versions and the configured model hash/size. The acceptance additionally binds the exact Git source SHA, fixture hash, transcript segments, frame hashes, checks, cleanup result and bounded resource measurements.

## Hosted acceptance before the manual gate

Before the local gate is declared READY, the exact candidate head must pass:

- R0 Repository Guard;
- Python Core all jobs on Ubuntu/Windows;
- KodeStudio UI Smoke;
- deterministic unit/schema tests in `tests/test_r7_7_media.py`.

`tests/test_r7_7_media_local_acceptance.py` deliberately skips when local evidence files do not exist. This skip does **not** satisfy the required gate.

## REQUIRED manual gate

Once the implementation PR has a final exact candidate head and all hosted gates succeed, checkout that exact head on the accepted Windows machine. Prerequisites:

- Python 3.12.x environment for Kodepoia;
- `ffmpeg` discoverable on `PATH`;
- `whisper-cli` discoverable on `PATH` and exposing the required CLI contract;
- a compatible whisper.cpp model stored at `.kodepoia/models/stt/ggml-base.en.bin`, or another project-relative model selected through `KODEPOIA_WHISPER_MODEL`;
- no tokens, cookies or cloud credentials.

Run verbatim from the repository root:

```powershell
python -m kodepoia.cli research-media-doctor --json .kodepoia/research/r7_7_media_doctor.json
python -m kodepoia.cli research-media-acceptance --fixture tests/fixtures/research/r7_7_media_fixture.mp4 --output .kodepoia/research/r7_7_local_acceptance.json
python -m pytest -q tests/test_r7_7_media_local_acceptance.py
```

Expected authoritative result:

- command 1 exits 0 and `ready=true`;
- command 2 exits 0 and `status=PASS`;
- command 3 passes, not skips;
- both JSON reports contain the exact candidate `source_sha`;
- all required checks are true;
- transcript includes the four expected words;
- three frame hashes are present and distinct;
- temporary cleanup is true.

Evidence to return: the two JSON files and the final pytest summary. Personal path/user-name fragments may be redacted if any appear. Do not send a model file, helper binary, token, cookie or unrelated logs.

## Current gate state

**NOT READY / NOT SATISFIED until the implementation PR exact head passes hosted CI.** The manual commands above are finalized, but must not be used as R7.7 acceptance evidence for an earlier or moving head.

## Rollback

If the local test fails: trigger/allow normal process cancellation as needed, preserve the two JSON reports/log summary, delete only R7.7 temporary outputs, do not change drivers automatically, and return to the exact candidate head for diagnosis. R7.7 remains IN PROGRESS until a valid REQUIRED proof exists.
