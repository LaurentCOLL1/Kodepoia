from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\D.*)?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PARAMETER_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_FORBIDDEN_PARAMETER_KEYS = frozenset(
    {
        "addon",
        "argv",
        "code",
        "command",
        "cwd",
        "env",
        "environment",
        "executable",
        "operator",
        "path",
        "python",
        "script",
        "url",
    }
)


def _bounded_text(value: str, *, field_name: str, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if (not allow_empty and not value) or len(value) > maximum:
        qualifier = "at most" if allow_empty else "between 1 and"
        raise ValueError(f"{field_name} must be {qualifier} {maximum} characters")
    if _CONTROL_RE.search(value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


class BlenderCapabilityState(StrEnum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    STALE = "stale"
    CORRUPT = "corrupt"
    UNSUPPORTED = "unsupported"


class BlenderJobState(StrEnum):
    PLANNED = "planned"
    STAGED = "staged"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    TIMED_OUT = "timed_out"


class BlenderOperation(StrEnum):
    INSPECT_ASSET = "inspect_asset"
    BUILD_GEOMETRY = "build_geometry"
    APPLY_MATERIAL = "apply_material"
    VALIDATE_MESH = "validate_mesh"
    RIG_ASSET = "rig_asset"
    RETARGET_ANIMATION = "retarget_animation"
    BUILD_LOD = "build_lod"
    EXPORT_GLTF = "export_gltf"


_TERMINAL_JOB_STATES = frozenset(
    {
        BlenderJobState.SUCCEEDED,
        BlenderJobState.FAILED,
        BlenderJobState.CANCELLED,
        BlenderJobState.BLOCKED,
        BlenderJobState.UNSUPPORTED,
        BlenderJobState.TIMED_OUT,
    }
)
_JOB_TRANSITIONS: dict[BlenderJobState, frozenset[BlenderJobState]] = {
    BlenderJobState.PLANNED: frozenset(
        {
            BlenderJobState.STAGED,
            BlenderJobState.BLOCKED,
            BlenderJobState.UNSUPPORTED,
            BlenderJobState.CANCELLED,
        }
    ),
    BlenderJobState.STAGED: frozenset(
        {
            BlenderJobState.RUNNING,
            BlenderJobState.FAILED,
            BlenderJobState.BLOCKED,
            BlenderJobState.CANCELLED,
        }
    ),
    BlenderJobState.RUNNING: frozenset(_TERMINAL_JOB_STATES),
    BlenderJobState.SUCCEEDED: frozenset(),
    BlenderJobState.FAILED: frozenset(),
    BlenderJobState.CANCELLED: frozenset(),
    BlenderJobState.BLOCKED: frozenset(),
    BlenderJobState.UNSUPPORTED: frozenset(),
    BlenderJobState.TIMED_OUT: frozenset(),
}


def is_terminal_job_state(state: BlenderJobState) -> bool:
    return state in _TERMINAL_JOB_STATES


def can_transition_job_state(previous: BlenderJobState, current: BlenderJobState) -> bool:
    return previous == current or current in _JOB_TRANSITIONS[previous]


@dataclass(frozen=True, slots=True, order=True)
class BlenderVersion:
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for name in ("major", "minor", "patch"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @classmethod
    def parse(cls, text: str) -> "BlenderVersion":
        match = _VERSION_RE.match(text.strip())
        if match is None:
            raise ValueError(f"Invalid Blender version: {text!r}")
        return cls(*(int(value) for value in match.groups()))

    def canonical(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True, slots=True)
class BlenderRuntimePolicy:
    required_major: int = 5
    required_minor: int = 2

    def supports(self, version: BlenderVersion) -> bool:
        return (version.major, version.minor) == (self.required_major, self.required_minor)

    def canonical(self) -> dict[str, int]:
        return {"required_major": self.required_major, "required_minor": self.required_minor}


@dataclass(frozen=True, slots=True)
class BlenderRuntimeIdentity:
    executable: str
    version: BlenderVersion
    platform: str
    python_abi: str | None = None
    executable_sha256: str | None = None
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "executable", _bounded_text(self.executable, field_name="executable", maximum=2048))
        object.__setattr__(self, "platform", _bounded_text(self.platform, field_name="platform", maximum=128))
        if self.python_abi is not None:
            object.__setattr__(
                self,
                "python_abi",
                _bounded_text(self.python_abi, field_name="python_abi", maximum=128),
            )
        if self.executable_sha256 is not None and not _SHA256_RE.fullmatch(self.executable_sha256):
            raise ValueError("executable_sha256 must be lowercase SHA-256 hex")
        for capability in self.capabilities:
            _bounded_text(capability, field_name="capability", maximum=128)
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))

    def canonical(self) -> dict[str, Any]:
        return {
            "executable": self.executable,
            "version": self.version.canonical(),
            "platform": self.platform,
            "python_abi": self.python_abi,
            "executable_sha256": self.executable_sha256,
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True, slots=True)
class BlenderProcessLimits:
    wall_time_seconds: float = 300.0
    max_stdout_bytes: int = 4 * 1024 * 1024
    max_stderr_bytes: int = 4 * 1024 * 1024
    max_result_bytes: int = 16 * 1024 * 1024

    def __post_init__(self) -> None:
        if not math.isfinite(self.wall_time_seconds) or self.wall_time_seconds <= 0:
            raise ValueError("wall_time_seconds must be finite and > 0")
        for name in ("max_stdout_bytes", "max_stderr_bytes", "max_result_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def canonical(self) -> dict[str, Any]:
        return {
            "wall_time_seconds": self.wall_time_seconds,
            "max_stdout_bytes": self.max_stdout_bytes,
            "max_stderr_bytes": self.max_stderr_bytes,
            "max_result_bytes": self.max_result_bytes,
        }


RecipeScalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class BlenderJobRecipe:
    operation: BlenderOperation
    parameters: tuple[tuple[str, RecipeScalar], ...] = ()
    input_revision_ids: tuple[str, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("R10.1 supports Blender job recipe schema_version=1 only")
        normalized: list[tuple[str, RecipeScalar]] = []
        seen: set[str] = set()
        for key, value in self.parameters:
            if not _PARAMETER_KEY_RE.fullmatch(key):
                raise ValueError(f"Invalid recipe parameter key: {key!r}")
            if key in _FORBIDDEN_PARAMETER_KEYS:
                raise ValueError(f"Forbidden recipe parameter key: {key}")
            if key in seen:
                raise ValueError(f"Duplicate recipe parameter key: {key}")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"Recipe parameter {key} must be finite")
            if isinstance(value, str):
                _bounded_text(value, field_name=f"parameter:{key}", maximum=4096, allow_empty=True)
            elif value is not None and not isinstance(value, (bool, int, float)):
                raise TypeError(f"Recipe parameter {key} must be a JSON scalar")
            seen.add(key)
            normalized.append((key, value))
        object.__setattr__(self, "parameters", tuple(sorted(normalized)))
        revisions: list[str] = []
        for revision_id in self.input_revision_ids:
            revisions.append(_bounded_text(revision_id, field_name="input_revision_id", maximum=256))
        object.__setattr__(self, "input_revision_ids", tuple(sorted(set(revisions))))

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation.value,
            "parameters": {key: value for key, value in self.parameters},
            "input_revision_ids": list(self.input_revision_ids),
        }


@dataclass(frozen=True, slots=True)
class BlenderRunManifest:
    run_id: str
    recipe_sha256: str
    state: BlenderJobState
    runtime_sha256: str | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _bounded_text(self.run_id, field_name="run_id", maximum=128))
        if not _SHA256_RE.fullmatch(self.recipe_sha256):
            raise ValueError("recipe_sha256 must be lowercase SHA-256 hex")
        if self.runtime_sha256 is not None and not _SHA256_RE.fullmatch(self.runtime_sha256):
            raise ValueError("runtime_sha256 must be lowercase SHA-256 hex")
        object.__setattr__(
            self,
            "detail",
            _bounded_text(self.detail, field_name="detail", maximum=4096, allow_empty=True),
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "recipe_sha256": self.recipe_sha256,
            "runtime_sha256": self.runtime_sha256,
            "state": self.state.value,
            "detail": self.detail,
        }
