from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from kodepoia.assets.contracts import AssetKind, AssetRevisionId
from kodepoia.assets.service import AssetService

from .client import ComfyUIClient
from .contracts import ComfyCapabilityState, ComfyRunState
from .errors import ComfyGovernanceError, ComfyProtocolError, ComfyUnavailableError
from .execution import ComfyExecutionBudget, ComfyExecutionService, ComfyRunManifest, ComfyRunStore
from .inventory import ComfyCapabilityInventory, ComfyCapabilitySnapshot
from .lifecycle import ComfyFreeMemoryEvidence, ComfyLifecycleService
from .outputs import ComfyOutputCaptureManifest, ComfyOutputCaptureService, ComfyOutputSpec
from .packs import (
    ProductionWorkflowFamily,
    ProductionWorkflowPack,
    ProductionWorkflowPackCatalog,
    WorkflowPackCompatibilityReport,
)
from .resources import (
    ComfyVramTelemetryAdapter,
    GpuAdmissionDecision,
    GpuAdmissionResult,
    GpuCleanupTrace,
    GpuResourceCoordinator,
    GpuResourceProfile,
)
from .serialization import canonical_sha256
from .workflow import GovernedModelResolver, ModelResolutionState, WorkflowInstance, WorkflowValidator


@dataclass(frozen=True, slots=True)
class ComfyServiceStatus:
    endpoint: str
    ready: bool
    capability_state: str
    capability_identity_sha256: str | None
    comfyui_version: str | None
    queue_running: int | None
    queue_pending: int | None
    vram_total_bytes: int | None
    vram_free_bytes: int | None
    run_id: str | None
    run_state: str | None
    progress_fraction: float | None
    reason: str
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "ready": self.ready,
            "capability_state": self.capability_state,
            "capability_identity_sha256": self.capability_identity_sha256,
            "comfyui_version": self.comfyui_version,
            "queue_running": self.queue_running,
            "queue_pending": self.queue_pending,
            "vram_total_bytes": self.vram_total_bytes,
            "vram_free_bytes": self.vram_free_bytes,
            "run_id": self.run_id,
            "run_state": self.run_state,
            "progress_fraction": self.progress_fraction,
            "reason": self.reason,
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.canonical_without_digest(), "digest_sha256": self.digest_sha256}


@dataclass(frozen=True, slots=True)
class ComfyWorkflowRunResult:
    manifest: ComfyRunManifest
    admission: GpuAdmissionResult
    cleanup_trace: GpuCleanupTrace | None

    def canonical(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.payload(),
            "admission": self.admission.canonical(),
            "cleanup_trace": self.cleanup_trace.canonical() if self.cleanup_trace is not None else None,
        }


