from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Mapping

from kodepoia.release.identity import ReleaseIdentity

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TerminalReleaseFreezeError(ValueError):
    """Raised when the terminal V2 release freeze is internally inconsistent."""


@dataclass(frozen=True, slots=True)
class TerminalReleaseFreeze:
    schema_version: int
    product: str
    package: str
    terminal_scope_base_sha: str
    payload: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> TerminalReleaseFreeze:
        freeze = cls(
            schema_version=int(payload.get("schema_version", 0)),
            product=str(payload.get("product", "")),
            package=str(payload.get("package", "")),
            terminal_scope_base_sha=str(payload.get("terminal_scope_base_sha", "")).lower(),
            payload=payload,
        )
        freeze.validate()
        return freeze

    def _mapping(self, key: str) -> Mapping[str, Any]:
        value = self.payload.get(key)
        if not isinstance(value, Mapping):
            raise TerminalReleaseFreezeError(f"{key} must be an object")
        return value

    @property
    def public_baseline(self) -> Mapping[str, Any]:
        return self._mapping("public_baseline")

    @property
    def successor(self) -> Mapping[str, Any]:
        return self._mapping("successor")

    @property
    def transition(self) -> Mapping[str, Any]:
        return self._mapping("transition")

    @property
    def windows_installer(self) -> Mapping[str, Any]:
        return self._mapping("windows_installer")

    @property
    def authenticode(self) -> Mapping[str, Any]:
        return self._mapping("authenticode")

    @property
    def winget(self) -> Mapping[str, Any]:
        return self._mapping("winget")

    @property
    def no_new_feature_freeze(self) -> Mapping[str, Any]:
        return self._mapping("no_new_feature_freeze")

    @property
    def effects(self) -> Mapping[str, Any]:
        return self._mapping("effects")

    @property
    def successor_identity(self) -> ReleaseIdentity:
        successor = self.successor
        version = successor.get("version")
        if not isinstance(version, Mapping):
            raise TerminalReleaseFreezeError("successor.version must be an object")
        return ReleaseIdentity(
            schema_version=1,
            product=self.product,
            package=self.package,
            channel=str(successor.get("channel", "")),
            build_type=str(successor.get("build_type", "")),
            source_binding=str(successor.get("source_binding", "")),
            major=int(version.get("major", -1)),
            minor=int(version.get("minor", -1)),
            patch=int(version.get("patch", -1)),
            stage=str(version.get("stage", "")),
            serial=int(version.get("serial", -1)),
        )

    def validate(self) -> None:
        if self.schema_version != 1:
            raise TerminalReleaseFreezeError("unsupported terminal release freeze schema")
        if self.product != "Kodepoia" or self.package != "kodepoia":
            raise TerminalReleaseFreezeError("terminal release product/package identity mismatch")
        if not _SHA_RE.fullmatch(self.terminal_scope_base_sha):
            raise TerminalReleaseFreezeError("terminal_scope_base_sha must be an exact Git SHA")

        baseline = self.public_baseline
        if baseline.get("public_version") != "1.1.0-rc8":
            raise TerminalReleaseFreezeError("public baseline must remain 1.1.0-rc8")
        if baseline.get("tag") != "v1.1.0-rc8" or baseline.get("channel") != "beta":
            raise TerminalReleaseFreezeError("public baseline tag/channel mismatch")
        if not _SHA_RE.fullmatch(str(baseline.get("source_sha", ""))):
            raise TerminalReleaseFreezeError("public baseline source SHA is invalid")
        if not _SHA256_RE.fullmatch(str(baseline.get("installer_sha256", ""))):
            raise TerminalReleaseFreezeError("public baseline installer SHA-256 is invalid")
        if baseline.get("production_signed") is not False:
            raise TerminalReleaseFreezeError("rc8 baseline must preserve unsigned truth")

        successor = self.successor
        identity = self.successor_identity
        if identity.public_version != "1.1.0" or identity.pep440_version != "1.1.0":
            raise TerminalReleaseFreezeError("successor must be the final 1.1.0 release")
        if successor.get("tag") != "v1.1.0":
            raise TerminalReleaseFreezeError("successor tag must be v1.1.0")
        if successor.get("candidate_source_freeze_phase") != "V2.6.3":
            raise TerminalReleaseFreezeError("candidate source must remain deferred to V2.6.3")
        if successor.get("candidate_source_sha") is not None:
            raise TerminalReleaseFreezeError("candidate source SHA cannot be preclaimed in V2.6.1")

        transition = self.transition
        if transition.get("from_public_version") != "1.1.0-rc8":
            raise TerminalReleaseFreezeError("transition baseline mismatch")
        if transition.get("to_public_version") != "1.1.0":
            raise TerminalReleaseFreezeError("transition target mismatch")
        if transition.get("monotonic") is not True:
            raise TerminalReleaseFreezeError("terminal transition must be monotonic")
        if transition.get("rc8_to_stable_rehearsal_channel") != "stable":
            raise TerminalReleaseFreezeError("rc8 terminal rehearsal must explicitly select stable")

        installer = self.windows_installer
        if installer.get("filename") != "KodepoiaSetup.exe":
            raise TerminalReleaseFreezeError("Windows installer filename changed")
        if installer.get("app_id") != "{A67EEAB5-46C2-4B21-A169-7E17275DE2F0}":
            raise TerminalReleaseFreezeError("Windows installer AppId changed")
        expected_target = "channels/stable/windows-x86_64/1.1.0/{source_sha}/KodepoiaSetup.exe"
        if installer.get("target_path_template") != expected_target:
            raise TerminalReleaseFreezeError("stable update target identity mismatch")

        signing = self.authenticode
        if signing.get("production_signing_verified") is not False:
            raise TerminalReleaseFreezeError("V2.6.1 must not claim production signing")
        if signing.get("production_signing_secret_provisioning_authorized") is not False:
            raise TerminalReleaseFreezeError("V2.6.1 cannot authorize signing-secret provisioning")
        if signing.get("unsigned_tuf_policy") != "allow-unsigned":
            raise TerminalReleaseFreezeError("unsigned posture must use existing target-scoped policy")
        if signing.get("unsigned_policy_scope") != "exact-target-only":
            raise TerminalReleaseFreezeError("unsigned policy must remain exact-target-scoped")

        winget = self.winget
        if winget.get("decision") != "out" or winget.get("public_submission_authorized") is not False:
            raise TerminalReleaseFreezeError("WinGet must be explicitly out for v1.1.0")

        freeze = self.no_new_feature_freeze
        if freeze.get("effective_after_v2_6_1_normalization") is not True:
            raise TerminalReleaseFreezeError("no-new-feature freeze activation is missing")
        if freeze.get("new_product_capability_allowed") is not False:
            raise TerminalReleaseFreezeError("new product capabilities must be frozen")
        if freeze.get("v2_7_authorized") is not False or freeze.get("r20_7_authorized") is not False:
            raise TerminalReleaseFreezeError("terminal scope cannot authorize V2.7 or R20.7")

        if any(value is not False for value in self.effects.values()):
            raise TerminalReleaseFreezeError("V2.6.1 cannot authorize live publication effects")

    def assert_transition_from(self, baseline: ReleaseIdentity) -> None:
        if baseline.public_version != self.public_baseline.get("public_version"):
            raise TerminalReleaseFreezeError("runtime baseline does not match frozen public baseline")
        target = self.successor_identity
        if not baseline.can_transition_to(target):
            raise TerminalReleaseFreezeError("frozen successor is not a valid monotonic transition")


def load_terminal_release_freeze() -> TerminalReleaseFreeze:
    resource = files("kodepoia.release").joinpath("terminal_release_freeze.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TerminalReleaseFreezeError("terminal release freeze root must be an object")
    return TerminalReleaseFreeze.from_mapping(payload)


TERMINAL_RELEASE_FREEZE = load_terminal_release_freeze()


__all__ = [
    "TERMINAL_RELEASE_FREEZE",
    "TerminalReleaseFreeze",
    "TerminalReleaseFreezeError",
    "load_terminal_release_freeze",
]
