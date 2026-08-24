from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..contracts import MediaState, bounded_text, sha256_hex, stable_id
from ..serialization import canonical_sha256
from .profiles import normalize_locale


class AllowedUse(StrEnum):
    INTERNAL = "internal"
    NONCOMMERCIAL = "noncommercial"
    COMMERCIAL = "commercial"
    REDISTRIBUTION = "redistribution"
    DERIVATIVE = "derivative"


@dataclass(frozen=True, slots=True)
class RightsDeclaration:
    provenance_id: str
    license_id: str
    allowed_uses: tuple[AllowedUse, ...]
    source_uri_id: str | None = None
    authorization_ref: str | None = None
    requires_authorization: bool = False
    state: MediaState = MediaState.AVAILABLE

    def __post_init__(self) -> None:
        stable_id(self.provenance_id, field="provenance_id")
        stable_id(self.license_id, field="license_id")
        uses = tuple(sorted(set(self.allowed_uses), key=lambda item: item.value))
        if not uses:
            raise ValueError("allowed_uses must not be empty")
        object.__setattr__(self, "allowed_uses", uses)
        if self.source_uri_id is not None:
            stable_id(self.source_uri_id, field="source_uri_id")
        if self.authorization_ref is not None:
            stable_id(self.authorization_ref, field="authorization_ref")
        if self.requires_authorization and self.authorization_ref is None:
            raise ValueError("authorization_ref is required")
        if self.state not in {MediaState.AVAILABLE, MediaState.RIGHTS_BLOCKED}:
            raise ValueError("rights state must be AVAILABLE or RIGHTS_BLOCKED")

    def permits(self, use: AllowedUse) -> bool:
        return self.state is MediaState.AVAILABLE and use in self.allowed_uses

    def canonical(self) -> dict[str, Any]:
        return {
            "provenance_id": self.provenance_id,
            "license_id": self.license_id,
            "allowed_uses": [item.value for item in self.allowed_uses],
            "source_uri_id": self.source_uri_id,
            "authorization_ref": self.authorization_ref,
            "requires_authorization": self.requires_authorization,
            "state": self.state.value,
        }


@dataclass(frozen=True, slots=True)
class VoiceModelBinding:
    binding_id: str
    backend_id: str
    model_sha256: str
    config_sha256: str
    locale: str
    rights: RightsDeclaration
    speaker_id: str | None = None
    display_label: str = "Synthetic voice"

    def __post_init__(self) -> None:
        stable_id(self.binding_id, field="binding_id")
        stable_id(self.backend_id, field="backend_id")
        sha256_hex(self.model_sha256, field="model_sha256")
        sha256_hex(self.config_sha256, field="config_sha256")
        object.__setattr__(self, "locale", normalize_locale(self.locale))
        if self.speaker_id is not None:
            stable_id(self.speaker_id, field="speaker_id")
        bounded_text(self.display_label, field="display_label", maximum=128)

    def require_use(self, use: AllowedUse) -> None:
        if not self.rights.permits(use):
            raise PermissionError(f"voice model binding is not permitted for {use.value}")

    @property
    def state(self) -> MediaState:
        return MediaState.AVAILABLE if self.rights.state is MediaState.AVAILABLE else MediaState.RIGHTS_BLOCKED

    def canonical(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "backend_id": self.backend_id,
            "model_sha256": self.model_sha256,
            "config_sha256": self.config_sha256,
            "locale": self.locale,
            "rights": self.rights.canonical(),
            "speaker_id": self.speaker_id,
            "display_label": self.display_label,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
