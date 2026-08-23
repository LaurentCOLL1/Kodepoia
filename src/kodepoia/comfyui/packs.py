from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from .contracts import ComfyCapabilityState
from .errors import ComfyGovernanceError, ComfyProtocolError
from .inventory import ComfyCapabilitySnapshot
from .serialization import canonical_sha256
from .workflow import (
    GovernedModelResolver,
    ModelRequirement,
    ModelResolutionState,
    WorkflowDefinition,
    WorkflowParameterKind,
    WorkflowParameterSpec,
    WorkflowValidator,
)

_MAX_PROMPT_CHARS = 8_192
_MAX_NEGATIVE_PROMPT_CHARS = 8_192
_MAX_TOTAL_PIXELS = 16_777_216


class ProductionWorkflowFamily(StrEnum):
    CONCEPT = "concept"
    UI_ILLUSTRATION = "ui_illustration"
    MATERIAL_SOURCE = "material_source"
    SPRITE_2D = "sprite_2d"


class WorkflowPackCompatibilityState(StrEnum):
    COMPATIBLE = "compatible"
    BLOCKED = "blocked"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ProductionWorkflowPack:
    family: ProductionWorkflowFamily
    variant_id: str
    definition: WorkflowDefinition
    required_output_node_ids: tuple[str, ...]
    min_width: int
    max_width: int
    min_height: int
    max_height: int
    max_outputs: int
    max_total_pixels: int
    estimated_vram_mib: int
    material_source_only: bool

    def __post_init__(self) -> None:
        if not self.variant_id or len(self.variant_id) > 128:
            raise ValueError("workflow pack variant_id must contain 1-128 characters")
        if not self.required_output_node_ids:
            raise ValueError("workflow pack requires at least one explicit output node")
        if len(set(self.required_output_node_ids)) != len(self.required_output_node_ids):
            raise ValueError("workflow pack output node IDs must be unique")
        if self.min_width < 1 or self.min_height < 1:
            raise ValueError("workflow pack minimum dimensions must be positive")
        if self.max_width < self.min_width or self.max_height < self.min_height:
            raise ValueError("workflow pack dimension bounds are invalid")
        if not 1 <= self.max_outputs <= 8:
            raise ValueError("workflow pack max_outputs must be between 1 and 8")
        if self.max_total_pixels < self.min_width * self.min_height:
            raise ValueError("workflow pack pixel budget is smaller than its minimum frame")
        if not 256 <= self.estimated_vram_mib <= 65_536:
            raise ValueError("workflow pack VRAM estimate is outside the accepted bound")

    @property
    def identity_sha256(self) -> str:
        return canonical_sha256(self.canonical())

    def canonical(self) -> dict[str, Any]:
        return {
            "family": self.family.value,
            "variant_id": self.variant_id,
            "definition_id": self.definition.definition_id,
            "definition_digest_sha256": self.definition.definition_digest_sha256,
            "required_output_node_ids": list(self.required_output_node_ids),
            "dimension_bounds": {
                "min_width": self.min_width,
                "max_width": self.max_width,
                "min_height": self.min_height,
                "max_height": self.max_height,
            },
            "max_outputs": self.max_outputs,
            "max_total_pixels": self.max_total_pixels,
            "estimated_vram_mib": self.estimated_vram_mib,
            "material_source_only": self.material_source_only,
        }

    def validate_request(self, parameters: Mapping[str, Any]) -> dict[str, Any]:
        required = {"prompt", "negative_prompt", "width", "height", "output_count", "seed", "steps", "cfg"}
        if set(parameters) != required:
            missing = sorted(required - set(parameters))
            extra = sorted(set(parameters) - required)
            raise ComfyGovernanceError(
                f"R9.9 workflow request fields are invalid: missing={missing}, extra={extra}"
            )
        prompt = parameters["prompt"]
        negative = parameters["negative_prompt"]
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > _MAX_PROMPT_CHARS:
            raise ComfyGovernanceError("R9.9 prompt must be a bounded non-empty string")
        if not isinstance(negative, str) or len(negative) > _MAX_NEGATIVE_PROMPT_CHARS:
            raise ComfyGovernanceError("R9.9 negative prompt must be a bounded string")
        width = _strict_int(parameters["width"], "width")
        height = _strict_int(parameters["height"], "height")
        outputs = _strict_int(parameters["output_count"], "output_count")
        if not self.min_width <= width <= self.max_width:
            raise ComfyGovernanceError("R9.9 width is outside the pack bounds")
        if not self.min_height <= height <= self.max_height:
            raise ComfyGovernanceError("R9.9 height is outside the pack bounds")
        if not 1 <= outputs <= self.max_outputs:
            raise ComfyGovernanceError("R9.9 output count is outside the pack bounds")
        if width * height * outputs > self.max_total_pixels:
            raise ComfyGovernanceError("R9.9 request exceeds the pack total-pixel budget")
        normalized = dict(parameters)
        normalized["width"] = width
        normalized["height"] = height
        normalized["output_count"] = outputs
        return normalized


