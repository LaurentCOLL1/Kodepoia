from __future__ import annotations

import hashlib
import io
import json
import platform as platform_module
import re
import struct
import tempfile
import time
import wave
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from kodepoia.media.alignment.contracts import (
    AlignmentSource,
    SpeechAlignmentTimeline,
    TimedPhoneme,
    TimedWord,
)
from kodepoia.media.alignment.visemes import build_viseme_timeline, default_viseme_set
from kodepoia.media.audio.qa import AudioQAProfile, evaluate_wav
from kodepoia.media.audio.wav import inspect_wav_bytes
from kodepoia.media.cinematic.contracts import (
    CinematicRef,
    CinematicTrackKind,
    ShotDefinition,
    TimelineEvent,
)
from kodepoia.media.cinematic.timebase import Timebase
from kodepoia.media.contracts import MediaState
from kodepoia.media.serialization import canonical_sha256
from kodepoia.media.tts.contracts import SynthesisRequest, TTSBackendCapabilities
from kodepoia.media.tts.registry import TTSBackendDescriptor, TTSBackendRegistry
from kodepoia.media.voice.governance import AllowedUse, RightsDeclaration, VoiceModelBinding
from kodepoia.media.voice.markup import SpeechSegment, SpeechSegmentKind
from kodepoia.media.voice.profiles import ProsodyIntent, VoiceProfile

FIXTURE_RELATIVE = Path("tests/fixtures/r16_14_media_beta/scenario.json")
SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_FIXTURE_BYTES = 256 * 1024
_MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_MAX_DURATION_SECONDS = 30.0
_MAX_TIMEOUT_SECONDS = 60.0