class ComfyService:
    """Single governed R9 facade used by CLI and KodeStudio.

    The facade owns the only UI-facing path to ComfyUI networking, workflow
    validation/resolution/execution, lifecycle operations, output capture and
    VRAM admission. It deliberately exposes production workflow families rather
    than accepting raw prompt/workflow JSON.
    """

    def __init__(
        self,
        project_root: Path,
        *,
        endpoint: str = "http://127.0.0.1:8188",
        client: ComfyUIClient | None = None,
        asset_service: AssetService | None = None,
        packs: ProductionWorkflowPackCatalog | None = None,
    ) -> None:
        raw_root = Path(project_root)
        if raw_root.exists() and raw_root.is_symlink():
            raise ComfyProtocolError("ComfyService project root must not be a symlink")
        self.project_root = raw_root.resolve(strict=False)
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.state_root = (self.project_root / ".kodepoia" / "comfyui").resolve(strict=False)
        if not self.state_root.is_relative_to(self.project_root):
            raise ComfyProtocolError("ComfyService state root escapes project root")
        if self.state_root.exists() and self.state_root.is_symlink():
            raise ComfyProtocolError("ComfyService state root must not be a symlink")
        self.state_root.mkdir(parents=True, exist_ok=True)

        self.client = client or ComfyUIClient(endpoint)
        self.endpoint = self.client.endpoint.origin
        self.packs = packs or ProductionWorkflowPackCatalog()
        self.run_store = ComfyRunStore(self.state_root / "runs")
        self.inventory = ComfyCapabilityInventory(self.client)
        self.lifecycle = ComfyLifecycleService(self.client, self.run_store)
        self.execution = ComfyExecutionService(self.client, self.run_store)
        self.telemetry = ComfyVramTelemetryAdapter(self.client)
        self.resources = GpuResourceCoordinator(self.telemetry, self.lifecycle)
        self._owns_assets = asset_service is None
        self.assets = asset_service or AssetService(self.project_root)
        self.outputs = ComfyOutputCaptureService(self.client, self.run_store, self.assets)
        self._closed = False

    def fork(self) -> "ComfyService":
        """Create independent client/SQLite state for a KodeStudio worker."""
        return ComfyService(
            self.project_root,
            endpoint=self.endpoint,
            asset_service=self.assets.fork(),
            packs=self.packs,
        )

    def close(self) -> None:
        if self._closed:
            return
        if self._owns_assets:
            self.assets.close()
        self._closed = True

    def workflow_families(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "family": pack.family.value,
                "variant_id": pack.variant_id,
                "definition_id": pack.definition.definition_id,
                "definition_digest_sha256": pack.definition.definition_digest_sha256,
                "estimated_vram_mib": pack.estimated_vram_mib,
                "max_outputs": pack.max_outputs,
                "max_total_pixels": pack.max_total_pixels,
                "material_source_only": pack.material_source_only,
            }
            for pack in self.packs.packs()
        )

    def status(self, run_id: str | None = None) -> ComfyServiceStatus:
        ready = False
        capability_state = ComfyCapabilityState.UNAVAILABLE.value
        capability_identity: str | None = None
        comfyui_version: str | None = None
        running: int | None = None
        pending: int | None = None
        total: int | None = None
        free: int | None = None
        reason = "local ComfyUI unavailable"
        run: ComfyRunManifest | None = None
        if run_id is not None:
            run = self.run_store.load(run_id)
        try:
            snapshot = self.inventory.capture()
            capability_state = snapshot.state.value
            capability_identity = snapshot.identity_sha256
            comfyui_version = snapshot.comfyui_version
            ready = snapshot.state is ComfyCapabilityState.CURRENT
            reason = "capability snapshot current" if ready else "; ".join(snapshot.unavailable) or snapshot.state.value
            queue = self.client.queue()
            running = len(queue.running_prompt_ids)
            pending = len(queue.pending_prompt_ids)
            vram = self.telemetry.sample()
            primary = vram.primary
            if primary is not None:
                total = primary.vram_total_bytes
                free = primary.vram_free_bytes
        except (ComfyUnavailableError, ComfyProtocolError, OSError) as exc:
            reason = str(exc)
        draft = ComfyServiceStatus(
            endpoint=self.endpoint,
            ready=ready,
            capability_state=capability_state,
            capability_identity_sha256=capability_identity,
            comfyui_version=comfyui_version,
            queue_running=running,
            queue_pending=pending,
            vram_total_bytes=total,
            vram_free_bytes=free,
            run_id=run.run_id if run is not None else None,
            run_state=run.state.value if run is not None else None,
            progress_fraction=run.progress_fraction if run is not None else None,
            reason=reason[:2048],
            digest_sha256="",
        )
        return ComfyServiceStatus(
            **draft.canonical_without_digest(),
            digest_sha256=canonical_sha256(draft.canonical_without_digest()),
        )

    def inventory_snapshot(self) -> ComfyCapabilitySnapshot:
        return self.inventory.capture()

    def validate_workflow(
        self,
        family: ProductionWorkflowFamily | str,
        *,
        model_selections: Mapping[str, str] | None = None,
    ) -> WorkflowPackCompatibilityReport:
        snapshot = self.inventory.capture()
        return self.packs.compatibility(family, snapshot, model_selections=model_selections)

    def resource_status(
        self,
        family: ProductionWorkflowFamily | str,
        *,
        reserve_mib: int = 512,
        headroom_mib: int = 512,
        device_index: int = 0,
    ) -> GpuAdmissionResult:
        pack = self.packs.get(family)
        profile = _profile(pack, reserve_mib, headroom_mib, device_index)
        _snapshot, result = self.resources.evaluate(profile)
        return result

    def run_workflow(
        self,
        family: ProductionWorkflowFamily | str,
        *,
        parameters: Mapping[str, Any],
        model_selections: Mapping[str, str],
        allow_memory_cleanup: bool = False,
        reserve_mib: int = 512,
        headroom_mib: int = 512,
        device_index: int = 0,
        budget: ComfyExecutionBudget | None = None,
    ) -> ComfyWorkflowRunResult:
        pack = self.packs.get(family)
        normalized = pack.validate_request(parameters)
        snapshot = self.inventory.capture()
        if snapshot.state is not ComfyCapabilityState.CURRENT:
            raise ComfyGovernanceError("R9.10 generation requires a CURRENT capability snapshot")
        validation = WorkflowValidator().validate(pack.definition, snapshot)
        if validation.definition_digest_sha256 != pack.definition.definition_digest_sha256:
            raise ComfyProtocolError("R9.10 workflow validation digest binding changed unexpectedly")
        resolutions = GovernedModelResolver().resolve(
            pack.definition,
            snapshot,
            selections=dict(model_selections),
        )
        if not resolutions.ready:
            states = ", ".join(
                f"{item.requirement_id}={item.state.value}" for item in resolutions.resolutions
            )
            raise ComfyGovernanceError(f"R9.10 model requirements are not resolved: {states}")
        instance = WorkflowValidator().instantiate(
            pack.definition,
            snapshot,
            resolutions,
            parameters=normalized,
        )

        profile = _profile(pack, reserve_mib, headroom_mib, device_index)
        _telemetry, admission = self.resources.evaluate(profile)
        cleanup_trace: GpuCleanupTrace | None = None
        if admission.decision is GpuAdmissionDecision.DEFER and allow_memory_cleanup:
            cleanup_trace = self.resources.admit_with_cleanup(profile)
            admission = cleanup_trace.final
        if admission.decision is not GpuAdmissionDecision.ADMIT:
            suffix = "; explicit memory cleanup is available" if admission.decision is GpuAdmissionDecision.DEFER else ""
            raise ComfyGovernanceError(
                f"R9.10 GPU admission is {admission.decision.value}: {admission.reason}{suffix}"
            )

        manifest = self.execution.prepare(
            pack.definition,
            snapshot,
            resolutions,
            instance,
            required_output_node_ids=pack.required_output_node_ids,
        )
        manifest = self.execution.submit(
            manifest.run_id,
            pack.definition,
            snapshot,
            resolutions,
            instance,
            budget=budget,
        )
        manifest = self.execution.wait(manifest.run_id, instance, budget=budget)
        return ComfyWorkflowRunResult(manifest, admission, cleanup_trace)

    def run_status(self, run_id: str, *, reconcile: bool = True) -> ComfyRunManifest:
        manifest = self.run_store.load(run_id)
        if not reconcile or manifest.terminal:
            return manifest
        instance = self._reconstruct_instance(manifest)
        return self.execution.reconcile_once(run_id, instance)

    def cancel_run(self, run_id: str) -> ComfyRunManifest:
        manifest = self.run_store.load(run_id)
        if manifest.terminal:
            return manifest
        instance = self._reconstruct_instance(manifest)
        return self.lifecycle.cancel(run_id, instance)

    def free_memory(self, *, confirmed: bool = False) -> ComfyFreeMemoryEvidence:
        if not confirmed:
            raise ComfyGovernanceError("R9.10 free-memory request requires explicit confirmation")
        return self.lifecycle.request_free_memory()

    def capture_run_outputs(
        self,
        run_id: str,
        *,
        source_revision_ids: tuple[AssetRevisionId, ...] = (),
    ) -> ComfyOutputCaptureManifest:
        manifest = self.run_store.load(run_id)
        if manifest.state is not ComfyRunState.SUCCEEDED:
            raise ComfyGovernanceError("R9.10 output capture requires a reconciled SUCCEEDED run")
        pack = self._pack_for_definition(manifest.definition_id)
        kind = _asset_kind(pack.family)
        specs = tuple(
            ComfyOutputSpec(
                node_id=reference.node_id,
                output_index=reference.output_index,
                asset_kind=kind,
                display_name=f"ComfyUI {pack.family.value} {manifest.run_id[-8:]} {index + 1}",
            )
            for index, reference in enumerate(manifest.output_references)
        )
        if not specs:
            raise ComfyProtocolError("R9.10 succeeded run contains no output references to capture")
        return self.outputs.capture(
            run_id,
            specs,
            source_revision_ids=source_revision_ids,
        )

    def evidence(self, run_id: str | None = None) -> dict[str, Any]:
        document: dict[str, Any] = {
            "service": self.status(run_id).canonical(),
            "workflow_families": list(self.workflow_families()),
        }
        if run_id is None:
            return document
        manifest = self.run_store.load(run_id)
        document["run"] = manifest.payload()
        try:
            document["lifecycle_audit"] = self.lifecycle.audit.load(run_id).payload()
        except KeyError:
            document["lifecycle_audit"] = None
        try:
            document["output_capture"] = self.outputs.capture_store.load(run_id).payload()
        except KeyError:
            document["output_capture"] = None
        return document

    def _reconstruct_instance(self, manifest: ComfyRunManifest) -> WorkflowInstance:
        pack = self._pack_for_definition(manifest.definition_id)
        if pack.definition.definition_digest_sha256 != manifest.definition_digest_sha256:
            raise ComfyProtocolError("Persisted run references a different workflow definition digest")
        snapshot = self.inventory.capture()
        if snapshot.state is not ComfyCapabilityState.CURRENT:
            raise ComfyGovernanceError("Run reconciliation requires a CURRENT capability snapshot")
        if snapshot.identity_sha256 != manifest.capability_identity_sha256:
            raise ComfyGovernanceError("Run capability snapshot is STALE; reconciliation fails closed")
        evidence = manifest.model_resolution_evidence()
        raw_resolutions = evidence.get("resolutions")
        if not isinstance(raw_resolutions, list):
            raise ComfyProtocolError("Run model-resolution evidence is malformed")
        selections: dict[str, str] = {}
        for raw in raw_resolutions:
            if not isinstance(raw, dict):
                raise ComfyProtocolError("Run model-resolution entry is malformed")
            if raw.get("state") != ModelResolutionState.RESOLVED.value:
                raise ComfyGovernanceError("Persisted run model resolution is not fully RESOLVED")
            requirement = raw.get("requirement_id")
            token = raw.get("selected_token")
            if not isinstance(requirement, str) or not isinstance(token, str):
                raise ComfyProtocolError("Run model-resolution selection is malformed")
            selections[requirement] = token
        resolutions = GovernedModelResolver().resolve(pack.definition, snapshot, selections=selections)
        if resolutions.digest_sha256 != manifest.model_resolution_digest_sha256:
            raise ComfyGovernanceError("Current model resolution no longer matches persisted run evidence")
        instance = WorkflowValidator().instantiate(
            pack.definition,
            snapshot,
            resolutions,
            parameters=dict(manifest.parameter_values),
            input_bindings=dict(manifest.input_bindings),
        )
        if instance.instance_digest_sha256 != manifest.instance_digest_sha256:
            raise ComfyProtocolError("Reconstructed workflow instance does not match persisted run evidence")
        return instance

    def _pack_for_definition(self, definition_id: str) -> ProductionWorkflowPack:
        matches = tuple(pack for pack in self.packs.packs() if pack.definition.definition_id == definition_id)
        if len(matches) != 1:
            raise ComfyGovernanceError("Run workflow definition is not one governed R9.9 production pack")
        return matches[0]


def jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [jsonable(item) for item in value]
    return value


def _profile(
    pack: ProductionWorkflowPack,
    reserve_mib: int,
    headroom_mib: int,
    device_index: int,
) -> GpuResourceProfile:
    for name, value in (("reserve_mib", reserve_mib), ("headroom_mib", headroom_mib)):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1_048_576:
            raise ValueError(f"{name} must be an integer between 0 and 1048576")
    return GpuResourceProfile(
        estimate_bytes=pack.estimated_vram_mib * 1024 * 1024,
        reserve_bytes=reserve_mib * 1024 * 1024,
        headroom_bytes=headroom_mib * 1024 * 1024,
        device_index=device_index,
    )


def _asset_kind(family: ProductionWorkflowFamily) -> AssetKind:
    if family is ProductionWorkflowFamily.UI_ILLUSTRATION:
        return AssetKind.UI
    if family is ProductionWorkflowFamily.MATERIAL_SOURCE:
        return AssetKind.TEXTURE
    return AssetKind.IMAGE