@dataclass(frozen=True, slots=True)
class WorkflowPackCompatibilityReport:
    family: ProductionWorkflowFamily
    variant_id: str
    pack_identity_sha256: str
    definition_id: str
    capability_identity_sha256: str
    state: WorkflowPackCompatibilityState
    reasons: tuple[str, ...]
    validation_digest_sha256: str | None
    model_resolution_digest_sha256: str | None
    selected_models: tuple[tuple[str, str], ...]
    report_digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "family": self.family.value,
            "variant_id": self.variant_id,
            "pack_identity_sha256": self.pack_identity_sha256,
            "definition_id": self.definition_id,
            "capability_identity_sha256": self.capability_identity_sha256,
            "state": self.state.value,
            "reasons": list(self.reasons),
            "validation_digest_sha256": self.validation_digest_sha256,
            "model_resolution_digest_sha256": self.model_resolution_digest_sha256,
            "selected_models": [list(item) for item in self.selected_models],
        }

    def canonical(self) -> dict[str, Any]:
        payload = self.canonical_without_digest()
        payload["report_digest_sha256"] = self.report_digest_sha256
        return payload


class ProductionWorkflowPackCatalog:
    def __init__(self, packs: tuple[ProductionWorkflowPack, ...] | None = None) -> None:
        values = default_production_workflow_packs() if packs is None else tuple(packs)
        by_family: dict[ProductionWorkflowFamily, ProductionWorkflowPack] = {}
        by_variant: dict[str, ProductionWorkflowPack] = {}
        for pack in values:
            if pack.family in by_family:
                raise ValueError(f"duplicate mandatory R9.9 workflow family: {pack.family.value}")
            if pack.variant_id in by_variant:
                raise ValueError(f"duplicate R9.9 workflow variant: {pack.variant_id}")
            by_family[pack.family] = pack
            by_variant[pack.variant_id] = pack
        expected = set(ProductionWorkflowFamily)
        if set(by_family) != expected:
            missing = sorted(item.value for item in expected - set(by_family))
            raise ValueError(f"R9.9 catalog is missing mandatory workflow families: {missing}")
        self._by_family = by_family
        self._by_variant = by_variant

    def packs(self) -> tuple[ProductionWorkflowPack, ...]:
        return tuple(self._by_family[item] for item in ProductionWorkflowFamily)

    def get(self, family: ProductionWorkflowFamily | str) -> ProductionWorkflowPack:
        key = ProductionWorkflowFamily(family)
        return self._by_family[key]

    def compatibility(
        self,
        family: ProductionWorkflowFamily | str,
        snapshot: ComfyCapabilitySnapshot,
        *,
        model_selections: Mapping[str, str] | None = None,
    ) -> WorkflowPackCompatibilityReport:
        pack = self.get(family)
        capability_id = snapshot.identity_sha256
        if snapshot.state is ComfyCapabilityState.STALE:
            return _compatibility_report(
                pack,
                capability_id,
                WorkflowPackCompatibilityState.STALE,
                ("capability snapshot is STALE",),
                None,
                None,
                (),
            )
        if snapshot.state is not ComfyCapabilityState.CURRENT:
            return _compatibility_report(
                pack,
                capability_id,
                WorkflowPackCompatibilityState.UNAVAILABLE,
                (f"capability snapshot state is {snapshot.state.value}",),
                None,
                None,
                (),
            )
        try:
            validation = WorkflowValidator().validate(pack.definition, snapshot)
            resolutions = GovernedModelResolver().resolve(
                pack.definition,
                snapshot,
                selections=dict(model_selections or {}),
            )
        except (ComfyGovernanceError, ComfyProtocolError) as exc:
            return _compatibility_report(
                pack,
                capability_id,
                WorkflowPackCompatibilityState.BLOCKED,
                (str(exc),),
                None,
                None,
                (),
            )
        selected = tuple(
            sorted(
                (item.requirement_id, item.selected_token)
                for item in resolutions.resolutions
                if item.state is ModelResolutionState.RESOLVED and item.selected_token is not None
            )
        )
        if not resolutions.ready:
            reasons = tuple(
                f"model requirement {item.requirement_id}: {item.state.value}"
                for item in resolutions.resolutions
                if item.state is not ModelResolutionState.RESOLVED
            )
            return _compatibility_report(
                pack,
                capability_id,
                WorkflowPackCompatibilityState.BLOCKED,
                reasons or ("model requirements are not resolved",),
                validation.digest_sha256,
                resolutions.digest_sha256,
                selected,
            )
        return _compatibility_report(
            pack,
            capability_id,
            WorkflowPackCompatibilityState.COMPATIBLE,
            (),
            validation.digest_sha256,
            resolutions.digest_sha256,
            selected,
        )


