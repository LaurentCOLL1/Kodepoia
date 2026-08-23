from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from .client import ComfyUIClient
from .contracts import ComfyCapabilityState
from .errors import ComfyGovernanceError, ComfyProtocolError, ComfyUnavailableError
from .execution import ComfyExecutionService, ComfyRunManifest, ComfyRunStore
from .inventory import CapabilitySnapshotStore, ComfyCapabilityInventory, ComfyCapabilitySnapshot
from .lifecycle import ComfyLifecycleAuditStore, ComfyLifecycleService
from .packs import (
    ProductionWorkflowFamily,
    ProductionWorkflowPack,
    ProductionWorkflowPackCatalog,
    WorkflowPackCompatibilityState,
)
from .resources import (
    ComfyVramTelemetryAdapter,
    GpuAdmissionDecision,
    GpuAdmissionPolicy,
    GpuResourceProfile,
)
from .workflow import GovernedModelResolver, WorkflowInstance, WorkflowValidator

_MIB = 1024 * 1024
_DEFAULT_ENDPOINT = "http://127.0.0.1:8188"
_MAX_RUNS_IN_EVIDENCE = 10_000


def jsonable(value: Any) -> Any:
    """Convert accepted typed ComfyUI evidence to bounded JSON-compatible values."""
    if isinstance(value, StrEnum):
        return value.value
    canonical = getattr(value, "canonical", None)
    if callable(canonical):
        return jsonable(canonical())
    payload = getattr(value, "payload", None)
    if callable(payload):
        return jsonable(payload())
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [jsonable(item) for item in value]
    return value