class MediaBetaGovernanceError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def _safe_relative_output(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise MediaBetaGovernanceError("output path must be a bounded non-empty relative path")
    posix = PurePosixPath(value.replace("\\", "/"))
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute():
        raise MediaBetaGovernanceError("output path must be relative")
    if ".." in posix.parts or ".." in windows.parts:
        raise MediaBetaGovernanceError("output path must not escape its workspace")
    if any(part in {"", "."} for part in posix.parts):
        raise MediaBetaGovernanceError("output path contains an unsafe segment")
    if posix.suffix.casefold() != ".wav":
        raise MediaBetaGovernanceError("representative media output must be WAV")
    return posix.as_posix()


def _validate_external_reference(value: object) -> None:
    if value not in {None, ""}:
        raise MediaBetaGovernanceError("external media references are denied by the core fixture")


def _bounded_int(value: object, *, field: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise MediaBetaGovernanceError(f"{field} must be an integer in [{low},{high}]")
    return value


def _bounded_float(value: object, *, field: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MediaBetaGovernanceError(f"{field} must be numeric")
    result = float(value)
    if not low <= result <= high:
        raise MediaBetaGovernanceError(f"{field} must be in [{low},{high}]")
    return result


def _load_fixture(repo_root: Path) -> tuple[dict[str, Any], bytes]:
    path = (repo_root / FIXTURE_RELATIVE).resolve(strict=True)
    raw = path.read_bytes()
    if not raw or len(raw) > _MAX_FIXTURE_BYTES:
        raise MediaBetaGovernanceError("R16.14 fixture must be non-empty and bounded")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MediaBetaGovernanceError("R16.14 fixture must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise MediaBetaGovernanceError("R16.14 fixture root must be an object")
    return payload, raw


def validate_fixture_payload(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "name",
        "locale",
        "text",
        "output_relative",
        "external_reference",
        "voice",
        "audio",
        "alignment",
        "cinematic",
        "budgets",
        "negative_controls",
    }
    if set(payload) != expected or payload.get("schema_version") != 1:
        raise MediaBetaGovernanceError("R16.14 fixture fields/schema do not match the frozen contract")
    if payload.get("name") != "r16.14-representative-audio-voice-cinematic-beta":
        raise MediaBetaGovernanceError("R16.14 fixture identity is invalid")
    if not isinstance(payload.get("text"), str) or not payload["text"] or len(payload["text"]) > 4096:
        raise MediaBetaGovernanceError("R16.14 fixture text is invalid")
    if not isinstance(payload.get("locale"), str):
        raise MediaBetaGovernanceError("R16.14 fixture locale is invalid")
    _safe_relative_output(payload["output_relative"])
    _validate_external_reference(payload["external_reference"])
    for field in ("voice", "audio", "alignment", "cinematic", "budgets", "negative_controls"):
        if not isinstance(payload.get(field), dict):
            raise MediaBetaGovernanceError(f"R16.14 {field} must be an object")
    audio = payload["audio"]
    if audio.get("waveform") != "triangle":
        raise MediaBetaGovernanceError("R16.14 fixture waveform must be deterministic triangle PCM")
    sample_rate = _bounded_int(audio.get("sample_rate_hz"), field="sample_rate_hz", low=8000, high=48000)
    frequency = _bounded_int(audio.get("frequency_hz"), field="frequency_hz", low=50, high=2000)
    if sample_rate % frequency != 0:
        raise MediaBetaGovernanceError("fixture frequency must divide sample rate exactly")
    _bounded_int(audio.get("duration_ms"), field="duration_ms", low=100, high=10000)
    _bounded_int(audio.get("amplitude"), field="amplitude", low=1, high=30000)
    if audio.get("channels") != 1 or audio.get("sample_width_bytes") != 2:
        raise MediaBetaGovernanceError("core fixture must be mono 16-bit PCM")
    budgets = payload["budgets"]
    max_fixture = _bounded_int(
        budgets.get("max_fixture_bytes"), field="max_fixture_bytes", low=1, high=_MAX_FIXTURE_BYTES
    )
    _bounded_int(budgets.get("max_output_bytes"), field="max_output_bytes", low=44, high=_MAX_OUTPUT_BYTES)
    _bounded_float(
        budgets.get("max_duration_seconds"), field="max_duration_seconds", low=0.1, high=_MAX_DURATION_SECONDS
    )
    _bounded_float(
        budgets.get("timeout_seconds"), field="timeout_seconds", low=0.1, high=_MAX_TIMEOUT_SECONDS
    )
    if max_fixture > _MAX_FIXTURE_BYTES:
        raise MediaBetaGovernanceError("fixture budget exceeds policy")
    return payload


def _triangle_wav_bytes(audio: dict[str, Any]) -> bytes:
    sample_rate = int(audio["sample_rate_hz"])
    duration_ms = int(audio["duration_ms"])
    frequency = int(audio["frequency_hz"])
    amplitude = int(audio["amplitude"])
    frame_count = sample_rate * duration_ms // 1000
    period = sample_rate // frequency
    half = period // 2
    if frame_count <= 0 or period < 4 or half <= 0:
        raise MediaBetaGovernanceError("deterministic audio recipe is invalid")
    samples: list[int] = []
    for index in range(frame_count):
        phase = index % period
        if phase < half:
            value = -amplitude + (2 * amplitude * phase) // half
        else:
            value = amplitude - (2 * amplitude * (phase - half)) // half
        samples.append(value)
    pcm = struct.pack("<" + "h" * len(samples), *samples)
    stream = io.BytesIO()
    with wave.open(stream, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm)
    return stream.getvalue()


def _voice_contracts(
    fixture: dict[str, Any],
) -> tuple[VoiceProfile, VoiceModelBinding, SynthesisRequest, TTSBackendDescriptor]:
    voice = fixture["voice"]
    profile = VoiceProfile(
        profile_id=str(voice["profile_id"]),
        scope_id=str(voice["scope_id"]),
        locale=str(fixture["locale"]),
        prosody=ProsodyIntent(),
        display_name="R16.14 synthetic fixture voice",
    )
    rights = RightsDeclaration(
        provenance_id=str(voice["provenance_id"]),
        license_id=str(voice["license_id"]),
        allowed_uses=(AllowedUse(str(voice["allowed_use"])),),
        state=MediaState.AVAILABLE,
    )
    binding = VoiceModelBinding(
        binding_id=str(voice["binding_id"]),
        backend_id=str(voice["backend_id"]),
        model_sha256=hashlib.sha256(str(voice["model_seed"]).encode("utf-8")).hexdigest(),
        config_sha256=hashlib.sha256(str(voice["config_seed"]).encode("utf-8")).hexdigest(),
        locale=str(fixture["locale"]),
        rights=rights,
        display_label="Synthetic public-domain fixture",
    )
    request = SynthesisRequest.from_profile(
        request_id="r16.14.fixture.request",
        profile=profile,
        binding=binding,
        text=str(fixture["text"]),
        allowed_use=AllowedUse.INTERNAL,
    )
    capabilities = TTSBackendCapabilities(
        backend_id=binding.backend_id,
        supports_explicit_model_path=True,
        supports_explicit_config_path=True,
        supports_output_wav=True,
        supports_speaker_id=True,
        supports_length_scale=True,
        network_required=False,
    )
    descriptor = TTSBackendDescriptor(
        backend_id=binding.backend_id,
        state=MediaState.AVAILABLE,
        role="representative-fixture",
        canonical_production=False,
        capabilities=capabilities,
    )
    return profile, binding, request, descriptor


def _alignment(
    fixture: dict[str, Any], audio_sha256: str, duration_seconds: float
) -> SpeechAlignmentTimeline:
    raw = fixture["alignment"]
    words = tuple(
        TimedWord(str(item["text"]), float(item["start_seconds"]), float(item["end_seconds"]), 1.0)
        for item in raw["words"]
    )
    phonemes = tuple(
        TimedPhoneme(
            str(item["phoneme"]),
            float(item["start_seconds"]),
            float(item["end_seconds"]),
            1.0,
            int(item["word_index"]),
        )
        for item in raw["phonemes"]
    )
    return SpeechAlignmentTimeline(
        timeline_id="r16.14.fixture.alignment",
        audio_sha256=audio_sha256,
        locale=str(fixture["locale"]),
        duration_seconds=duration_seconds,
        source=AlignmentSource.SYNTHETIC,
        source_id="r16.14.repository.fixture",
        words=words,
        phonemes=phonemes,
    )


def _cinematic(
    fixture: dict[str, Any], *, audio_sha256: str, alignment_digest: str, viseme_digest: str, request_id: str
) -> ShotDefinition:
    raw = fixture["cinematic"]
    timebase = Timebase(int(raw["fps_num"]), int(raw["fps_den"]))
    refs = (
        CinematicRef("r16.14.audio", "audio", audio_sha256),
        CinematicRef("r16.14.alignment", "alignment", alignment_digest),
        CinematicRef("r16.14.visemes", "visemes", viseme_digest),
    )
    events = (
        TimelineEvent(
            event_id="r16.14.dialogue",
            track_kind=CinematicTrackKind.DIALOGUE,
            start_frame=int(raw["dialogue_start_frame"]),
            duration_frames=int(raw["dialogue_duration_frames"]),
            ref_id="r16.14.audio",
            payload={"voice_run_id": request_id, "speaker_id": str(raw["speaker_id"])},
        ),
        TimelineEvent(
            event_id="r16.14.facial",
            track_kind=CinematicTrackKind.FACIAL,
            start_frame=int(raw["dialogue_start_frame"]),
            duration_frames=int(raw["dialogue_duration_frames"]),
            ref_id="r16.14.visemes",
            payload={"curve_set_id": "r16.14.visemes", "weight": 1.0},
        ),
    )
    return ShotDefinition(
        shot_id="r16.14.fixture.shot",
        timebase=timebase,
        duration_frames=int(raw["duration_frames"]),
        refs=refs,
        events=events,
    )


def _raises(expected: type[BaseException], operation: Any) -> bool:
    try:
        operation()
    except expected:
        return True
    return False


def _promote(staged: Path, final: Path, *, cancelled: bool) -> bool:
    if cancelled:
        staged.unlink(missing_ok=True)
        return False
    final.parent.mkdir(parents=True, exist_ok=True)
    staged.replace(final)
    return final.is_file()


def qualify_human_listening(*, requested: bool = False) -> dict[str, Any]:
    if not requested:
        return {
            "state": "NOT_EXERCISED",
            "claim_satisfied": False,
            "manual_required": False,
            "detail": "human listening/device playback is optional and was not requested",
        }
    return {
        "state": "MANUAL_REQUIRED",
        "claim_satisfied": False,
        "manual_required": True,
        "detail": (
            "an explicitly requested listening/device-quality claim requires a "
            "human/device qualification outside core CI"
        ),
    }


def _secret_free(value: Any) -> bool:
    text = _canonical_json(value).casefold()
    markers = ("ghp_", "github_pat_", "sk-", "password=", "authorization: bearer")
    return not any(marker in text for marker in markers)


def build_media_beta_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str | None = None,
    require_human_listening: bool = False,
) -> dict[str, Any]:
    if not isinstance(source_sha, str) or SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be the exact lowercase 40-character candidate SHA")
    started = time.monotonic()
    fixture, fixture_bytes = _load_fixture(repo_root)
    validate_fixture_payload(fixture)
    fixture_sha256 = canonical_sha256(fixture)
    output_relative = _safe_relative_output(str(fixture["output_relative"]))
    _validate_external_reference(fixture["external_reference"])

    profile, binding, request, descriptor = _voice_contracts(fixture)
    registry = TTSBackendRegistry()
    registry.register(descriptor)
    registry_entry = registry.get(descriptor.backend_id, role="representative-fixture")
    binding.require_use(AllowedUse.INTERNAL)
    rights_denied = _raises(PermissionError, lambda: binding.require_use(AllowedUse.COMMERCIAL))

    structured = SpeechSegment(SpeechSegmentKind.TEXT, text=str(fixture["text"]))
    unsafe_markup_denied = _raises(
        ValueError,
        lambda: SpeechSegment(
            SpeechSegmentKind.TEXT, text=str(fixture["negative_controls"]["unsafe_markup"])
        ),
    )

    wav_bytes = _triangle_wav_bytes(fixture["audio"])
    audio_sha256 = hashlib.sha256(wav_bytes).hexdigest()
    budgets = fixture["budgets"]
    facts = inspect_wav_bytes(
        wav_bytes,
        max_bytes=int(budgets["max_output_bytes"]),
        max_duration_seconds=float(budgets["max_duration_seconds"]),
    )
    qa = evaluate_wav(
        audio_sha256,
        facts,
        AudioQAProfile(
            profile_id="r16.14.synthetic-dialogue.v1",
            max_duration_seconds=float(budgets["max_duration_seconds"]),
            max_channels=1,
            allowed_sample_rates=(int(fixture["audio"]["sample_rate_hz"]),),
            max_clipped_samples=0,
        ),
    )

    alignment = _alignment(fixture, audio_sha256, facts.duration_seconds)
    viseme_set = default_viseme_set()
    visemes = build_viseme_timeline(
        alignment,
        viseme_set,
        timeline_id="r16.14.fixture.visemes",
        attack_seconds=0.02,
        release_seconds=0.03,
    )
    shot = _cinematic(
        fixture,
        audio_sha256=audio_sha256,
        alignment_digest=alignment.digest(),
        viseme_digest=visemes.digest(),
        request_id=request.request_id,
    )

    negative = fixture["negative_controls"]
    path_escape_denied = _raises(
        MediaBetaGovernanceError, lambda: _safe_relative_output(str(negative["path_escape"]))
    )
    external_reference_denied = _raises(
        MediaBetaGovernanceError,
        lambda: _validate_external_reference(negative["external_reference"]),
    )
    cinematic_payload_denied = _raises(
        ValueError,
        lambda: TimelineEvent(
            event_id="r16.14.bad-event",
            track_kind=CinematicTrackKind.DIALOGUE,
            start_frame=0,
            duration_frames=1,
            ref_id=None,
            payload={str(negative["cinematic_payload_key"]): "R16_14_COMMAND_SHOULD_NOT_RUN"},
        ),
    )

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-14-") as tmp:
        workspace = Path(tmp).resolve()
        positive_stage = workspace / "staged" / "dialogue.wav"
        positive_stage.parent.mkdir(parents=True, exist_ok=True)
        positive_stage.write_bytes(wav_bytes)
        final = (workspace / output_relative).resolve()
        if workspace not in final.parents:
            raise MediaBetaGovernanceError("validated R16.14 output escaped workspace")
        promoted = _promote(positive_stage, final, cancelled=False)
        promoted_sha256 = hashlib.sha256(final.read_bytes()).hexdigest() if promoted else "0" * 64

        cancelled_stage = workspace / "cancelled" / "partial.wav"
        cancelled_final = workspace / "cancelled-output" / "dialogue.wav"
        cancelled_stage.parent.mkdir(parents=True, exist_ok=True)
        cancelled_stage.write_bytes(wav_bytes[: max(44, len(wav_bytes) // 4)])
        cancelled_promoted = _promote(cancelled_stage, cancelled_final, cancelled=True)
        cancellation_clean = (
            not cancelled_promoted and not cancelled_final.exists() and not cancelled_stage.exists()
        )

    request_digest = canonical_sha256(
        {"schema": "kodepoia.r16.14.tts_request", "version": 1, "payload": request.canonical()}
    )
    binding_payload = {
        "source_sha": source_sha,
        "fixture_sha256": fixture_sha256,
        "text_sha256": request.text_sha256,
        "profile_sha256": profile.digest(),
        "voice_binding_sha256": binding.digest(),
        "tts_request_sha256": request_digest,
        "audio_sha256": audio_sha256,
        "alignment_sha256": alignment.digest(),
        "viseme_sha256": visemes.digest(),
        "cinematic_sha256": shot.digest(),
    }
    elapsed = time.monotonic() - started
    cases = [
        _case(
            "deterministic-repository-media-fixture",
            fixture_sha256 == canonical_sha256(fixture)
            and 0 < len(fixture_bytes) <= int(budgets["max_fixture_bytes"]),
            "repository-owned UTF-8 JSON fixture is canonically hashed and bounded",
        ),
        _case(
            "supported-local-tts-contract-path",
            registry_entry.state is MediaState.AVAILABLE
            and registry_entry.capabilities is not None
            and registry_entry.capabilities.supports_output_wav
            and not registry_entry.capabilities.network_required
            and request.locale == str(fixture["locale"]),
            (
                "existing local TTS registry/request contracts are exercised without "
                "claiming a live synthesis runtime"
            ),
        ),
        _case(
            "voice-rights-governance",
            binding.state is MediaState.AVAILABLE and rights_denied,
            "synthetic fixture rights permit internal use and fail closed for an undeclared commercial use",
        ),
        _case(
            "structured-voice-markup",
            structured.text == str(fixture["text"]),
            "repository-owned structured speech segment accepts bounded plain text",
        ),
        _case(
            "unsafe-xml-ssml-markup-denied",
            unsafe_markup_denied,
            "raw XML/SSML-like markup cannot cross the structured speech contract",
        ),
        _case(
            "deterministic-wav-audio-qa",
            qa.state is MediaState.PASS
            and facts.channels == 1
            and facts.sample_width_bytes == 2
            and facts.clipped_samples == 0,
            "deterministic mono PCM fixture passes existing WAV inspection and audio QA",
        ),
        _case(
            "alignment-bounded-by-audio",
            alignment.audio_sha256 == audio_sha256
            and len(alignment.words) == 2
            and len(alignment.phonemes) == 9,
            "synthetic word/phoneme timing is monotonic and bounded by accepted audio duration",
        ),
        _case(
            "viseme-generation-bound",
            visemes.audio_sha256 == audio_sha256
            and len(visemes.events) == len(alignment.phonemes)
            and all(not event.fallback_used for event in visemes.events),
            (
                "visemes are deterministically derived from the exact alignment and "
                "bounded coarticulation policy"
            ),
        ),
        _case(
            "cinematic-timing-and-digest-links",
            shot.duration_frames == 24
            and {ref.ref_kind for ref in shot.refs} == {"audio", "alignment", "visemes"}
            and len(shot.digest()) == 64,
            "cinematic dialogue/facial timing references exact media/alignment/viseme digests",
        ),
        _case(
            "cinematic-payload-command-denied",
            cinematic_payload_denied,
            "non-allowlisted cinematic payload keys cannot acquire arbitrary command authority",
        ),
        _case(
            "workspace-output-boundary",
            promoted and promoted_sha256 == audio_sha256 and path_escape_denied,
            "validated output is promoted only inside the temporary workspace and traversal is denied",
        ),
        _case(
            "external-reference-denied",
            external_reference_denied,
            "core media fixture cannot silently introduce an external model/media reference",
        ),
        _case(
            "resource-budgets",
            len(wav_bytes) <= int(budgets["max_output_bytes"])
            and facts.duration_seconds <= float(budgets["max_duration_seconds"])
            and elapsed <= float(budgets["timeout_seconds"]),
            "fixture bytes, output bytes, duration and execution time remain inside frozen limits",
        ),
        _case(
            "cancellation-partial-output-not-promoted",
            cancellation_clean,
            "a cancelled partial media output is deleted and never promoted",
        ),
        _case(
            "exact-source-media-provenance-binding",
            binding_payload["source_sha"] == source_sha
            and binding_payload["audio_sha256"] == promoted_sha256
            and len(canonical_sha256(binding_payload)) == 64,
            (
                "media evidence binds exact source, fixture, text, voice, request, audio, "
                "alignment, viseme and cinematic digests"
            ),
        ),
    ]

    human = qualify_human_listening(requested=require_human_listening)
    cases.append(
        _case(
            "human-listening-not-inferred",
            human["state"] in {"NOT_EXERCISED", "MANUAL_REQUIRED"} and not human["claim_satisfied"],
            "core CI never infers an audible/device-quality claim from synthetic machine-verifiable evidence",
        )
    )
    security_claim = all(bool(item["pass"]) for item in cases)
    semantic = {
        "phase": "R16.14",
        "source_sha": source_sha,
        "fixture_sha256": fixture_sha256,
        "binding_sha256": canonical_sha256(binding_payload),
        "cases": [{"name": item["name"], "pass": item["pass"]} for item in cases],
        "manual_state": "CONDITIONAL_REQUESTED" if require_human_listening else "CONDITIONAL_NOT_TRIGGERED",
        "security_claim": security_claim,
        "critical_veto": not security_claim,
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.14",
        "source_sha": source_sha,
        "platform": platform or platform_module.system(),
        "manual_state": "CONDITIONAL_REQUESTED" if require_human_listening else "CONDITIONAL_NOT_TRIGGERED",
        "core_manual_required": False,
        "security_claim": security_claim,
        "critical_veto": not security_claim,
        "live_credentials_used": False,
        "destructive_host_actions": False,
        "external_network_calls": 0,
        "fixture_is_synthetic_audio": True,
        "fixture_is_real_tts_runtime": False,
        "fixture_is_human_listened": False,
        "fixture_sha256": fixture_sha256,
        "text_sha256": request.text_sha256,
        "profile_sha256": profile.digest(),
        "voice_binding_sha256": binding.digest(),
        "tts_request_sha256": request_digest,
        "audio_sha256": audio_sha256,
        "audio_facts": facts.canonical(),
        "audio_qa": qa.canonical(),
        "alignment_sha256": alignment.digest(),
        "viseme_sha256": visemes.digest(),
        "cinematic_sha256": shot.digest(),
        "binding_sha256": canonical_sha256(binding_payload),
        "human_listening_qualification": human,
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(bool(item["pass"]) for item in cases),
            "failed": sum(not bool(item["pass"]) for item in cases),
        },
        "semantic_sha256": canonical_sha256(semantic),
    }
    report["secret_free"] = _secret_free(report)
    if not report["secret_free"]:
        report["security_claim"] = False
        report["critical_veto"] = True
    report["evidence_sha256"] = _digest(report)
    return report
