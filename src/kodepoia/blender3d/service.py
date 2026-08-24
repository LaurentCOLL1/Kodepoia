from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from .errors import BlenderBoundaryError
from .geometry_contracts import GeometryRecipe

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_MAX_JSON_BYTES = 2 * 1024 * 1024
_REPORT_KINDS = ("inspect", "qa", "rig", "animation", "lod", "export")
_EVIDENCE_FILES = {
    "r10.2": "docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json",
    "r10.6": "docs/roadmap/R10_6_LOCAL_ACCEPTANCE.json",
    "r10.7": "docs/roadmap/R10_7_LOCAL_ACCEPTANCE.json",
    "r10.10": "docs/roadmap/R10_10_LOCAL_ACCEPTANCE.json",
}


class BlenderUXState(StrEnum):
    READY = "ready"
    MISSING = "missing"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class BlenderUXResult:
    operation: str
    state: BlenderUXState
    payload: Mapping[str, Any]
    reason: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "state": self.state.value,
            "reason": self.reason,
            "payload": dict(self.payload),
        }


class BlenderCancellation:
    """Thread-safe cooperative cancellation token for R10.11 UX workers."""

    def __init__(self) -> None:
        self._event = threading.Event()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()


def _safe_id(value: str, *, field: str = "id") -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


