# R11.5 — Multilingual local TTS adapters, synthesis cache + real-runtime acceptance

## Status

Implementation candidate. Manual acceptance is **REQUIRED** before merge.

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
- real local collector requiring explicit voice-license review.

## Piper-compatible boundary

Kodepoia never downloads Piper or a voice model. The user supplies existing paths to:

1. a `piper` / `piper.exe` executable;
2. a governed `.onnx` model;
3. its exact `<model>.onnx.json` sibling.

The adapter hashes executable/model/config bytes before synthesis. The current Piper CLI is capability-probed with `--help`; the required markers are `--model`, `--input-file`, `--output-file`, `--speaker` and `--length-scale`.

The text is written to a bounded UTF-8 staging `.txt` file, passed via `--input-file`, and deleted after process execution. The text itself is never passed in argv or written to acceptance evidence; evidence stores only its SHA-256 digest.

The config file is still part of the governed identity and must be the exact `<model>.onnx.json` sibling. R11.5 does not claim an independently routed config path changes Piper runtime behavior.

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

## Rights and provenance

R11.4 `VoiceModelBinding` remains authoritative. A synthesis request can only be created when:

- the binding permits the requested use;
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
- license/provenance acknowledgement identifiers;
- runtime executable/help hashes;
- model/config hashes;
- binding/profile/request/cache identities;
- output WAV hash and R11.2 facts/QA;
- process status/budgets;
- privacy facts confirming no clone/reference recording/download/audio retention.

The temporary WAV and text staging directory are removed when the collector exits.

## External baseline note

As verified on 2026-08-24, the maintained OHF Piper project installs as `piper-tts`; its current CLI exposes explicit model/input-file/output-file/speaker/length-scale controls. Voice packages remain external and have per-resource model cards/licenses. This is a compatibility baseline, not vendored dependency evidence.
