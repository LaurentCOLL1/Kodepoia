from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from kodepoia.kodecode.workspace import WorkspaceBoundary

_SCHEMA_VERSION = 1
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_USES_RE = re.compile(r"^\s*-?\s*uses:\s*[\"']?([^\"'\s#]+)", re.MULTILINE)
_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")
_SECRET_RE = re.compile(
    r"(?i)(?:password|passwd|secret|token|authorization|api[_-]?key|private[_-]?key)"
)


class SupplyChainStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class AttestationState(StrEnum):
    NOT_EXERCISED = "not_exercised"
    VERIFIED = "verified"
    UNAVAILABLE = "unavailable"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha40(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if not _SHA40_RE.fullmatch(normalized):
        raise ValueError(f"{field} must be a 40-character Git commit SHA")
    return normalized


def _require_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _action_repository(action: str) -> str:
    parts = action.split("/")
    if len(parts) < 2:
        raise ValueError(f"invalid external action reference: {action}")
    return "/".join(parts[:2])


@dataclass(frozen=True, slots=True)
class ActionPin:
    repository: str
    source_ref: str
    commit_sha: str

    def __post_init__(self) -> None:
        if self.repository.count("/") != 1:
            raise ValueError("action pin repository must be owner/repository")
        if not self.source_ref.strip():
            raise ValueError("action pin requires source_ref")
        object.__setattr__(self, "commit_sha", _require_sha40(self.commit_sha, field="action pin"))

    def to_dict(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "source_ref": self.source_ref,
            "commit_sha": self.commit_sha,
        }


@dataclass(frozen=True, slots=True)
class SupplyChainPolicy:
    policy_id: str
    pins: Mapping[str, ActionPin]
    require_explicit_permissions: bool
    required_contents_permission: str
    allow_write_workflows: tuple[str, ...]
    require_exact_source_sha: bool
    require_build_manifest_binding: bool
    require_bom_evidence_binding: bool
    external_attestation_required_for_core: bool
    external_attestation_semantics: str
    schema_version: int = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported supply-chain policy schema")
        if not self.policy_id.strip():
            raise ValueError("supply-chain policy requires policy_id")
        if self.required_contents_permission not in {"read", "none"}:
            raise ValueError("required contents permission must be read or none")
        if self.external_attestation_semantics != "provenance_only_not_security_verdict":
            raise ValueError("external attestation semantics must remain provenance-only")
        object.__setattr__(self, "pins", dict(sorted(self.pins.items())))
        object.__setattr__(self, "allow_write_workflows", tuple(sorted(self.allow_write_workflows)))

    @property
    def digest_sha256(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "pins": {name: pin.to_dict() for name, pin in sorted(self.pins.items())},
            "require_explicit_permissions": self.require_explicit_permissions,
            "required_contents_permission": self.required_contents_permission,
            "allow_write_workflows": list(self.allow_write_workflows),
            "require_exact_source_sha": self.require_exact_source_sha,
            "require_build_manifest_binding": self.require_build_manifest_binding,
            "require_bom_evidence_binding": self.require_bom_evidence_binding,
            "external_attestation_required_for_core": self.external_attestation_required_for_core,
            "external_attestation_semantics": self.external_attestation_semantics,
        }
        return _sha256_bytes(_canonical_json(payload).encode("utf-8"))

    @classmethod
    def load(cls, path: str | Path) -> SupplyChainPolicy:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("supply-chain policy must be a JSON object")
        raw_pins = payload.get("external_action_pins")
        if not isinstance(raw_pins, dict) or not raw_pins:
            raise ValueError("supply-chain policy requires external_action_pins")
        pins = {
            str(repository): ActionPin(
                str(repository),
                str(item["source_ref"]),
                str(item["commit_sha"]),
            )
            for repository, item in raw_pins.items()
        }
        workflow = dict(payload.get("workflow_policy") or {})
        provenance = dict(payload.get("provenance_policy") or {})
        return cls(
            policy_id=str(payload["policy_id"]),
            pins=pins,
            require_explicit_permissions=bool(workflow.get("require_explicit_permissions", True)),
            required_contents_permission=str(workflow.get("required_contents_permission", "read")),
            allow_write_workflows=tuple(str(v) for v in workflow.get("allow_write_workflows", [])),
            require_exact_source_sha=bool(provenance.get("require_exact_source_sha", True)),
            require_build_manifest_binding=bool(provenance.get("require_build_manifest_binding", True)),
            require_bom_evidence_binding=bool(provenance.get("require_bom_evidence_binding", True)),
            external_attestation_required_for_core=bool(
                provenance.get("external_attestation_required_for_core", False)
            ),
            external_attestation_semantics=str(
                provenance.get("external_attestation_semantics", "")
            ),
            schema_version=int(payload.get("schema_version", 0)),
        )


@dataclass(frozen=True, slots=True)
class DependencyInput:
    group: str
    name: str
    requirement: str
    declaration_sha256: str

    def __post_init__(self) -> None:
        if not self.group.strip() or not self.name.strip() or not self.requirement.strip():
            raise ValueError("dependency input fields must be non-empty")
        object.__setattr__(
            self,
            "declaration_sha256",
            _require_sha256(self.declaration_sha256, field="dependency declaration"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "group": self.group,
            "name": self.name,
            "requirement": self.requirement,
            "declaration_sha256": self.declaration_sha256,
        }


@dataclass(frozen=True, slots=True)
class WorkflowAction:
    workflow: str
    action: str
    repository: str
    commit_sha: str

    def __post_init__(self) -> None:
        if not self.workflow.strip() or not self.action.strip() or not self.repository.strip():
            raise ValueError("workflow action fields must be non-empty")
        object.__setattr__(self, "commit_sha", _require_sha40(self.commit_sha, field="workflow action"))

    def to_dict(self) -> dict[str, str]:
        return {
            "workflow": self.workflow,
            "action": self.action,
            "repository": self.repository,
            "commit_sha": self.commit_sha,
        }


@dataclass(frozen=True, slots=True)
class WorkflowAudit:
    workflow_count: int
    actions: tuple[WorkflowAction, ...]
    permissions: Mapping[str, Mapping[str, str]]
    blockers: tuple[str, ...]
    evidence_sha256: str

    @property
    def status(self) -> SupplyChainStatus:
        return SupplyChainStatus.FAIL if self.blockers else SupplyChainStatus.PASS

    def _payload(self) -> dict[str, Any]:
        return {
            "workflow_count": self.workflow_count,
            "actions": [item.to_dict() for item in self.actions],
            "permissions": {
                name: dict(sorted(values.items())) for name, values in sorted(self.permissions.items())
            },
            "blockers": list(self.blockers),
        }

    def validate(self) -> None:
        expected = _sha256_bytes(_canonical_json(self._payload()).encode("utf-8"))
        if self.evidence_sha256 != expected:
            raise ValueError("workflow audit evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return self._payload() | {
            "status": self.status.value,
            "evidence_sha256": self.evidence_sha256,
        }


def _parse_permissions(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^permissions:\s*(.*)$", line)
        if match is None:
            continue
        inline = match.group(1).strip()
        if inline:
            return {"__inline__": inline}
        values: dict[str, str] = {}
        for child in lines[index + 1 :]:
            if not child.startswith((" ", "\t")):
                break
            child_match = re.match(r"^\s+([A-Za-z0-9_-]+):\s*([A-Za-z0-9_-]+)\s*$", child)
            if child_match:
                values[child_match.group(1)] = child_match.group(2)
        return values
    return None


def audit_workflows(project_root: str | Path, policy: SupplyChainPolicy) -> WorkflowAudit:
    root = Path(project_root).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    workflow_root = boundary.resolve(".github/workflows", must_exist=True)
    paths = sorted(
        (path for path in workflow_root.glob("*.y*ml") if path.is_file()),
        key=lambda item: item.name,
    )
    actions: list[WorkflowAction] = []
    permissions: dict[str, dict[str, str]] = {}
    blockers: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        parsed_permissions = _parse_permissions(text)
        if parsed_permissions is None:
            permissions[relative] = {}
            if policy.require_explicit_permissions:
                blockers.append(f"workflow_permissions_missing:{relative}")
        else:
            permissions[relative] = parsed_permissions
            contents = parsed_permissions.get("contents")
            if contents != policy.required_contents_permission:
                if relative not in policy.allow_write_workflows:
                    blockers.append(f"workflow_contents_permission:{relative}:{contents or 'missing'}")
            if any(value == "write" for value in parsed_permissions.values()):
                if relative not in policy.allow_write_workflows:
                    blockers.append(f"workflow_write_permission:{relative}")
        for reference in _USES_RE.findall(text):
            if reference.startswith("./"):
                continue
            if "@" not in reference:
                blockers.append(f"workflow_action_unversioned:{relative}:{reference}")
                continue
            action, ref = reference.rsplit("@", 1)
            repository = _action_repository(action)
            if not _SHA40_RE.fullmatch(ref.lower()):
                blockers.append(f"workflow_action_mutable_ref:{relative}:{reference}")
                continue
            pin = policy.pins.get(repository)
            if pin is None:
                blockers.append(f"workflow_action_unapproved:{relative}:{repository}")
                continue
            normalized_ref = ref.lower()
            if normalized_ref != pin.commit_sha:
                blockers.append(f"workflow_action_pin_drift:{relative}:{repository}:{normalized_ref}")
            actions.append(WorkflowAction(relative, action, repository, normalized_ref))
    actions.sort(key=lambda item: (item.workflow, item.action, item.commit_sha))
    blockers_tuple = tuple(sorted(set(blockers)))
    payload = {
        "workflow_count": len(paths),
        "actions": [item.to_dict() for item in actions],
        "permissions": {
            name: dict(sorted(values.items())) for name, values in sorted(permissions.items())
        },
        "blockers": list(blockers_tuple),
    }
    audit = WorkflowAudit(
        workflow_count=len(paths),
        actions=tuple(actions),
        permissions=permissions,
        blockers=blockers_tuple,
        evidence_sha256=_sha256_bytes(_canonical_json(payload).encode("utf-8")),
    )
    audit.validate()
    return audit


def declared_dependencies(project_root: str | Path) -> tuple[DependencyInput, ...]:
    root = Path(project_root).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    pyproject = boundary.resolve("pyproject.toml", must_exist=True)
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    entries: list[DependencyInput] = []

    def add(group: str, requirement: str) -> None:
        match = _REQ_NAME_RE.match(requirement)
        if match is None:
            raise ValueError(f"cannot determine dependency name: {requirement}")
        normalized = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        digest = _sha256_bytes(f"{group}\0{requirement}".encode("utf-8"))
        entries.append(DependencyInput(group, normalized, requirement, digest))

    for requirement in payload.get("build-system", {}).get("requires", []):
        add("build-system", str(requirement))
    project = payload.get("project", {})
    for requirement in project.get("dependencies", []):
        add("runtime", str(requirement))
    for group, requirements in sorted(project.get("optional-dependencies", {}).items()):
        for requirement in requirements:
            add(f"optional:{group}", str(requirement))
    entries.sort(key=lambda item: (item.group, item.name, item.requirement))
    return tuple(entries)


def repository_supply_chain_digest(project_root: str | Path) -> str:
    root = Path(project_root).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    candidates = [
        boundary.resolve("pyproject.toml", must_exist=True),
        boundary.resolve("configs/r16_supply_chain_policy.json", must_exist=True),
        boundary.resolve("src/kodepoia/quality/build.py", must_exist=True),
        boundary.resolve("src/kodepoia/quality/license_bom.py", must_exist=True),
        boundary.resolve("src/kodepoia/quality/supply_chain.py", must_exist=True),
    ]
    workflow_root = boundary.resolve(".github/workflows", must_exist=True)
    candidates.extend(sorted(path for path in workflow_root.glob("*.y*ml") if path.is_file()))
    digest = hashlib.sha256()
    for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class SupplyChainManifest:
    source_sha: str
    policy_sha256: str
    repository_input_sha256: str
    workflow_audit_sha256: str
    dependency_inventory_sha256: str
    build_manifest_evidence_sha256: str
    bom_evidence_sha256: str
    external_attestation: AttestationState
    status: SupplyChainStatus
    blockers: tuple[str, ...]
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported supply-chain manifest schema")
        object.__setattr__(self, "source_sha", _require_sha40(self.source_sha, field="source_sha"))
        for field_name in (
            "policy_sha256",
            "repository_input_sha256",
            "workflow_audit_sha256",
            "dependency_inventory_sha256",
            "build_manifest_evidence_sha256",
            "bom_evidence_sha256",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_sha256(getattr(self, field_name), field=field_name),
            )
        object.__setattr__(self, "blockers", tuple(sorted(set(self.blockers))))

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "policy_sha256": self.policy_sha256,
            "repository_input_sha256": self.repository_input_sha256,
            "workflow_audit_sha256": self.workflow_audit_sha256,
            "dependency_inventory_sha256": self.dependency_inventory_sha256,
            "build_manifest_evidence_sha256": self.build_manifest_evidence_sha256,
            "bom_evidence_sha256": self.bom_evidence_sha256,
            "external_attestation": self.external_attestation.value,
            "status": self.status.value,
            "blockers": list(self.blockers),
        }

    def validate(self) -> None:
        expected = _sha256_bytes(_canonical_json(self._payload()).encode("utf-8"))
        if self.evidence_sha256 != expected:
            raise ValueError("supply-chain manifest evidence hash mismatch")
        expected_status = SupplyChainStatus.FAIL if self.blockers else SupplyChainStatus.PASS
        if self.status is not expected_status:
            raise ValueError("supply-chain manifest status does not match blockers")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return self._payload() | {"evidence_sha256": self.evidence_sha256}

    @classmethod
    def build(
        cls,
        project_root: str | Path,
        *,
        source_sha: str,
        build_manifest_evidence_sha256: str,
        bom_evidence_sha256: str,
        external_attestation: AttestationState = AttestationState.NOT_EXERCISED,
    ) -> SupplyChainManifest:
        root = Path(project_root).resolve(strict=False)
        policy = SupplyChainPolicy.load(root / "configs/r16_supply_chain_policy.json")
        audit = audit_workflows(root, policy)
        dependencies = declared_dependencies(root)
        dependency_payload = {"dependencies": [item.to_dict() for item in dependencies]}
        dependency_digest = _sha256_bytes(_canonical_json(dependency_payload).encode("utf-8"))
        blockers = list(audit.blockers)
        if policy.external_attestation_required_for_core and external_attestation is not AttestationState.VERIFIED:
            blockers.append("external_attestation_required")
        provisional = cls(
            source_sha=source_sha,
            policy_sha256=policy.digest_sha256,
            repository_input_sha256=repository_supply_chain_digest(root),
            workflow_audit_sha256=audit.evidence_sha256,
            dependency_inventory_sha256=dependency_digest,
            build_manifest_evidence_sha256=build_manifest_evidence_sha256,
            bom_evidence_sha256=bom_evidence_sha256,
            external_attestation=external_attestation,
            status=SupplyChainStatus.FAIL if blockers else SupplyChainStatus.PASS,
            blockers=tuple(blockers),
            evidence_sha256="0" * 64,
        )
        digest = _sha256_bytes(_canonical_json(provisional._payload()).encode("utf-8"))
        manifest = cls(
            source_sha=provisional.source_sha,
            policy_sha256=provisional.policy_sha256,
            repository_input_sha256=provisional.repository_input_sha256,
            workflow_audit_sha256=provisional.workflow_audit_sha256,
            dependency_inventory_sha256=provisional.dependency_inventory_sha256,
            build_manifest_evidence_sha256=provisional.build_manifest_evidence_sha256,
            bom_evidence_sha256=provisional.bom_evidence_sha256,
            external_attestation=provisional.external_attestation,
            status=provisional.status,
            blockers=provisional.blockers,
            evidence_sha256=digest,
        )
        manifest.validate()
        return manifest

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SupplyChainManifest:
        manifest = cls(
            source_sha=str(payload["source_sha"]),
            policy_sha256=str(payload["policy_sha256"]),
            repository_input_sha256=str(payload["repository_input_sha256"]),
            workflow_audit_sha256=str(payload["workflow_audit_sha256"]),
            dependency_inventory_sha256=str(payload["dependency_inventory_sha256"]),
            build_manifest_evidence_sha256=str(payload["build_manifest_evidence_sha256"]),
            bom_evidence_sha256=str(payload["bom_evidence_sha256"]),
            external_attestation=AttestationState(str(payload["external_attestation"])),
            status=SupplyChainStatus(str(payload["status"])),
            blockers=tuple(str(item) for item in payload.get("blockers", [])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        manifest.validate()
        return manifest

    def assert_promotable(
        self,
        *,
        expected_source_sha: str,
        expected_evidence_sha256: str | None = None,
    ) -> None:
        self.validate()
        expected_source = _require_sha40(expected_source_sha, field="expected_source_sha")
        if self.source_sha != expected_source:
            raise ValueError("supply-chain source SHA mismatch")
        if expected_evidence_sha256 is not None:
            expected = _require_sha256(expected_evidence_sha256, field="expected_evidence_sha256")
            if self.evidence_sha256 != expected:
                raise ValueError("supply-chain evidence digest mismatch")
        if self.status is not SupplyChainStatus.PASS:
            raise ValueError("release candidate supply chain is not promotable")


def report_contains_secret_like_value(payload: Mapping[str, Any]) -> bool:
    serialized = _canonical_json(payload)
    return bool(_SECRET_RE.search(serialized))