def default_production_workflow_packs() -> tuple[ProductionWorkflowPack, ...]:
    return (
        _make_pack(
            ProductionWorkflowFamily.CONCEPT,
            "core-checkpoint-concept-v1",
            min_size=256,
            max_size=1536,
            max_outputs=4,
            max_total_pixels=9_437_184,
            estimate_mib=8192,
            material_source_only=False,
        ),
        _make_pack(
            ProductionWorkflowFamily.UI_ILLUSTRATION,
            "core-checkpoint-ui-v1",
            min_size=64,
            max_size=1024,
            max_outputs=4,
            max_total_pixels=4_194_304,
            estimate_mib=6144,
            material_source_only=False,
        ),
        _make_pack(
            ProductionWorkflowFamily.MATERIAL_SOURCE,
            "core-checkpoint-material-source-v1",
            min_size=256,
            max_size=1536,
            max_outputs=4,
            max_total_pixels=9_437_184,
            estimate_mib=8192,
            material_source_only=True,
        ),
        _make_pack(
            ProductionWorkflowFamily.SPRITE_2D,
            "core-checkpoint-sprite-v1",
            min_size=64,
            max_size=1024,
            max_outputs=4,
            max_total_pixels=4_194_304,
            estimate_mib=6144,
            material_source_only=False,
        ),
    )


