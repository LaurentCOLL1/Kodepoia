from __future__ import annotations

import hashlib
import io
import json
import wave
from pathlib import Path

import pytest
from jsonschema import validate

from kodepoia.core.sandbox import SandboxResult
from kodepoia.media.boundary import MediaRuntimeBoundary
from kodepoia.media.tts import PiperAdapter, SynthesisLimits, SynthesisRequest, synthesize_local
from kodepoia.media.voice import AllowedUse, ProsodyIntent, RightsDeclaration, VoiceModelBinding, VoiceProfile


def _wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(22050)
        samples = [0, 300, -300, 800, -800, 1200, -1200, 500] * 512
        payload = b"".join(int(sample).to_bytes(2, "little", signed=True) for sample in samples)
        handle.writeframes(payload)
    return buffer.getvalue()


class FakeSandbox:
    def __init__(self, wav: bytes, *, cancel: bool = False) -> None:
        self.wav = wav
        self.cancel = cancel
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: tuple[str, ...], *, timeout: float = 60.0, **_kwargs: object) -> SandboxResult:
        self.calls.append(tuple(argv))
        if "--help" in argv:
            help_text = "--model --config --output-file --speaker --length-scale"
            return SandboxResult(0, help_text, "")
        output_index = argv.index("--output-file") + 1
        Path(argv[output_index]).write_bytes(self.wav)
        if self.cancel:
            return SandboxResult(17, "", "cancelled", cancelled=True)
        return SandboxResult(0, "", "")


def _fixture(tmp_path: Path) -> tuple[PiperAdapter, Path, Path, Path, VoiceModelBinding, SynthesisRequest]:
    runtime_root = tmp_path / "runtime"
    model_root = tmp_path / "models"
    staging = tmp_path / "staging"
    runtime_root.mkdir()
    model_root.mkdir()
    staging.mkdir()
    executable = runtime_root / ("piper.exe" if __import__("os").name == "nt" else "piper")
    executable.write_bytes(b"synthetic-piper-executable")
    model = model_root / "fr_FR-test-medium.onnx"
    config = model_root / "fr_FR-test-medium.onnx.json"
    model.write_bytes(b"synthetic-model")
    config.write_text('{"audio":{"sample_rate":22050}}', encoding="utf-8")
    rights = RightsDeclaration(
        provenance_id="prov.synthetic.fixture",
        license_id="cc-by-4.0",
        allowed_uses=(AllowedUse.INTERNAL,),
        source_uri_id="source.synthetic.model-card",
    )
    binding = VoiceModelBinding(
        binding_id="binding.fr.fixture",
        backend_id="piper-compatible",
        model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
        config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        locale="fr-FR",
        rights=rights,
    )
    profile = VoiceProfile(
        profile_id="voice.fixture",
        scope_id="character.fixture",
        locale="fr-FR",
        prosody=ProsodyIntent(pace=1.25),
    )
    request = SynthesisRequest.from_profile(
        request_id="tts.fixture",
        profile=profile,
        binding=binding,
        text="Kodepoia vérifie une synthèse locale.",
    )
    boundary = MediaRuntimeBoundary(allowed_roots=(runtime_root,), staging_root=staging)
    adapter = PiperAdapter(boundary, FakeSandbox(_wav_bytes()), model_root=model_root)  # type: ignore[arg-type]
    return adapter, executable, model, config, binding, request


def test_synthesis_request_identity_is_deterministic_and_rights_gated(tmp_path: Path) -> None:
    adapter, executable, model, config, binding, request = _fixture(tmp_path)
    runtime_sha = hashlib.sha256(executable.read_bytes()).hexdigest()
    key1 = request.cache_key(runtime_sha256=runtime_sha, model_sha256=binding.model_sha256, config_sha256=binding.config_sha256)
    key2 = request.cache_key(runtime_sha256=runtime_sha, model_sha256=binding.model_sha256, config_sha256=binding.config_sha256)
    assert key1 == key2
    assert len(key1) == 64
    assert request.length_scale == pytest.approx(0.8)
    blocked = VoiceModelBinding(
        binding_id="binding.blocked",
        backend_id="piper-compatible",
        model_sha256=binding.model_sha256,
        config_sha256=binding.config_sha256,
        locale="fr-FR",
        rights=RightsDeclaration(
            provenance_id="prov.blocked",
            license_id="restricted",
            allowed_uses=(AllowedUse.INTERNAL,),
            state=__import__("kodepoia.media.contracts", fromlist=["MediaState"]).MediaState.RIGHTS_BLOCKED,
        ),
    )
    profile = VoiceProfile("voice.blocked", "character.blocked", "fr-FR")
    with pytest.raises(PermissionError):
        SynthesisRequest.from_profile(request_id="tts.blocked", profile=profile, binding=blocked, text="Test")


