from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TrustOrigin(StrEnum):
    SYSTEM = "system"
    USER = "user"
    REPOSITORY = "repository"
    RESEARCH = "research"
    DOCUMENT = "document"
    WEB = "web"
    TOOL_OUTPUT = "tool_output"
    MODEL_OUTPUT = "model_output"
    MEMORY = "memory"
    UNKNOWN = "unknown"


class TrustLevel(StrEnum):
    TRUSTED = "trusted"
    USER_AUTHORIZED = "user_authorized"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"


class ContentAuthority(StrEnum):
    POLICY = "policy"
    USER_INTENT = "user_intent"
    DATA_ONLY = "data_only"


class AuthorityEffect(StrEnum):
    INSPECT_DATA = "inspect_data"
    POLICY_MUTATION = "policy_mutation"
    ROADMAP_AUTHORITY = "roadmap_authority"
    PERMISSION_GRANT = "permission_grant"
    SUPPRESS_CONFIRMATION = "suppress_confirmation"
    FILESYSTEM_SCOPE_WIDEN = "filesystem_scope_widen"
    NETWORK_SCOPE_WIDEN = "network_scope_widen"
    PRIVILEGED_TOOL_TRIGGER = "privileged_tool_trigger"
    PROCESS_EXECUTION = "process_execution"
    SECRET_ACCESS = "secret_access"


_EXTERNAL_ORIGINS = frozenset(
    {
        TrustOrigin.REPOSITORY,
        TrustOrigin.RESEARCH,
        TrustOrigin.DOCUMENT,
        TrustOrigin.WEB,
        TrustOrigin.TOOL_OUTPUT,
        TrustOrigin.MODEL_OUTPUT,
        TrustOrigin.MEMORY,
    }
)