class BlenderService:
    """Single governed R10.11 façade shared by CLI and KodeStudio.

    The service exposes only accepted R10 capability/evidence views, service-managed
    recipe/report IDs and cooperative UX cancellation. It deliberately does not
    expose Blender executables, arbitrary filesystem paths, Python source,
    operators, argv, environment variables, URLs, process handles or shell access.
    """

    def __init__(self, project_root: Path) -> None:
        root = Path(project_root).resolve(strict=False)
        self.project_root = root
        self.metadata_root = (root / ".kodepoia" / "blender" / "r10_11").resolve(strict=False)
        if self.metadata_root != root and root not in self.metadata_root.parents:
            raise BlenderBoundaryError("R10.11 metadata root escapes the project workspace")
        self.recipe_root = self.metadata_root / "recipes"
        self.report_root = self.metadata_root / "reports"

    def fork(self) -> "BlenderService":
        return BlenderService(self.project_root)

    def status(self, *, cancellation: BlenderCancellation | None = None) -> BlenderUXResult:
        if self._cancelled(cancellation):
            return self._cancelled_result("status")
        accepted = self._accepted_evidence_summary()
        runtime = accepted.get("r10.10") or accepted.get("r10.2")
        state = BlenderUXState.READY if runtime else BlenderUXState.MISSING
        return BlenderUXResult(
            "status",
            state,
            {
                "manual_intervention": "NONE",
                "service_version": 1,
                "runtime_evidence": runtime,
                "accepted_evidence_ids": sorted(accepted),
                "report_kinds": list(_REPORT_KINDS),
            },
            None if runtime else "accepted_runtime_evidence_missing",
        )

    def capabilities(self, *, cancellation: BlenderCancellation | None = None) -> BlenderUXResult:
        if self._cancelled(cancellation):
            return self._cancelled_result("capabilities")
        evidence = self._accepted_evidence_summary()
        runtime = evidence.get("r10.10") or evidence.get("r10.2")
        capabilities = {
            "runtime_boundary": "accepted",
            "geometry": "accepted",
            "uv_pbr": "accepted",
            "mesh_qa": "accepted",
            "rig_skin": "accepted",
            "animation_retarget": "accepted",
            "organic_profiles": "accepted",
            "lod": "accepted",
            "gltf_glb": "accepted",
            "godot_47_interop": "accepted" if "r10.10" in evidence else "evidence_missing",
        }
        return BlenderUXResult(
            "capabilities",
            BlenderUXState.READY,
            {
                "capabilities": capabilities,
                "runtime_evidence": runtime,
                "api_inventory": self.api_inventory(),
            },
        )

    def api_inventory(self) -> dict[str, Any]:
        return {
            "version": 1,
            "operations": [
                "status",
                "capabilities",
                "inspect",
                "validate_geometry",
                "qa",
                "rig",
                "animation",
                "lod",
                "export",
                "evidence",
            ],
            "identifiers_only": True,
            "raw_python_surface": False,
            "raw_process_surface": False,
            "raw_path_surface": False,
        }

    def inspect(
        self,
        kind: str,
        record_id: str,
        *,
        cancellation: BlenderCancellation | None = None,
    ) -> BlenderUXResult:
        if self._cancelled(cancellation):
            return self._cancelled_result("inspect")
        if kind not in _REPORT_KINDS:
            raise BlenderBoundaryError("Unsupported R10.11 inspect kind")
        return self._report(kind, record_id, operation="inspect", cancellation=cancellation)

    def validate_geometry(
        self,
        recipe_id: str,
        *,
        cancellation: BlenderCancellation | None = None,
    ) -> BlenderUXResult:
        if self._cancelled(cancellation):
            return self._cancelled_result("geometry")
        recipe_id = _safe_id(recipe_id, field="recipe_id")
        path = self.recipe_root / f"{recipe_id}.json"
        payload = self._load_managed_json(path, root=self.recipe_root)
        if payload is None:
            return BlenderUXResult(
                "geometry",
                BlenderUXState.MISSING,
                {"recipe_id": recipe_id},
                "managed_recipe_missing",
            )
        try:
            recipe = GeometryRecipe.from_dict(payload)
        except (BlenderBoundaryError, TypeError, ValueError) as exc:
            return BlenderUXResult(
                "geometry",
                BlenderUXState.INVALID,
                {"recipe_id": recipe_id},
                f"{type(exc).__name__}: {exc}",
            )
        if self._cancelled(cancellation):
            return self._cancelled_result("geometry")
        return BlenderUXResult(
            "geometry",
            BlenderUXState.READY,
            {
                "recipe_id": recipe.recipe_id,
                "digest": recipe.digest,
                "steps": len(recipe.steps),
                "units": recipe.units,
                "forward_axis": recipe.forward_axis,
                "up_axis": recipe.up_axis,
            },
        )

    def qa(self, record_id: str, *, cancellation: BlenderCancellation | None = None) -> BlenderUXResult:
        return self._report("qa", record_id, operation="qa", cancellation=cancellation)

    def rig(self, record_id: str, *, cancellation: BlenderCancellation | None = None) -> BlenderUXResult:
        return self._report("rig", record_id, operation="rig", cancellation=cancellation)

    def animation(
        self,
        record_id: str,
        *,
        cancellation: BlenderCancellation | None = None,
    ) -> BlenderUXResult:
        return self._report("animation", record_id, operation="animation", cancellation=cancellation)

    def lod(self, record_id: str, *, cancellation: BlenderCancellation | None = None) -> BlenderUXResult:
        return self._report("lod", record_id, operation="lod", cancellation=cancellation)

    def export(self, record_id: str, *, cancellation: BlenderCancellation | None = None) -> BlenderUXResult:
        return self._report("export", record_id, operation="export", cancellation=cancellation)

    def evidence(
        self,
        evidence_id: str,
        *,
        cancellation: BlenderCancellation | None = None,
    ) -> BlenderUXResult:
        if self._cancelled(cancellation):
            return self._cancelled_result("evidence")
        if evidence_id not in _EVIDENCE_FILES:
            raise BlenderBoundaryError("Unsupported R10 evidence ID")
        path = (self.project_root / _EVIDENCE_FILES[evidence_id]).resolve(strict=False)
        payload = self._load_managed_json(path, root=self.project_root)
        if payload is None:
            return BlenderUXResult(
                "evidence",
                BlenderUXState.MISSING,
                {"evidence_id": evidence_id},
                "accepted_evidence_missing",
            )
        if self._cancelled(cancellation):
            return self._cancelled_result("evidence")
        return BlenderUXResult(
            "evidence",
            BlenderUXState.READY,
            {
                "evidence_id": evidence_id,
                "status": payload.get("status"),
                "blockers": payload.get("blockers"),
                "source_sha": payload.get("source_sha"),
                "evidence": payload,
            },
        )

    def serialized(self, result: BlenderUXResult) -> str:
        return json.dumps(result.canonical(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _report(
        self,
        kind: str,
        record_id: str,
        *,
        operation: str,
        cancellation: BlenderCancellation | None,
    ) -> BlenderUXResult:
        if self._cancelled(cancellation):
            return self._cancelled_result(operation)
        if kind not in _REPORT_KINDS:
            raise BlenderBoundaryError("Unsupported R10.11 report kind")
        record_id = _safe_id(record_id, field="record_id")
        root = self.report_root / kind
        payload = self._load_managed_json(root / f"{record_id}.json", root=root)
        if payload is None:
            return BlenderUXResult(
                operation,
                BlenderUXState.MISSING,
                {"kind": kind, "record_id": record_id},
                "managed_report_missing",
            )
        if self._cancelled(cancellation):
            return self._cancelled_result(operation)
        return BlenderUXResult(
            operation,
            BlenderUXState.READY,
            {"kind": kind, "record_id": record_id, "report": payload},
        )

    def _accepted_evidence_summary(self) -> dict[str, dict[str, Any]]:
        accepted: dict[str, dict[str, Any]] = {}
        for evidence_id, relative in _EVIDENCE_FILES.items():
            payload = self._load_managed_json(
                (self.project_root / relative).resolve(strict=False),
                root=self.project_root,
            )
            if not payload or payload.get("status") != "pass":
                continue
            summary: dict[str, Any] = {
                "status": payload.get("status"),
                "source_sha": payload.get("source_sha"),
            }
            runtime = payload.get("runtime")
            if isinstance(runtime, dict):
                summary["blender_version"] = runtime.get("version") or runtime.get("blender_version")
                summary["background"] = runtime.get("background")
                summary["online_access"] = runtime.get("online_access")
            blender = payload.get("blender")
            if isinstance(blender, dict):
                summary["blender_version"] = blender.get("version")
                summary["background"] = blender.get("background")
                summary["online_access"] = blender.get("online_access")
            godot = payload.get("godot")
            if isinstance(godot, dict):
                version = godot.get("version")
                if isinstance(version, dict):
                    summary["godot_version"] = version.get("raw")
            accepted[evidence_id] = summary
        return accepted

    @staticmethod
    def _cancelled(cancellation: BlenderCancellation | None) -> bool:
        return cancellation is not None and cancellation.cancelled

    @staticmethod
    def _cancelled_result(operation: str) -> BlenderUXResult:
        return BlenderUXResult(
            operation,
            BlenderUXState.CANCELLED,
            {},
            "cancelled",
        )

    @staticmethod
    def _load_managed_json(path: Path, *, root: Path) -> dict[str, Any] | None:
        resolved_root = root.resolve(strict=False)
        resolved = path.resolve(strict=False)
        if resolved != resolved_root and resolved_root not in resolved.parents:
            raise BlenderBoundaryError("Managed R10.11 path escapes its fixed root")
        if not resolved.is_file():
            return None
        size = resolved.stat().st_size
        if size <= 0 or size > _MAX_JSON_BYTES:
            raise BlenderBoundaryError("Managed R10.11 JSON exceeds the bounded size")
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise BlenderBoundaryError("Managed R10.11 JSON is malformed") from exc
        if not isinstance(payload, dict):
            raise BlenderBoundaryError("Managed R10.11 JSON root must be an object")
        return payload


__all__ = [
    "BlenderCancellation",
    "BlenderService",
    "BlenderUXResult",
    "BlenderUXState",
]
