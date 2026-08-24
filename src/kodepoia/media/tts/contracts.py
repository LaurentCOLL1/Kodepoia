from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any

from ..contracts import sha256_hex, stable_id
from ..serialization import canonical_sha256
from ..voice import AllowedUse, VoiceModelBinding, VoiceProfile, normalize_locale, normalize_voice_text


def _plain_tts_text(value: str) -> str:
    normalized = normalize_voice_text(value, field="text", maximum=4096)
    if "<" in normalized or ">" in normalized:
        raise ValueError("raw XML/SSML-like text is not accepted by the TTS request")
    return normalized


@dataclass(frozen=True, slots=True)
class SynthesisLimits:
    timeout_seconds: float = 60.0
    max_output_bytes: int = 32 * 1024 * 1024
    max_duration_seconds: float = 120.0
    max_stdout_bytes: int = 256 * 1024
    max_stderr_bytes: int = 512 * 1024

    def __post_init__(self) -> None:
        if not math.isfinite(self.timeout_seconds) or not 1.0 <= self.timeout_seconds <= 600.0:
            raise ValueError("timeout_seconds must be finite and between 1 and 600")
        if not math.isfinite(self.max_duration_seconds) or not 0.1 <= self.max_duration_seconds <= 600.0:
            raise ValueError("max_duration_seconds must be finite and between 0.1 and 600")
        for name in ("max_output_bytes", "max_stdout_bytes", "max_stderr_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def canonical(self) -> dict[str, Any]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
            "max_duration_seconds": self.max_duration_seconds,
            "max_stdout_bytes": self.max_stdout_bytes,
            "max_stderr_bytes": self.max_stderr_bytes,
        }


@dataclass(frozen=True, slots=True)
class TTSBackendCapabilities:
    backend_id: str
    supports_explicit_model_path: bool
    supports_explicit_config_path: bool
    supports_output_wav: bool
    supports_speaker_id: bool
    supports_length_scale: bool
    network_required: bool = False

    def __post_init__(self) -> None:
        stable_id(self.backend_id, field="backend_id")
        if self.network_required:
            raise ValueError("R11.5 local TTS backend must not require network access")

    def canonical(self) -> dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "supports_explicit_model_path": self.supports_explicit_model_path,
            "supports_explicit_config_path": self.supports_explicit_config_path,
            "supports_output_wav": self.supports_output_wav,
            "supports_speaker_id": self.supports_speaker_id,
            "supports_length_scale": self.supports_length_scale,
            "network_required": self.network_required,
        }


@dataclass(frozen=True, slots=True)
class SynthesisRequest:
    request_id: str
    profile_digest: str
    binding_digest: str
    locale: str
    text: str
    speaker_id: int | None
    length_scale: float
    allowed_use: AllowedUse = AllowedUse.INTERNAL

    def __post_init__(self) -> None:
        stable_id(self.request_id, field="request_id")
        for name in ("profile_digest", "binding_digest"):
            sha256_hex(getattr(self, name), field=name)
        object.__setattr__(self, "locale", normalize_locale(self.locale))
        object.__setattr__(self, "text", _plain_tts_text(self.text))
        if self.speaker_id is not None and (isinstance(self.speaker_id, bool) or not isinstance(self.speaker_id, int) or not 0 <= self.speaker_id <= 65535):
            raise ValueError("speaker_id must be an integer between 0 and 65535")
        if isinstance(self.length_scale, bool) or not isinstance(self.length_scale, (int, float)) or not math.isfinite(float(self.length_scale)) or not 0.5 <= float(self.length_scale) <= 2.0:
            raise ValueError("length_scale must be finite and between 0.5 and 2.0")

    @classmethod
    def from_profile(
        cls,
        *,
        request_id: str,
        profile: VoiceProfile,
        binding: VoiceModelBinding,
        text: str,
        speaker_id: int | None = None,
        allowed_use: AllowedUse = AllowedUse.INTERNAL,
    ) -> "SynthesisRequest":
        binding.require_use(allowed_use)
        if binding.locale not in profile.locale_candidates():
            raise ValueError("voice binding locale is not permitted by profile locale/fallbacks")
        return cls(
            request_id=request_id,
            profile_digest=profile.digest(),
            binding_digest=binding.digest(),
            locale=binding.locale,
            text=text,
            speaker_id=speaker_id,
            length_scale=1.0 / float(profile.prosody.pace),
            allowed_use=allowed_use,
        )

    @property
    def text_sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def canonical(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "profile_digest": self.profile_digest,
            "binding_digest": self.binding_digest,
            "locale": self.locale,
            "text": self.text,
            "speaker_id": self.speaker_id,
            "length_scale": float(self.length_scale),
            "allowed_use": self.allowed_use.value,
        }

    def cache_key(self, *, runtime_sha256: str, model_sha256: str, config_sha256: str) -> str:
        sha256_hex(runtime_sha256, field="runtime_sha256")
        sha256_hex(model_sha256, field="model_sha256")
        sha256_hex(config_sha256, field="config_sha256")
        payload = {
            "schema_version": 1,
            "request": self.canonical(),
            "runtime_sha256": runtime_sha256,
            "model_sha256": model_sha256,
            "config_sha256": config_sha256,
        }
        return canonical_sha256(payload)