def provenance_sha256(*parts: str) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TrustMetadata:
    origin: TrustOrigin
    level: TrustLevel
    authority: ContentAuthority
    provenance_id: str

    def __post_init__(self) -> None:
        provenance = self.provenance_id.strip().lower()
        if not _SHA256_RE.fullmatch(provenance):
            raise ValueError("trust provenance_id must be a lowercase SHA-256 digest")
        if self.origin in _EXTERNAL_ORIGINS:
            if self.level is not TrustLevel.UNTRUSTED:
                raise ValueError("external content cannot be promoted above untrusted")
            if self.authority is not ContentAuthority.DATA_ONLY:
                raise ValueError("external content must remain data-only")
        if self.origin is TrustOrigin.SYSTEM and (
            self.level is not TrustLevel.TRUSTED
            or self.authority is not ContentAuthority.POLICY
        ):
            raise ValueError("system trust metadata must be trusted policy")
        if self.origin is TrustOrigin.USER and (
            self.level is not TrustLevel.USER_AUTHORIZED
            or self.authority is not ContentAuthority.USER_INTENT
        ):
            raise ValueError("user trust metadata must be user-authorized intent")
        if self.origin is TrustOrigin.UNKNOWN and (
            self.level is not TrustLevel.UNKNOWN
            or self.authority is not ContentAuthority.DATA_ONLY
        ):
            raise ValueError("unknown provenance must fail closed as data-only")
        object.__setattr__(self, "provenance_id", provenance)

    @classmethod
    def untrusted(
        cls,
        origin: TrustOrigin,
        *,
        provenance_id: str | None = None,
        source: str = "",
        content: str = "",
    ) -> TrustMetadata:
        if origin not in _EXTERNAL_ORIGINS:
            raise ValueError("untrusted() requires an external origin")
        provenance = provenance_id or provenance_sha256(origin.value, source, content)
        return cls(origin, TrustLevel.UNTRUSTED, ContentAuthority.DATA_ONLY, provenance)

    @classmethod
    def user(cls, *, provenance_id: str) -> TrustMetadata:
        return cls(
            TrustOrigin.USER,
            TrustLevel.USER_AUTHORIZED,
            ContentAuthority.USER_INTENT,
            provenance_id,
        )

    @classmethod
    def system(cls, *, provenance_id: str) -> TrustMetadata:
        return cls(
            TrustOrigin.SYSTEM,
            TrustLevel.TRUSTED,
            ContentAuthority.POLICY,
            provenance_id,
        )

    @classmethod
    def unknown(cls, *, provenance_id: str) -> TrustMetadata:
        return cls(
            TrustOrigin.UNKNOWN,
            TrustLevel.UNKNOWN,
            ContentAuthority.DATA_ONLY,
            provenance_id,
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> TrustMetadata:
        if payload is None:
            raise ValueError("trust metadata is required at a content-driven authority boundary")
        if not isinstance(payload, Mapping):
            raise TypeError("trust metadata must be a mapping")
        try:
            origin = TrustOrigin(str(payload["origin"]))
            level = TrustLevel(str(payload["level"]))
            authority = ContentAuthority(str(payload["authority"]))
            provenance_id = str(payload["provenance_id"])
        except KeyError as exc:
            raise ValueError(f"missing trust metadata field: {exc.args[0]}") from exc
        return cls(origin, level, authority, provenance_id)

    def to_dict(self) -> dict[str, str]:
        return {
            "origin": self.origin.value,
            "level": self.level.value,
            "authority": self.authority.value,
            "provenance_id": self.provenance_id,
        }


@dataclass(frozen=True, slots=True)
class TrustDecision:
    effect: AuthorityEffect
    allowed: bool
    reason: str


class TrustBoundary:
    """Deterministic authority boundary. Content never self-promotes its own trust."""

    _SYSTEM_ONLY = frozenset(
        {
            AuthorityEffect.POLICY_MUTATION,
            AuthorityEffect.ROADMAP_AUTHORITY,
            AuthorityEffect.SUPPRESS_CONFIRMATION,
        }
    )
    _USER_OR_SYSTEM = frozenset(
        {
            AuthorityEffect.PERMISSION_GRANT,
            AuthorityEffect.FILESYSTEM_SCOPE_WIDEN,
            AuthorityEffect.NETWORK_SCOPE_WIDEN,
            AuthorityEffect.PRIVILEGED_TOOL_TRIGGER,
            AuthorityEffect.PROCESS_EXECUTION,
            AuthorityEffect.SECRET_ACCESS,
        }
    )

    def evaluate(self, metadata: TrustMetadata | None, effect: AuthorityEffect) -> TrustDecision:
        if effect is AuthorityEffect.INSPECT_DATA:
            if metadata is None:
                return TrustDecision(
                    effect,
                    True,
                    "Unlabelled content may be inspected only as data.",
                )
            reason = (
                f"{metadata.origin.value} content remains inspectable "
                f"as {metadata.authority.value}."
            )
            return TrustDecision(effect, True, reason)
        if metadata is None:
            return TrustDecision(effect, False, "Missing trust provenance fails closed.")
        if metadata.origin is TrustOrigin.UNKNOWN or metadata.level is TrustLevel.UNKNOWN:
            return TrustDecision(
                effect,
                False,
                "Unknown trust provenance cannot authorize privileged effects.",
            )
        if metadata.authority is ContentAuthority.DATA_ONLY:
            return TrustDecision(effect, False, "Data-only content cannot acquire authority.")
        if effect in self._SYSTEM_ONLY:
            allowed = (
                metadata.origin is TrustOrigin.SYSTEM
                and metadata.authority is ContentAuthority.POLICY
            )
            reason = (
                "System policy authority verified."
                if allowed
                else "System policy authority required."
            )
            return TrustDecision(effect, allowed, reason)
        if effect in self._USER_OR_SYSTEM:
            allowed = metadata.origin in {TrustOrigin.SYSTEM, TrustOrigin.USER}
            reason = (
                "Explicit user/system authority verified."
                if allowed
                else "Explicit user/system authority required."
            )
            return TrustDecision(effect, allowed, reason)
        return TrustDecision(effect, False, "Unknown authority effect fails closed.")


def external_origin_from_tags(tags: tuple[str, ...]) -> TrustOrigin | None:
    normalized = {tag.strip().lower().replace("-", "_") for tag in tags}
    for tag, origin in (
        ("research", TrustOrigin.RESEARCH),
        ("web", TrustOrigin.WEB),
        ("document", TrustOrigin.DOCUMENT),
        ("repository", TrustOrigin.REPOSITORY),
        ("tool_output", TrustOrigin.TOOL_OUTPUT),
        ("model_output", TrustOrigin.MODEL_OUTPUT),
        ("memory", TrustOrigin.MEMORY),
    ):
        if tag in normalized:
            return origin
    if "external" in normalized or "untrusted" in normalized:
        return TrustOrigin.UNKNOWN
    return None
