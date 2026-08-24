from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRevision,
    AssetRevisionId,
    AssetRole,
    AssetStatus,
    LineageRef,
    PreservationPolicy,
    ProvenanceRef,
    ReuseScope,
)

from .errors import BlenderBoundaryError
from .serialization import canonical_sha256

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_EXTENSIONS = frozenset(
    {
        "KHR_materials_clearcoat",
        "KHR_materials_emissive_strength",
        "KHR_materials_ior",
        "KHR_materials_sheen",
        "KHR_materials_specular",
        "KHR_materials_transmission",
        "KHR_materials_unlit",
        "KHR_materials_volume",
        "KHR_texture_transform",
        "KHR_lights_punctual",
    }
)


class GltfContainer(StrEnum):
    GLB = "GLB"
    GLTF_SEPARATE = "GLTF_SEPARATE"


class GltfAssetMode(StrEnum):
    STATIC = "static"
    SKINNED = "skinned"


class GltfExportScope(StrEnum):
    SCENE = "scene"
    SELECTED = "selected"


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must be a lowercase SHA-256")
    return value


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise BlenderBoundaryError(f"{field} must be boolean")
    return value


def _int(value: Any, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise BlenderBoundaryError(f"{field} must be an integer between {minimum} and {maximum}")
    return value


def _number(value: Any, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderBoundaryError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise BlenderBoundaryError(f"{field} must be finite and between {minimum} and {maximum}")
    return result


def _names(value: Any, field: str, maximum: int = 512) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > maximum or not all(isinstance(item, str) for item in value):
        raise BlenderBoundaryError(f"{field} must contain at most {maximum} strings")
    result = tuple(value)
    if len(set(result)) != len(result):
        raise BlenderBoundaryError(f"{field} must contain unique strings")
    if any(not item or len(item) > 128 or any(ord(ch) < 32 for ch in item) for item in result):
        raise BlenderBoundaryError(f"{field} contains an invalid name")
    return result


@dataclass(frozen=True, slots=True)
class GltfExportProfile:
    version: int
    profile_id: str
    input_blend_sha256: str
    source_asset_id: str
    source_revision_id: str
    source_content_sha256: str
    output_asset_id: str
    asset_mode: GltfAssetMode
    container: GltfContainer
    scope: GltfExportScope
    source_object_ids: tuple[str, ...]
    mesh_qa_digest: str
    pbr_profile_digest: str
    rig_profile_digest: str | None
    animation_report_digest: str | None
    lod_manifest_digest: str | None
    export_normals: bool
    export_tangents: bool
    export_uvs: bool
    export_materials: bool
    export_skins: bool
    export_morphs: bool
    export_animations: bool
    deform_bones_only: bool
    max_influences: int
    required_uv_sets: tuple[str, ...]
    required_materials: tuple[str, ...]
    required_bones: tuple[str, ...]
    required_shape_keys: tuple[str, ...]
    required_animations: tuple[str, ...]
    allowed_extensions: tuple[str, ...]
    max_output_bytes: int
    unit_scale_meters: float = 1.0
    export_y_up: bool = True

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GltfExportProfile":
        required = {
            "version", "profile_id", "input_blend_sha256", "source_asset_id", "source_revision_id",
            "source_content_sha256", "output_asset_id", "asset_mode", "container", "scope",
            "source_object_ids", "mesh_qa_digest", "pbr_profile_digest", "rig_profile_digest",
            "animation_report_digest", "lod_manifest_digest", "export_normals", "export_tangents",
            "export_uvs", "export_materials", "export_skins", "export_morphs", "export_animations",
            "deform_bones_only", "max_influences", "required_uv_sets", "required_materials",
            "required_bones", "required_shape_keys", "required_animations", "allowed_extensions",
            "max_output_bytes", "unit_scale_meters", "export_y_up",
        }
        if set(payload) != required:
            raise BlenderBoundaryError("GltfExportProfile has missing or unknown fields")
        if payload["version"] != 1:
            raise BlenderBoundaryError("only GltfExportProfile version 1 is supported")
        try:
            source_asset = AssetId(str(payload["source_asset_id"]))
            source_revision = AssetRevisionId(str(payload["source_revision_id"]))
            output_asset = AssetId(str(payload["output_asset_id"]))
            asset_mode = GltfAssetMode(payload["asset_mode"])
            container = GltfContainer(payload["container"])
            scope = GltfExportScope(payload["scope"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("invalid R8 identity or glTF profile enum") from exc
        if source_asset == output_asset:
            raise BlenderBoundaryError("glTF export may not overwrite the source asset identity")
        input_sha = _sha(payload["input_blend_sha256"], "input_blend_sha256")
        source_sha = _sha(payload["source_content_sha256"], "source_content_sha256")
        if input_sha != source_sha:
            raise BlenderBoundaryError("input_blend_sha256 must equal source_content_sha256")
        rig_digest = payload["rig_profile_digest"]
        if rig_digest is not None:
            rig_digest = _sha(rig_digest, "rig_profile_digest")
        animation_digest = payload["animation_report_digest"]
        if animation_digest is not None:
            animation_digest = _sha(animation_digest, "animation_report_digest")
        lod_digest = payload["lod_manifest_digest"]
        if lod_digest is not None:
            lod_digest = _sha(lod_digest, "lod_manifest_digest")
        flags = {}
        for field in (
            "export_normals", "export_tangents", "export_uvs", "export_materials", "export_skins",
            "export_morphs", "export_animations", "deform_bones_only", "export_y_up",
        ):
            flags[field] = _bool(payload[field], field)
        if abs(_number(payload["unit_scale_meters"], "unit_scale_meters", 1e-9, 1_000_000.0) - 1.0) > 1e-9:
            raise BlenderBoundaryError("R10.10 requires normalized metre units")
        if flags["export_y_up"] is not True:
            raise BlenderBoundaryError("R10.10 glTF export requires Y-up")
        source_object_ids = _names(payload["source_object_ids"], "source_object_ids", 256)
        if scope is GltfExportScope.SELECTED and not source_object_ids:
            raise BlenderBoundaryError("selected export scope requires governed source_object_ids")
        if scope is GltfExportScope.SCENE and source_object_ids:
            raise BlenderBoundaryError("scene export scope requires source_object_ids=[]")
        required_bones = _names(payload["required_bones"], "required_bones")
        required_animations = _names(payload["required_animations"], "required_animations")
        required_shapes = _names(payload["required_shape_keys"], "required_shape_keys")
        if asset_mode is GltfAssetMode.SKINNED:
            if rig_digest is None or not flags["export_skins"] or not required_bones:
                raise BlenderBoundaryError("skinned exports require rig binding, skins and required bones")
        else:
            if rig_digest is not None or required_bones or flags["export_skins"]:
                raise BlenderBoundaryError("static exports may not claim rig/skin semantics")
        if required_animations and (animation_digest is None or not flags["export_animations"]):
            raise BlenderBoundaryError("required animations need animation evidence and export_animations=true")
        if required_shapes and not flags["export_morphs"]:
            raise BlenderBoundaryError("required shape keys need export_morphs=true")
        extensions = _names(payload["allowed_extensions"], "allowed_extensions", 32)
        unsupported = sorted(set(extensions) - _ALLOWED_EXTENSIONS)
        if unsupported:
            raise BlenderBoundaryError("unsupported glTF extension policy: " + ", ".join(unsupported))
        return cls(
            1,
            _id(payload["profile_id"], "profile_id"),
            input_sha,
            str(source_asset),
            str(source_revision),
            source_sha,
            str(output_asset),
            asset_mode,
            container,
            scope,
            source_object_ids,
            _sha(payload["mesh_qa_digest"], "mesh_qa_digest"),
            _sha(payload["pbr_profile_digest"], "pbr_profile_digest"),
            rig_digest,
            animation_digest,
            lod_digest,
            flags["export_normals"],
            flags["export_tangents"],
            flags["export_uvs"],
            flags["export_materials"],
            flags["export_skins"],
            flags["export_morphs"],
            flags["export_animations"],
            flags["deform_bones_only"],
            _int(payload["max_influences"], "max_influences", 1, 8),
            _names(payload["required_uv_sets"], "required_uv_sets", 16),
            _names(payload["required_materials"], "required_materials", 256),
            required_bones,
            required_shapes,
            required_animations,
            extensions,
            _int(payload["max_output_bytes"], "max_output_bytes", 1, 2_147_483_647),
            1.0,
            True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "profile_id": self.profile_id,
            "input_blend_sha256": self.input_blend_sha256,
            "source_asset_id": self.source_asset_id,
            "source_revision_id": self.source_revision_id,
            "source_content_sha256": self.source_content_sha256,
            "output_asset_id": self.output_asset_id,
            "asset_mode": self.asset_mode.value,
            "container": self.container.value,
            "scope": self.scope.value,
            "source_object_ids": list(self.source_object_ids),
            "mesh_qa_digest": self.mesh_qa_digest,
            "pbr_profile_digest": self.pbr_profile_digest,
            "rig_profile_digest": self.rig_profile_digest,
            "animation_report_digest": self.animation_report_digest,
            "lod_manifest_digest": self.lod_manifest_digest,
            "export_normals": self.export_normals,
            "export_tangents": self.export_tangents,
            "export_uvs": self.export_uvs,
            "export_materials": self.export_materials,
            "export_skins": self.export_skins,
            "export_morphs": self.export_morphs,
            "export_animations": self.export_animations,
            "deform_bones_only": self.deform_bones_only,
            "max_influences": self.max_influences,
            "required_uv_sets": list(self.required_uv_sets),
            "required_materials": list(self.required_materials),
            "required_bones": list(self.required_bones),
            "required_shape_keys": list(self.required_shape_keys),
            "required_animations": list(self.required_animations),
            "allowed_extensions": list(self.allowed_extensions),
            "max_output_bytes": self.max_output_bytes,
            "unit_scale_meters": 1.0,
            "export_y_up": True,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


def validate_gltf_source_revision(profile: GltfExportProfile, revision: AssetRevision) -> None:
    if str(revision.asset_id) != profile.source_asset_id or str(revision.revision_id) != profile.source_revision_id:
        raise BlenderBoundaryError("R8 source asset/revision identity mismatch")
    if revision.kind is not AssetKind.MODEL_3D or revision.status is not AssetStatus.READY:
        raise BlenderBoundaryError("R10.10 requires a READY R8 model_3d source revision")
    if revision.content_sha256 != profile.source_content_sha256:
        raise BlenderBoundaryError("R8 source content digest mismatch")
    if not revision.provenance:
        raise BlenderBoundaryError("R10.10 source revision requires retained R8 provenance")


def make_gltf_export_revision(
    profile: GltfExportProfile,
    *,
    output_sha256: str,
    output_length: int,
    source_revision: AssetRevision,
    manifest_digest: str,
) -> AssetRevision:
    validate_gltf_source_revision(profile, source_revision)
    if profile.container is not GltfContainer.GLB:
        raise BlenderBoundaryError("only canonical GLB output is directly promotable as one R8 model revision")
    digest = _sha(output_sha256, "output_sha256")
    evidence = _sha(manifest_digest, "manifest_digest")
    if isinstance(output_length, bool) or not isinstance(output_length, int) or output_length < 1:
        raise BlenderBoundaryError("output_length must be a positive integer")
    transform_id = f"blender.gltf.v1.{profile.profile_id}"
    return AssetRevision.create(
        asset_id=AssetId(profile.output_asset_id),
        role=AssetRole.DERIVED,
        kind=AssetKind.MODEL_3D,
        content_sha256=digest,
        content_length=output_length,
        reuse_scope=ReuseScope.EXPORTABLE,
        preservation=PreservationPolicy.REFERENCED,
        provenance=(ProvenanceRef("transform", transform_id, evidence_sha256=evidence),),
        lineage=(LineageRef(AssetRevisionId(profile.source_revision_id), relation="gltf_export", transform_id=transform_id),),
        status=AssetStatus.READY,
    )
