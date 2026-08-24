from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from kodepoia.media.contracts import MediaState
from kodepoia.media.tts import (
    GodotSystemTTSCapabilityAdapter,
    GodotSystemTTSProbe,
    SynthesisCacheIndex,
    SynthesisCacheRecord,
    TTSBackendCapabilities,
    TTSBackendDescriptor,
    TTSBackendRegistry,
)


def test_missing_backend_is_explicitly_unavailable() -> None:
    registry = TTSBackendRegistry()
    missing = registry.get("missing-backend")
    assert missing.state is MediaState.UNAVAILABLE
    assert missing.canonical_production is False
    assert missing.capabilities is None


def test_registry_rejects_duplicate_backend_identity() -> None:
    registry = TTSBackendRegistry()
    descriptor = TTSBackendDescriptor(
        backend_id="piper-compatible",
        state=MediaState.AVAILABLE,
        role="production",
        canonical_production=True,
        capabilities=TTSBackendCapabilities(
            backend_id="piper-compatible",
            supports_explicit_model_path=True,
            supports_explicit_config_path=False,
            supports_output_wav=True,
            supports_speaker_id=True,
            supports_length_scale=True,
        ),
    )
    registry.register(descriptor)
    assert registry.get("piper-compatible") == descriptor
    with pytest.raises(ValueError, match="already registered"):
        registry.register(descriptor)


def test_network_required_backend_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not require network"):
        TTSBackendCapabilities(
            backend_id="cloud-like",
            supports_explicit_model_path=False,
            supports_explicit_config_path=False,
            supports_output_wav=True,
            supports_speaker_id=False,
            supports_length_scale=False,
            network_required=True,
        )


def test_godot_system_tts_is_accessibility_only_and_never_canonical_production() -> None:
    probe = GodotSystemTTSProbe(platform="Windows", available=True, locales=("fr_fr", "en-US"))
    descriptor = GodotSystemTTSCapabilityAdapter.descriptor(probe)
    assert descriptor.state is MediaState.AVAILABLE
    assert descriptor.role == "accessibility_runtime"
    assert descriptor.canonical_production is False
    assert descriptor.capabilities is not None
    assert descriptor.capabilities.supports_output_wav is False
    assert probe.locales == ("en-US", "fr-FR")


def test_unavailable_system_tts_stays_unavailable_without_network_fallback() -> None:
    descriptor = GodotSystemTTSCapabilityAdapter.descriptor(
        GodotSystemTTSProbe(platform="Linux", available=False)
    )
    assert descriptor.state is MediaState.UNAVAILABLE
    assert descriptor.capabilities is None


def test_cache_resolves_only_exact_runtime_model_config_identity() -> None:
    record = SynthesisCacheRecord(
        cache_key="a" * 64,
        asset_revision_id="asset.rev.tts.001",
        output_sha256="b" * 64,
        runtime_sha256="c" * 64,
        model_sha256="d" * 64,
        config_sha256="e" * 64,
    )
    cache = SynthesisCacheIndex()
    cache.put(record)
    assert cache.resolve(
        record.cache_key,
        runtime_sha256=record.runtime_sha256,
        model_sha256=record.model_sha256,
        config_sha256=record.config_sha256,
    ) == record
    assert cache.resolve(
        record.cache_key,
        runtime_sha256="f" * 64,
        model_sha256=record.model_sha256,
        config_sha256=record.config_sha256,
    ) is None


def test_cache_record_schema_accepts_canonical_record() -> None:
    record = SynthesisCacheRecord(
        cache_key="1" * 64,
        asset_revision_id="asset.rev.tts.002",
        output_sha256="2" * 64,
        runtime_sha256="3" * 64,
        model_sha256="4" * 64,
        config_sha256="5" * 64,
    )
    schema = json.loads(Path("schemas/r11/tts-cache-record.schema.json").read_text(encoding="utf-8"))
    validate(instance=record.canonical(), schema=schema)


def test_local_acceptance_schema_accepts_privacy_minimized_representative_evidence() -> None:
    evidence = {
        "schema": "kodepoia.r11_5_local_acceptance",
        "version": 1,
        "source_sha": "a" * 40,
        "status": "pass",
        "blockers": [],
        "approval": {
            "license_reviewed": True,
            "license_id": "cc-by-4.0",
            "provenance_id": "prov.voice.fixture",
            "allowed_use": "internal",
            "locale": "fr-FR",
        },
        "voice_identity": {
            "model_sha256": "b" * 64,
            "config_sha256": "c" * 64,
            "binding_digest": "d" * 64,
            "profile_digest": "e" * 64,
        },
        "capability": {},
        "synthesis": {},
        "privacy": {
            "private_recording_used": False,
            "voice_clone_used": False,
            "network_download_performed_by_collector": False,
            "audio_retained": False,
        },
        "evidence_digest": "f" * 64,
    }
    schema = json.loads(Path("schemas/r11/tts-local-acceptance.schema.json").read_text(encoding="utf-8"))
    validate(instance=evidence, schema=schema)
