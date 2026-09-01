from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

from kodepoia.core.permissions import Capability, PermissionSet
from kodepoia.core.trust import TrustMetadata, TrustOrigin

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ToolLifecycle(StrEnum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    TRUSTED = "trusted"
    QUARANTINED = "quarantined"
    REVOKED = "revoked"


class ToolDecisionKind(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _require_digest(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return normalized


@dataclass(frozen=True, slots=True)
class ToolIdentity:
    stable_id: str
    kind: str
    version: str
    artifact_digest: str
    issuer: str = ""
    audience: str = ""

    def __post_init__(self) -> None:
        if not self.stable_id.strip():
            raise ValueError("stable_id is required")
        if not self.kind.strip():
            raise ValueError("tool kind is required")
        if not self.version.strip():
            raise ValueError("tool version is required")
        object.__setattr__(self, "artifact_digest", _require_digest(self.artifact_digest, "artifact_digest"))

    @property
    def fingerprint(self) -> str:
        return _sha256_text(
            _canonical_json(
                {
                    "stable_id": self.stable_id,
                    "kind": self.kind,
                    "version": self.version,
                    "artifact_digest": self.artifact_digest,
                    "issuer": self.issuer,
                    "audience": self.audience,
                }
            )
        )


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    identity: ToolIdentity
    name: str
    description: str
    input_schema: Mapping[str, Any]

    @property
    def digest(self) -> str:
        return _sha256_text(
            _canonical_json(
                {
                    "identity_fingerprint": self.identity.fingerprint,
                    "name": self.name,
                    "description": self.description,
                    "input_schema": self.input_schema,
                }
            )
        )

    def metadata_trust(self) -> TrustMetadata:
        return TrustMetadata.untrusted(
            TrustOrigin.TOOL_OUTPUT,
            source=self.identity.stable_id,
            content=self.digest,
        )


@dataclass(frozen=True, slots=True)
class ToolTrustRecord:
    stable_id: str
    identity_fingerprint: str
    definition_digest: str
    allowed_capabilities: tuple[Capability, ...]
    lifecycle: ToolLifecycle


@dataclass(frozen=True, slots=True)
class InvocationGrant:
    grant_id: str
    stable_id: str
    identity_fingerprint: str
    definition_digest: str
    operation: str
    capabilities: tuple[Capability, ...]
    intent_digest: str


@dataclass(frozen=True, slots=True)
class ToolAuthorizationDecision:
    kind: ToolDecisionKind
    reason: str
    stable_id: str
    lifecycle: ToolLifecycle

    @property
    def allowed(self) -> bool:
        return self.kind is ToolDecisionKind.ALLOW


class ToolTrustRegistry:
    """Deny-by-default trust and invocation authority for plugin/MCP/tool identities."""

    def __init__(self, permissions: PermissionSet) -> None:
        self.permissions = permissions
        self._records: dict[str, ToolTrustRecord] = {}
        self._grants: dict[str, InvocationGrant] = {}

    def discover(self, definition: ToolDefinition) -> ToolTrustRecord:
        record = ToolTrustRecord(
            stable_id=definition.identity.stable_id,
            identity_fingerprint=definition.identity.fingerprint,
            definition_digest=definition.digest,
            allowed_capabilities=(),
            lifecycle=ToolLifecycle.DISCOVERED,
        )
        self._records[record.stable_id] = record
        return record

    def register(self, definition: ToolDefinition) -> ToolTrustRecord:
        record = ToolTrustRecord(
            stable_id=definition.identity.stable_id,
            identity_fingerprint=definition.identity.fingerprint,
            definition_digest=definition.digest,
            allowed_capabilities=(),
            lifecycle=ToolLifecycle.REGISTERED,
        )
        self._records[record.stable_id] = record
        return record

    def trust(
        self,
        stable_id: str,
        *,
        allowed_capabilities: Sequence[Capability],
    ) -> ToolTrustRecord:
        record = self._records.get(stable_id)
        if record is None:
            raise ValueError("tool must be registered before trust can be granted")
        capabilities = tuple(sorted(set(allowed_capabilities), key=lambda item: item.value))
        record = replace(
            record,
            allowed_capabilities=capabilities,
            lifecycle=ToolLifecycle.TRUSTED,
        )
        self._records[stable_id] = record
        return record

    def approve_invocation(
        self,
        stable_id: str,
        *,
        operation: str,
        capabilities: Sequence[Capability],
        intent_digest: str,
    ) -> InvocationGrant:
        record = self._records.get(stable_id)
        if record is None or record.lifecycle is not ToolLifecycle.TRUSTED:
            raise ValueError("invocation approval requires an explicitly trusted tool")
        requested = tuple(sorted(set(capabilities), key=lambda item: item.value))
        if not set(requested).issubset(record.allowed_capabilities):
            raise ValueError("invocation approval cannot widen trusted capability scope")
        normalized_intent = _require_digest(intent_digest, "intent_digest")
        grant_id = _sha256_text(
            _canonical_json(
                {
                    "stable_id": stable_id,
                    "identity_fingerprint": record.identity_fingerprint,
                    "definition_digest": record.definition_digest,
                    "operation": operation,
                    "capabilities": [item.value for item in requested],
                    "intent_digest": normalized_intent,
                }
            )
        )
        grant = InvocationGrant(
            grant_id=grant_id,
            stable_id=stable_id,
            identity_fingerprint=record.identity_fingerprint,
            definition_digest=record.definition_digest,
            operation=operation,
            capabilities=requested,
            intent_digest=normalized_intent,
        )
        self._grants[grant_id] = grant
        return grant

    def revoke(self, stable_id: str) -> ToolTrustRecord:
        record = self._records.get(stable_id)
        if record is None:
            raise ValueError("unknown tool")
        record = replace(record, lifecycle=ToolLifecycle.REVOKED)
        self._records[stable_id] = record
        self._grants = {
            grant_id: grant
            for grant_id, grant in self._grants.items()
            if grant.stable_id != stable_id
        }
        return record

    def observe_definition(self, definition: ToolDefinition) -> ToolTrustRecord:
        stable_id = definition.identity.stable_id
        record = self._records.get(stable_id)
        if record is None:
            return self.discover(definition)
        if (
            definition.identity.fingerprint != record.identity_fingerprint
            or definition.digest != record.definition_digest
        ):
            record = replace(record, lifecycle=ToolLifecycle.QUARANTINED)
            self._records[stable_id] = record
        return record

    def _deny(self, stable_id: str, reason: str) -> ToolAuthorizationDecision:
        record = self._records.get(stable_id)
        lifecycle = record.lifecycle if record is not None else ToolLifecycle.DISCOVERED
        return ToolAuthorizationDecision(ToolDecisionKind.DENY, reason, stable_id, lifecycle)

    def authorize(
        self,
        definition: ToolDefinition,
        *,
        operation: str,
        capabilities: Sequence[Capability],
        intent_digest: str,
        grant_id: str,
        credential_issuer: str = "",
        credential_audience: str = "",
    ) -> ToolAuthorizationDecision:
        stable_id = definition.identity.stable_id
        record = self._records.get(stable_id)
        if record is None:
            return self._deny(stable_id, "Unknown tool identity is denied by default.")
        if record.lifecycle is not ToolLifecycle.TRUSTED:
            return self._deny(stable_id, f"Tool lifecycle is {record.lifecycle.value}, not trusted.")
        if definition.identity.fingerprint != record.identity_fingerprint:
            self._records[stable_id] = replace(record, lifecycle=ToolLifecycle.QUARANTINED)
            return self._deny(stable_id, "Tool identity/version/artifact changed after approval.")
        if definition.digest != record.definition_digest:
            self._records[stable_id] = replace(record, lifecycle=ToolLifecycle.QUARANTINED)
            return self._deny(stable_id, "Pinned tool definition/schema digest changed after approval.")

        requested = tuple(sorted(set(capabilities), key=lambda item: item.value))
        if not set(requested).issubset(record.allowed_capabilities):
            return self._deny(stable_id, "Requested capability exceeds the trusted tool scope.")
        for capability in requested:
            if capability not in self.permissions.grants:
                return self._deny(stable_id, f"Runtime permission is not granted: {capability.value}.")

        try:
            normalized_intent = _require_digest(intent_digest, "intent_digest")
        except ValueError as exc:
            return self._deny(stable_id, str(exc))
        grant = self._grants.get(grant_id)
        if grant is None:
            return self._deny(stable_id, "Missing or revoked invocation approval.")
        if (
            grant.stable_id != stable_id
            or grant.identity_fingerprint != record.identity_fingerprint
            or grant.definition_digest != record.definition_digest
            or grant.operation != operation
            or grant.capabilities != requested
            or grant.intent_digest != normalized_intent
        ):
            return self._deny(stable_id, "Invocation approval does not bind this exact call.")

        if credential_issuer or credential_audience:
            if not definition.identity.issuer or credential_issuer != definition.identity.issuer:
                return self._deny(stable_id, "Credential issuer is not bound to this tool identity.")
            if not definition.identity.audience or credential_audience != definition.identity.audience:
                return self._deny(stable_id, "Credential audience is not bound to this tool identity.")

        return ToolAuthorizationDecision(
            ToolDecisionKind.ALLOW,
            "Trusted identity, pinned definition, least-privilege scope and exact invocation approval verified.",
            stable_id,
            record.lifecycle,
        )

    def tool_output_trust(self, definition: ToolDefinition, payload: Any) -> TrustMetadata:
        return TrustMetadata.untrusted(
            TrustOrigin.TOOL_OUTPUT,
            source=definition.identity.stable_id,
            content=_canonical_json(payload),
        )
