from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contracts import MediaState, bounded_text
from ..voice import normalize_locale
from .contracts import TTSBackendCapabilities
from .registry import TTSBackendDescriptor


@dataclass(frozen=True, slots=True)
class GodotSystemTTSProbe:
    platform: str
    available: bool
    locales: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        bounded_text(self.platform, field="platform", maximum=128)
        normalized = tuple(sorted({normalize_locale(item) for item in self.locales}))
        object.__setattr__(self, "locales", normalized)
        if not self.available and normalized:
            raise ValueError("unavailable system TTS must not claim locales")

    def canonical(self) -> dict[str, Any]:
        return {"platform": self.platform, "available": self.available, "locales": list(self.locales)}


class GodotSystemTTSCapabilityAdapter:
    """Capability-only bridge for Godot/system TTS.

    It is explicitly non-canonical for production speech assets and exposes no
    subprocess, voice-cloning, model-download or arbitrary engine-flag surface.
    """

    backend_id = "godot-system-tts"

    @classmethod
    def descriptor(cls, probe: GodotSystemTTSProbe) -> TTSBackendDescriptor:
        capabilities = None
        if probe.available:
            capabilities = TTSBackendCapabilities(
                backend_id=cls.backend_id,
                supports_explicit_model_path=False,
                supports_explicit_config_path=False,
                supports_output_wav=False,
                supports_speaker_id=False,
                supports_length_scale=False,
                network_required=False,
            )
        return TTSBackendDescriptor(
            backend_id=cls.backend_id,
            state=MediaState.AVAILABLE if probe.available else MediaState.UNAVAILABLE,
            role="accessibility_runtime",
            canonical_production=False,
            capabilities=capabilities,
        )