def test_piper_probe_and_compiler_are_finite_and_path_safe(tmp_path: Path) -> None:
    adapter, executable, model, config, binding, request = _fixture(tmp_path)
    probe = adapter.capability_probe(executable)
    assert probe.status == "pass"
    output = adapter.boundary.staging_root / "voice.wav"
    argv = adapter.compile_synthesis_argv(executable, model, config, output, binding=binding, request=request)
    assert argv[0] == str(executable.resolve())
    assert "--model" in argv and "--config" in argv and "--output-file" in argv
    assert "--length-scale" in argv
    assert "--cuda" not in argv and "download" not in " ".join(argv).lower()
    assert argv[-2] == "--"
    assert argv[-1] == request.text
    with pytest.raises(ValueError):
        adapter.compile_synthesis_argv(executable, model, config, tmp_path / "escape.wav", binding=binding, request=request)


def test_model_byte_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    adapter, executable, model, config, binding, request = _fixture(tmp_path)
    model.write_bytes(b"tampered")
    with pytest.raises(ValueError):
        adapter.compile_synthesis_argv(
            executable,
            model,
            config,
            adapter.boundary.staging_root / "voice.wav",
            binding=binding,
            request=request,
        )


def test_synthesize_local_validates_wav_qa_and_emits_deterministic_manifest(tmp_path: Path) -> None:
    adapter, executable, model, config, binding, request = _fixture(tmp_path)
    output = adapter.boundary.staging_root / "voice.wav"
    manifest = synthesize_local(
        adapter,
        executable=executable,
        model_path=model,
        config_path=config,
        output_path=output,
        binding=binding,
        request=request,
        source_sha="a" * 40,
        limits=SynthesisLimits(timeout_seconds=10.0, max_duration_seconds=10.0),
    )
    assert manifest.status == "pass"
    assert manifest.blockers == ()
    assert manifest.output_sha256 == hashlib.sha256(_wav_bytes()).hexdigest()
    assert manifest.qa["state"] in {"PASS", "WARN"}
    assert manifest.wav_facts["sample_rate_hz"] == 22050
    assert len(manifest.cache_key) == 64


def test_cancelled_runtime_fails_manifest(tmp_path: Path) -> None:
    adapter, executable, model, config, binding, request = _fixture(tmp_path)
    adapter.sandbox = FakeSandbox(_wav_bytes(), cancel=True)  # type: ignore[assignment]
    manifest = synthesize_local(
        adapter,
        executable=executable,
        model_path=model,
        config_path=config,
        output_path=adapter.boundary.staging_root / "cancelled.wav",
        binding=binding,
        request=request,
        source_sha="b" * 40,
    )
    assert manifest.status == "fail"
    assert "synthesis_cancelled" in manifest.blockers
    assert "synthesis_nonzero" in manifest.blockers


def test_raw_markup_and_unapproved_locale_fail_before_execution(tmp_path: Path) -> None:
    adapter, _executable, _model, _config, binding, _request = _fixture(tmp_path)
    profile = VoiceProfile("voice.en", "character.en", "en-US")
    with pytest.raises(ValueError):
        SynthesisRequest.from_profile(request_id="tts.locale", profile=profile, binding=binding, text="Hello")
    profile_fr = VoiceProfile("voice.fr", "character.fr", "fr-FR")
    with pytest.raises(ValueError):
        SynthesisRequest.from_profile(request_id="tts.ssml", profile=profile_fr, binding=binding, text="<speak>Bonjour</speak>")


def test_synthesis_manifest_schema_accepts_representative_manifest(tmp_path: Path) -> None:
    adapter, executable, model, config, binding, request = _fixture(tmp_path)
    manifest = synthesize_local(
        adapter,
        executable=executable,
        model_path=model,
        config_path=config,
        output_path=adapter.boundary.staging_root / "schema.wav",
        binding=binding,
        request=request,
        source_sha="c" * 40,
    )
    schema = json.loads(Path("schemas/r11/tts-synthesis-manifest.schema.json").read_text(encoding="utf-8"))
    validate(instance=manifest.canonical(), schema=schema)
