# R11.5 — Multilingual local TTS adapters, synthesis cache + real-runtime acceptance

## Status

Implementation revised after the first real-runtime checkpoint. Manual acceptance remains **REQUIRED** before merge.

## Scope

R11.5 adds governed local speech synthesis without changing the frozen R1–R10 architecture:

- backend-neutral TTS capabilities and explicit backend registry;
- `piper-compatible` production adapter behind `MediaRuntimeBoundary` + `ProcessSandbox`;
- Godot/system-TTS capability adapter restricted to accessibility/runtime speech and never canonical production assets;
- multilingual `VoiceProfile`/`VoiceModelBinding` request construction from R11.4;
- canonical request/cache identity bound to normalized text, profile/binding, runtime, model and config SHA-256;
- identity-only synthesis cache records whose physical bytes remain governed by the R8 Vault;
- bounded synthesis time/stdout/stderr/output bytes/duration;
- WAV/PCM inspection and QA through R11.2;
- privacy-minimized synthesis/local-acceptance evidence schemas;
- repository-local `models/` catalog governed by `KodeModelRegistry`;
- real local collector requiring explicit voice-license review.

## Repository-local model catalog

Kodepoia now treats `<repo>/models/` as the canonical local home for model payloads. This is a physical catalog, not a Git payload store.

Tracked content:

- `models/README.md` and category/role documentation;
- `models/registry/models.json`;
- one tracked `manifest.json` per governed installed model identity;
- model schemas, license/provenance metadata, SHA-256 identities and byte budgets.

Local-only content:

- `.onnx`, `.gguf`, `.safetensors`, checkpoints and other large model payloads;
- downloaded model-package sidecars such as `.onnx.json` when they are third-party payload bytes;
- runtime caches and provider-specific binary stores.

The existing `kodepoia.models.router.ModelRegistry` remains the logical model-routing registry for roles such as `fast/core/coder/embed/vision`. `KodeModelRegistry` is complementary: it resolves the physical repository-relative model catalog, validates path confinement and verifies local payload SHA-256 identities. No second routing architecture is introduced.

The first registered physical model is:

- model id: `tts.piper.fr-FR.siwis-medium`;
- local directory: `models/tts/piper/fr-FR/siwis-medium/`;
- model/config SHA-256 identities taken from the real R11.5 operator run;
- locale `fr-FR`, backend `piper-compatible`, license id `cc-by-4.0`, provenance id `piper.fr-fr.siwis.medium`.

The collector selects this voice by model id and derives locale/license/provenance from the tracked manifest. Operator approval is still explicit and mandatory.

## Piper-compatible boundary

Kodepoia runtime collectors never download Piper or a voice model. Prerequisite installation/download is an explicit operator action performed before the offline collector run.

The adapter uses:

1. an existing `piper` / `piper.exe` executable;
2. a governed `.onnx` model resolved by `KodeModelRegistry`;
3. its exact `<model>.onnx.json` sibling resolved by the same manifest.

The adapter hashes executable/model/config bytes before synthesis. The current Piper CLI is capability-probed with `--help`; the required markers are `--model`, `--input-file`, `--output-file`, `--speaker` and `--length-scale`.

The text is written to a bounded UTF-8 staging `.txt` file, passed via `--input-file`, and deleted after process execution. The text itself is never passed in argv or written to acceptance evidence; evidence stores only its SHA-256 digest.

No raw Piper flags, `--cuda`, server mode, download command, shell fragment, URL, SSML/XML or arbitrary argv surface is exposed.

## Runtime and resource policy

- `ProcessSandbox` remains the sole subprocess primitive.
- `shell=False` and existing KillSwitch semantics remain authoritative.
- network is not required and the collector performs no network download.
- default synthesis timeout is 60 seconds, bounded to 600 seconds maximum.
- output is constrained to staging and `.wav`.
- stdout/stderr and output byte budgets are checked.
- stale output is removed before execution.
- malformed/truncated/non-PCM WAV output fails through R11.2 validation.
- cancellation/non-zero exit/timeouts fail closed.

## TTS-specific clipping policy

The first real Piper run produced valid 16-bit PCM with one full-scale endpoint sample in 106,496 frames. R11.2's generic audio profile intentionally uses `max_clipped_samples=0`, so that candidate was correctly reported as blocked under the then-current policy.

R11.5 does **not** weaken the generic R11.2 policy. Instead, local neural TTS uses `tts.local.v2` with a tiny isolated-endpoint tolerance:

- maximum 10 parts per million of samples;
- minimum allowance of one isolated endpoint sample;
- absolute cap of 16 samples regardless of output length;
- any count above that budget remains `BLOCKED` as clipping.

This is a Kodepoia TTS acceptance policy, not a claim that full-scale samples are universally harmless. It distinguishes a single isolated PCM endpoint from repeated saturation while keeping the general audio QA profile unchanged.

## Rights and provenance

R11.4 `VoiceModelBinding` remains authoritative. A synthesis request can only be created when:

- the tracked model manifest permits the requested use;
- binding/profile locale compatibility succeeds;
- runtime/model/config bytes match the governed identity;
- the local acceptance operator explicitly confirms that the per-voice/model license was reviewed.

No voice cloning, model training, biometric inference, personal reference recording or unrelated user data is accepted by this flow.

## Cache semantics

`SynthesisRequest.cache_key()` incorporates the normalized request plus runtime/model/config SHA-256. `SynthesisCacheRecord` additionally binds that key to the accepted output SHA-256 and an R8 asset revision identifier. A changed runtime, model or config makes lookup return a cache miss. Physical audio bytes are not stored by the R11 cache index; R8 remains the storage/promotion authority.

## Godot/system TTS

`GodotSystemTTSCapabilityAdapter` only records an externally established availability/platform/locale capability. It exposes no process launcher and cannot produce canonical production speech assets. Its role is `accessibility_runtime` only.

## Evidence

Hosted acceptance uses synthetic/fake process fixtures only. Real-runtime acceptance is intentionally local and REQUIRED. The local collector emits one JSON document containing:

- candidate Git SHA;
- `KodeModelRegistry` model id and manifest digest;
- license/provenance acknowledgement identifiers;
- runtime executable/help hashes;
- model/config hashes;
- binding/profile/request/cache identities;
- output WAV hash and R11.2 facts/QA;
- process status/budgets;
- privacy facts confirming no clone/reference recording/download/audio retention.

The temporary WAV and text staging directory are removed when the collector exits.

## First local checkpoint result

Candidate `441ea87436c6851cd106654454f955a91460f7af` passed all hosted gates but its first real local evidence returned `status=fail`. Piper itself succeeded and the privacy/process checks passed; QA blocked only because the WAV contained one full-scale endpoint sample and the original generic profile allowed zero. That evidence remains a rejected historical candidate and is not reclassified as PASS.

The catalog + TTS QA revision therefore requires a new exact implementation candidate, fresh hosted gates and a fresh local collector run before R11.5 may merge.