def _make_pack(
    family: ProductionWorkflowFamily,
    variant_id: str,
    *,
    min_size: int,
    max_size: int,
    max_outputs: int,
    max_total_pixels: int,
    estimate_mib: int,
    material_source_only: bool,
) -> ProductionWorkflowPack:
    graph = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": {"$model": "checkpoint"}}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": {"$param": "prompt"}, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": {"$param": "negative_prompt"}, "clip": ["1", 1]}},
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": {"$param": "width"},
                "height": {"$param": "height"},
                "batch_size": {"$param": "output_count"},
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": {"$param": "seed"},
                "steps": {"$param": "steps"},
                "cfg": {"$param": "cfg"},
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {
            "class_type": "SaveImage",
            "inputs": {"images": ["6", 0], "filename_prefix": f"kodepoia_r9_9_{family.value}"},
        },
    }
    parameters = (
        WorkflowParameterSpec("prompt", "2", "text", WorkflowParameterKind.STRING),
        WorkflowParameterSpec("negative_prompt", "3", "text", WorkflowParameterKind.STRING),
        WorkflowParameterSpec("width", "4", "width", WorkflowParameterKind.INTEGER, min_size, max_size),
        WorkflowParameterSpec("height", "4", "height", WorkflowParameterKind.INTEGER, min_size, max_size),
        WorkflowParameterSpec("output_count", "4", "batch_size", WorkflowParameterKind.INTEGER, 1, max_outputs),
        WorkflowParameterSpec("seed", "5", "seed", WorkflowParameterKind.SEED, 0, 18_446_744_073_709_551_615),
        WorkflowParameterSpec("steps", "5", "steps", WorkflowParameterKind.INTEGER, 1, 80),
        WorkflowParameterSpec("cfg", "5", "cfg", WorkflowParameterKind.NUMBER, 1.0, 20.0),
    )
    definition = WorkflowDefinition.create(
        name=f"r9.9-{family.value}-core-checkpoint",
        revision=1,
        graph=graph,
        parameters=parameters,
        input_slots=(),
        output_slots=(),
        model_requirements=(
            ModelRequirement(
                requirement_id="checkpoint",
                model_type="checkpoints",
                node_id="1",
                input_name="ckpt_name",
                accepted_tokens=(),
            ),
        ),
        allowed_node_classes=(
            "CheckpointLoaderSimple",
            "CLIPTextEncode",
            "EmptyLatentImage",
            "KSampler",
            "VAEDecode",
            "SaveImage",
        ),
    )
    return ProductionWorkflowPack(
        family=family,
        variant_id=variant_id,
        definition=definition,
        required_output_node_ids=("7",),
        min_width=min_size,
        max_width=max_size,
        min_height=min_size,
        max_height=max_size,
        max_outputs=max_outputs,
        max_total_pixels=min(max_total_pixels, _MAX_TOTAL_PIXELS),
        estimated_vram_mib=estimate_mib,
        material_source_only=material_source_only,
    )


def _compatibility_report(
    pack: ProductionWorkflowPack,
    capability_identity_sha256: str,
    state: WorkflowPackCompatibilityState,
    reasons: tuple[str, ...],
    validation_digest_sha256: str | None,
    model_resolution_digest_sha256: str | None,
    selected_models: tuple[tuple[str, str], ...],
) -> WorkflowPackCompatibilityReport:
    draft = {
        "family": pack.family.value,
        "variant_id": pack.variant_id,
        "pack_identity_sha256": pack.identity_sha256,
        "definition_id": pack.definition.definition_id,
        "capability_identity_sha256": capability_identity_sha256,
        "state": state.value,
        "reasons": list(reasons),
        "validation_digest_sha256": validation_digest_sha256,
        "model_resolution_digest_sha256": model_resolution_digest_sha256,
        "selected_models": [list(item) for item in selected_models],
    }
    return WorkflowPackCompatibilityReport(
        family=pack.family,
        variant_id=pack.variant_id,
        pack_identity_sha256=pack.identity_sha256,
        definition_id=pack.definition.definition_id,
        capability_identity_sha256=capability_identity_sha256,
        state=state,
        reasons=reasons,
        validation_digest_sha256=validation_digest_sha256,
        model_resolution_digest_sha256=model_resolution_digest_sha256,
        selected_models=selected_models,
        report_digest_sha256=canonical_sha256(draft),
    )


def _strict_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ComfyGovernanceError(f"R9.9 {field} must be an integer")
    return value
