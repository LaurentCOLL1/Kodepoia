from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "password",
    "private_key",
    "secret",
    "token",
}
_PATH_KEYS = {"path", "file", "output", "registry_path", "evidence_path"}


class R15UXPolicyError(RuntimeError):
    """Raised when an R15 UX request violates the frozen safety contract."""


class R15WorkflowMode(StrEnum):
    INSPECT = "inspect"
    DRY_RUN = "dry_run"
    APPLY = "apply"
    CANCEL = "cancel"
    ROLLBACK = "rollback"


@dataclass(frozen=True, slots=True)
class R15ActionSpec:
    domain: str
    action: str
    mutation: bool = False
    terminal_mode: R15WorkflowMode = R15WorkflowMode.INSPECT
    identifier_required: bool = False
    description: str = ""

    @property
    def key(self) -> str:
        return f"{self.domain}.{self.action}"

    def canonical(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "action": self.action,
            "mutation": self.mutation,
            "terminal_mode": self.terminal_mode.value,
            "identifier_required": self.identifier_required,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class R15WorkflowRequest:
    domain: str
    action: str
    mode: R15WorkflowMode = R15WorkflowMode.INSPECT
    identifier: str | None = None
    confirmed: bool = False

    @property
    def key(self) -> str:
        return f"{self.domain}.{self.action}"


R15ActionHandler = Callable[[R15WorkflowRequest], Mapping[str, object]]


_ACTIONS: tuple[R15ActionSpec, ...] = (
    R15ActionSpec(
        "experience",
        "status",
        description="Inspect governed experience eligibility and capture state.",
    ),
    R15ActionSpec(
        "experience",
        "curate",
        mutation=True,
        terminal_mode=R15WorkflowMode.APPLY,
        identifier_required=True,
        description="Apply an explicitly authorized curation transition to a stable experience identifier.",
    ),
    R15ActionSpec(
        "dataset",
        "inspect",
        identifier_required=True,
        description="Inspect an immutable dataset identity.",
    ),
    R15ActionSpec(
        "dataset",
        "build",
        mutation=True,
        terminal_mode=R15WorkflowMode.APPLY,
        description="Build a governed immutable dataset from already eligible records.",
    ),
    R15ActionSpec("bench", "status", description="Inspect KodeBench evidence availability."),
    R15ActionSpec(
        "bench",
        "run",
        mutation=True,
        terminal_mode=R15WorkflowMode.APPLY,
        description="Run a governed KodeBench plan through a configured backend handler.",
    ),
    R15ActionSpec(
        "bench",
        "compare",
        identifier_required=True,
        description="Inspect a saved base/candidate benchmark comparison identity.",
    ),
    R15ActionSpec(
        "gap",
        "diagnose",
        identifier_required=True,
        description="Inspect a governed TRAIN/NO_TRAIN gap decision.",
    ),
    R15ActionSpec(
        "training",
        "doctor",
        description="Inspect optional training backend capability without installing it.",
    ),
    R15ActionSpec(
        "training",
        "plan",
        identifier_required=True,
        description="Inspect an immutable training plan.",
    ),
    R15ActionSpec(
        "training",
        "run",
        mutation=True,
        terminal_mode=R15WorkflowMode.APPLY,
        identifier_required=True,
        description=(
            "Start an explicitly confirmed bounded training plan through a configured backend handler."
        ),
    ),
    R15ActionSpec(
        "training",
        "status",
        identifier_required=True,
        description="Inspect one training run identity.",
    ),
    R15ActionSpec(
        "training",
        "cancel",
        mutation=True,
        terminal_mode=R15WorkflowMode.CANCEL,
        identifier_required=True,
        description="Cancel one exact training run identity.",
    ),
    R15ActionSpec(
        "conversion",
        "doctor",
        description="Inspect GGUF/quantization capability without installing tools.",
    ),
    R15ActionSpec(
        "conversion",
        "status",
        identifier_required=True,
        description="Inspect conversion evidence for one candidate.",
    ),
    R15ActionSpec("ollama", "status", description="Inspect persisted Ollama packaging/runtime evidence."),
    R15ActionSpec(
        "registry",
        "candidates",
        description="Inspect immutable specialized-model registry candidates.",
    ),
    R15ActionSpec(
        "registry",
        "promote",
        mutation=True,
        terminal_mode=R15WorkflowMode.APPLY,
        identifier_required=True,
        description="Promote an eligible immutable candidate through the configured registry handler.",
    ),
    R15ActionSpec(
        "registry",
        "rollback",
        mutation=True,
        terminal_mode=R15WorkflowMode.ROLLBACK,
        identifier_required=True,
        description="Restore the prior immutable role mapping through the configured registry handler.",
    ),
)
_ACTION_BY_KEY = {spec.key: spec for spec in _ACTIONS}
if len(_ACTION_BY_KEY) != len(_ACTIONS):
    raise RuntimeError("duplicate R15 UX action key")


def stable_r15_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_path(root: Path, value: Path) -> str:
    candidate = value if value.is_absolute() else root / value
    resolved = candidate.resolve(strict=False)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return "<external-path>"


def _redact(root: Path, value: object, *, key: str | None = None) -> object:
    key_l = (key or "").lower()
    if any(token in key_l for token in _SENSITIVE_KEYS):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(k): _redact(root, v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(root, item) for item in value]
    if isinstance(value, Path):
        return _safe_path(root, value)
    if isinstance(value, str) and key_l in _PATH_KEYS:
        return _safe_path(root, Path(value))
    return value


class R15UXService:
    """Safe structured UX facade over R15 services and persisted evidence."""

    schema = "kodepoia.r15.ux.v1"

    def __init__(
        self,
        project_root: Path,
        *,
        handlers: Mapping[str, R15ActionHandler] | None = None,
    ) -> None:
        self.root = Path(project_root).resolve(strict=False)
        self.handlers = dict(handlers or {})

    @classmethod
    def for_project(cls, project_root: Path) -> R15UXService:
        return cls(project_root)

    @staticmethod
    def actions() -> tuple[R15ActionSpec, ...]:
        return _ACTIONS

    @staticmethod
    def action(domain: str, action: str) -> R15ActionSpec:
        try:
            return _ACTION_BY_KEY[f"{domain}.{action}"]
        except KeyError as exc:
            raise R15UXPolicyError("unknown R15 workflow action") from exc

    def catalog(self) -> dict[str, object]:
        domains: dict[str, list[dict[str, object]]] = {}
        for spec in _ACTIONS:
            domains.setdefault(spec.domain, []).append(spec.canonical())
        return {
            "schema": self.schema,
            "status": "ok",
            "domains": domains,
            "raw_shell_exposed": False,
            "raw_secret_editor_exposed": False,
            "public_model_upload_exposed": False,
            "default_mutation_mode": R15WorkflowMode.DRY_RUN.value,
        }

    def _candidate_evidence_paths(self) -> tuple[Path, ...]:
        return (
            self.root / ".kodepoia" / "experience",
            self.root / ".kodepoia" / "datasets",
            self.root / ".kodepoia" / "benchmarks",
            self.root / ".kodepoia" / "tuning",
            self.root / ".kodepoia" / "model-registry.json",
        )

    def status(self) -> dict[str, object]:
        evidence: list[dict[str, object]] = []
        for path in self._candidate_evidence_paths():
            if path.is_file():
                evidence.append(
                    {
                        "path": _safe_path(self.root, path),
                        "kind": "file",
                        "bytes": path.stat().st_size,
                        "sha256": _sha256_file(path),
                    }
                )
            elif path.is_dir():
                files = sorted(item for item in path.rglob("*") if item.is_file())
                evidence.append(
                    {
                        "path": _safe_path(self.root, path),
                        "kind": "directory",
                        "file_count": len(files),
                    }
                )
        return {
            "schema": self.schema,
            "status": "ok",
            "project_root": ".",
            "action_count": len(_ACTIONS),
            "evidence": evidence,
            "handlers": sorted(self.handlers),
            "redacted": True,
        }

    def _validate(self, request: R15WorkflowRequest) -> R15ActionSpec:
        spec = self.action(request.domain, request.action)
        identifier = request.identifier.strip() if request.identifier else None
        if spec.identifier_required and not identifier:
            raise R15UXPolicyError("stable identifier is required for this action")
        if identifier and any(char in identifier for char in ("\n", "\r", "\x00")):
            raise R15UXPolicyError("identifier contains forbidden control characters")
        if spec.mutation:
            if request.mode is R15WorkflowMode.DRY_RUN:
                return spec
            if request.mode is not spec.terminal_mode:
                raise R15UXPolicyError(
                    f"{spec.key} requires dry_run or {spec.terminal_mode.value}"
                )
            if not request.confirmed:
                raise R15UXPolicyError("explicit confirmation is required for mutation")
        elif request.mode not in {R15WorkflowMode.INSPECT, R15WorkflowMode.DRY_RUN}:
            raise R15UXPolicyError("read-only action accepts inspect or dry_run only")
        return spec

    def execute(self, request: R15WorkflowRequest) -> dict[str, object]:
        spec = self._validate(request)
        base: dict[str, object] = {
            "schema": self.schema,
            "workflow": spec.key,
            "mode": request.mode.value,
            "identifier": request.identifier,
            "mutation": spec.mutation,
            "redacted": True,
        }
        if request.mode is R15WorkflowMode.DRY_RUN:
            return {
                **base,
                "status": "dry_run",
                "would_mutate": spec.mutation,
                "required_mode": spec.terminal_mode.value if spec.mutation else "inspect",
                "confirmed": False,
            }

        handler = self.handlers.get(spec.key)
        if handler is None:
            if spec.mutation:
                raise R15UXPolicyError(
                    "mutation backend is not configured; no state was changed"
                )
            return {
                **base,
                "status": "ok",
                "available": False,
                "reason": "backend_not_configured",
            }

        payload = dict(handler(request))
        return {
            **base,
            **_redact(self.root, payload),
            "schema": self.schema,
            "workflow": spec.key,
            "mode": request.mode.value,
            "redacted": True,
        }

    def export_evidence(self, output: Path) -> dict[str, object]:
        destination = (self.root / output).resolve(strict=False)
        if destination != self.root and self.root not in destination.parents:
            raise R15UXPolicyError("evidence output must remain inside the project root")
        payload = {
            "catalog": self.catalog(),
            "status": self.status(),
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = stable_r15_json(payload) + "\n"
        destination.write_text(text, encoding="utf-8")
        return {
            "schema": self.schema,
            "status": "ok",
            "output": _safe_path(self.root, destination),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "redacted": True,
        }