class ComfyService:
    """Single governed R9 façade shared by the CLI and KodeStudio.

    The façade intentionally exposes only the fixed loopback client, the four
    accepted R9.9 workflow packs, bounded scalar parameters/model selection,
    persisted run evidence, targeted lifecycle operations and typed VRAM
    telemetry. It does not expose arbitrary ComfyUI routes, workflow graphs,
    process execution, model installation/download, or arbitrary URLs.
    """

    def __init__(
        self,
        project_root: Path,
        *,
        client: ComfyUIClient | None = None,
        catalog: ProductionWorkflowPackCatalog | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.client = client or ComfyUIClient(_DEFAULT_ENDPOINT)
        self.catalog = catalog or ProductionWorkflowPackCatalog()
        metadata = (self.project_root / ".kodepoia" / "comfyui").resolve(strict=False)
        if not metadata.is_relative_to(self.project_root):
            raise ComfyGovernanceError("ComfyUI metadata root escapes the project workspace")
        metadata.mkdir(parents=True, exist_ok=True)
        self.metadata_root = metadata
        self.snapshot_store = CapabilitySnapshotStore(metadata / "capabilities")
        self.run_store = ComfyRunStore(metadata / "runs")
        self.lifecycle_audit = ComfyLifecycleAuditStore(metadata / "lifecycle")
        self.inventory_adapter = ComfyCapabilityInventory(self.client)
        self.execution = ComfyExecutionService(self.client, self.run_store)
        self.lifecycle = ComfyLifecycleService(self.client, self.run_store, self.lifecycle_audit)
        self.telemetry = ComfyVramTelemetryAdapter(self.client)
        self.validator = WorkflowValidator()
        self.resolver = GovernedModelResolver()
        self.admission = GpuAdmissionPolicy()

    def fork(self) -> "ComfyService":
        """Create a worker-safe façade without sharing transport objects."""
        return ComfyService(
            self.project_root,
            client=ComfyUIClient(self.client.endpoint),
            catalog=self.catalog,
        )

    def status(self) -> dict[str, Any]:
        try:
            probe = self.client.probe()
        except (ComfyUnavailableError, ComfyProtocolError, OSError) as exc:
            return {
                "state": "unavailable",
                "endpoint": self.client.endpoint.origin,
                "protocol_ready": False,
                "capability_state": ComfyCapabilityState.UNAVAILABLE.value,
                "reason": f"{type(exc).__name__}: {exc}",
            }
        snapshot: ComfyCapabilitySnapshot | None = None
        try:
            snapshot = self.snapshot_store.load("current")
        except (ComfyProtocolError, OSError):
            pass
        return {
            "state": "ready" if probe.ready else "unavailable",
            "endpoint": self.client.endpoint.origin,
            "protocol_ready": probe.ready,
            "probe": probe.canonical(),
            "capability_state": (
                snapshot.state.value if snapshot is not None else "missing"
            ),
            "capability_identity_sha256": (
                snapshot.identity_sha256 if snapshot is not None else None
            ),
            "manual_intervention": "NONE",
        }

    def inventory(self, *, refresh: bool = True) -> dict[str, Any]:
        snapshot = self._snapshot(refresh=refresh)
        return snapshot.payload()

    def workflows(
        self,
        *,
        refresh_inventory: bool = False,
        model_selection: str | None = None,
    ) -> dict[str, Any]:
        snapshot: ComfyCapabilitySnapshot | None = None
        try:
            snapshot = self._snapshot(refresh=refresh_inventory)
        except (ComfyUnavailableError, ComfyProtocolError, OSError):
            pass
        packs: list[dict[str, Any]] = []
        selections = self._selections(model_selection)
        for pack in self.catalog.packs():
            item = pack.canonical()
            if snapshot is None:
                item["compatibility"] = {
                    "state": "unknown",
                    "reasons": ["capability snapshot is unavailable"],
                }
            else:
                item["compatibility"] = self.catalog.compatibility(
                    pack.family,
                    snapshot,
                    model_selections=selections,
                ).canonical()
            packs.append(item)
        return {
            "state": "ready",
            "capability_identity_sha256": snapshot.identity_sha256 if snapshot else None,
            "packs": packs,
        }

    def validate(
        self,
        family: ProductionWorkflowFamily | str,
        *,
        model_selection: str | None = None,
        refresh_inventory: bool = True,
    ) -> dict[str, Any]:
        snapshot = self._snapshot(refresh=refresh_inventory)
        pack = self.catalog.get(family)
        report = self.catalog.compatibility(
            pack.family,
            snapshot,
            model_selections=self._selections(model_selection),
        )
        return {
            "family": pack.family.value,
            "pack": pack.canonical(),
            "compatibility": report.canonical(),
        }

    def run(
        self,
        family: ProductionWorkflowFamily | str,
        *,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        output_count: int,
        seed: int,
        steps: int,
        cfg: float,
        model_selection: str | None = None,
        reserve_mib: int = 512,
        headroom_mib: int = 512,
    ) -> dict[str, Any]:
        pack = self.catalog.get(family)
        parameters = pack.validate_request(
            {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "output_count": output_count,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
            }
        )
        snapshot = self._snapshot(refresh=True)
        selections = self._selections(model_selection)
        compatibility = self.catalog.compatibility(
            pack.family,
            snapshot,
            model_selections=selections,
        )
        if compatibility.state is not WorkflowPackCompatibilityState.COMPATIBLE:
            return {
                "state": "blocked",
                "family": pack.family.value,
                "compatibility": compatibility.canonical(),
                "run": None,
            }
        profile = self._profile(pack, reserve_mib=reserve_mib, headroom_mib=headroom_mib)
        telemetry = self.telemetry.sample()
        admission = self.admission.decide(telemetry, profile)
        if admission.decision is not GpuAdmissionDecision.ADMIT:
            return {
                "state": admission.decision.value,
                "family": pack.family.value,
                "compatibility": compatibility.canonical(),
                "telemetry": telemetry.canonical(),
                "admission": admission.canonical(),
                "run": None,
            }
        resolutions = self.resolver.resolve(
            pack.definition,
            snapshot,
            selections=selections,
        )
        instance = self.validator.instantiate(
            pack.definition,
            snapshot,
            resolutions,
            parameters=parameters,
        )
        manifest = self.execution.prepare(
            pack.definition,
            snapshot,
            resolutions,
            instance,
            required_output_node_ids=pack.required_output_node_ids,
        )
        self.snapshot_store.save(manifest.run_id, snapshot)
        submitted = self.execution.submit(
            manifest.run_id,
            pack.definition,
            snapshot,
            resolutions,
            instance,
        )
        return {
            "state": submitted.state.value,
            "family": pack.family.value,
            "compatibility": compatibility.canonical(),
            "telemetry": telemetry.canonical(),
            "admission": admission.canonical(),
            "run": submitted.payload(),
        }

    def run_status(self, run_id: str, *, reconcile: bool = True) -> dict[str, Any]:
        manifest = self.run_store.load(run_id)
        if reconcile and not manifest.terminal:
            instance = self._instance_for(manifest)
            manifest = self.execution.reconcile_once(run_id, instance)
        return manifest.payload()

    def cancel(self, run_id: str) -> dict[str, Any]:
        manifest = self.run_store.load(run_id)
        instance = self._instance_for(manifest)
        result = self.lifecycle.cancel(run_id, instance)
        return result.payload()

    def vram(
        self,
        *,
        family: ProductionWorkflowFamily | str | None = None,
        reserve_mib: int = 512,
        headroom_mib: int = 512,
    ) -> dict[str, Any]:
        snapshot = self.telemetry.sample()
        result: dict[str, Any] = {
            "state": "ready",
            "telemetry": snapshot.canonical(),
            "ollama_coexistence": {"state": "n/a", "models": []},
        }
        if family is not None:
            pack = self.catalog.get(family)
            profile = self._profile(pack, reserve_mib=reserve_mib, headroom_mib=headroom_mib)
            result["admission"] = self.admission.decide(snapshot, profile).canonical()
        return result

    def free_memory(self) -> dict[str, Any]:
        evidence = self.lifecycle.request_free_memory(
            known_run_ids=self._known_run_ids(),
            unload_models=True,
            free_memory=True,
        )
        return {"state": "requested", "evidence": evidence.canonical()}

    def evidence(self, run_id: str) -> dict[str, Any]:
        manifest = self.run_store.load(run_id)
        revisions = self.run_store.revisions(run_id)
        try:
            lifecycle = self.lifecycle_audit.load(run_id).payload()
        except KeyError:
            lifecycle = None
        return {
            "state": "ready",
            "run": manifest.payload(),
            "revisions": [item.payload() for item in revisions],
            "lifecycle": lifecycle,
            "outputs": [item.canonical() for item in manifest.output_references],
            "capability_snapshot": self.snapshot_store.load(run_id).payload(),
        }

    def _snapshot(self, *, refresh: bool) -> ComfyCapabilitySnapshot:
        if refresh:
            snapshot = self.inventory_adapter.capture()
            self.snapshot_store.save("current", snapshot)
            return snapshot
        return self.snapshot_store.load("current")

    @staticmethod
    def _selections(model_selection: str | None) -> dict[str, str]:
        return {} if model_selection is None else {"checkpoint": model_selection}

    @staticmethod
    def _bounded_mib(value: int, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 65_536:
            raise ValueError(f"{field} must be an integer between 0 and 65536 MiB")
        return value

    def _profile(
        self,
        pack: ProductionWorkflowPack,
        *,
        reserve_mib: int,
        headroom_mib: int,
    ) -> GpuResourceProfile:
        reserve = self._bounded_mib(reserve_mib, "reserve_mib")
        headroom = self._bounded_mib(headroom_mib, "headroom_mib")
        return GpuResourceProfile(
            estimate_bytes=pack.estimated_vram_mib * _MIB,
            reserve_bytes=reserve * _MIB,
            headroom_bytes=headroom * _MIB,
        )

    def _pack_for_definition(self, definition_id: str) -> ProductionWorkflowPack:
        for pack in self.catalog.packs():
            if pack.definition.definition_id == definition_id:
                return pack
        raise ComfyGovernanceError("Run manifest references a workflow outside the accepted R9.9 catalog")

    def _instance_for(self, manifest: ComfyRunManifest) -> WorkflowInstance:
        pack = self._pack_for_definition(manifest.definition_id)
        snapshot = self.snapshot_store.load(manifest.run_id)
        if snapshot.identity_sha256 != manifest.capability_identity_sha256:
            raise ComfyGovernanceError("Persisted run capability evidence is stale or mismatched")
        evidence = manifest.model_resolution_evidence()
        raw = evidence.get("resolutions", [])
        if not isinstance(raw, list):
            raise ComfyProtocolError("Persisted model resolution evidence is invalid")
        selections: dict[str, str] = {}
        for item in raw:
            if not isinstance(item, dict):
                raise ComfyProtocolError("Persisted model resolution entry is invalid")
            requirement = item.get("requirement_id")
            selected = item.get("selected_token")
            if isinstance(requirement, str) and isinstance(selected, str):
                selections[requirement] = selected
        resolutions = self.resolver.resolve(pack.definition, snapshot, selections=selections)
        instance = self.validator.instantiate(
            pack.definition,
            snapshot,
            resolutions,
            parameters=dict(manifest.parameter_values),
            input_bindings=dict(manifest.input_bindings),
        )
        if instance.instance_digest_sha256 != manifest.instance_digest_sha256:
            raise ComfyGovernanceError("Reconstructed workflow instance does not match persisted run evidence")
        return instance

    def _known_run_ids(self) -> tuple[str, ...]:
        ids: list[str] = []
        for entry in sorted(self.run_store.root.glob("run_*.json")):
            if entry.is_symlink() or not entry.is_file():
                continue
            run_id = entry.stem
            try:
                self.run_store.load(run_id)
            except (KeyError, ValueError, ComfyProtocolError):
                continue
            ids.append(run_id)
            if len(ids) > _MAX_RUNS_IN_EVIDENCE:
                raise ComfyProtocolError("Known ComfyUI run count exceeds the accepted bound")
        return tuple(ids)
