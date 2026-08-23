from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .errors import BlenderBoundaryError
from .serialization import canonical_sha256

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RootMotionPolicy(StrEnum):
    KEEP = "keep"
    ZERO = "zero"


class ChannelPath(StrEnum):
    LOCATION = "location"
    ROTATION_QUATERNION = "rotation_quaternion"
    SCALE = "scale"


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must be a lowercase SHA-256")
    return value


def _number(value: Any, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderBoundaryError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise BlenderBoundaryError(f"{field} must be finite and between {minimum} and {maximum}")
    return result


@dataclass(frozen=True, slots=True)
class SemanticBone:
    bone_id: str
    actual_name: str
    parent_id: str | None
    deform: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SemanticBone":
        if set(payload) != {"bone_id", "actual_name", "parent_id", "deform"}:
            raise BlenderBoundaryError("SemanticBone has missing or unknown fields")
        actual = payload["actual_name"]
        if not isinstance(actual, str) or not 1 <= len(actual) <= 128 or any(ord(ch) < 32 for ch in actual):
            raise BlenderBoundaryError("actual_name must be printable and 1-128 characters")
        parent = payload["parent_id"]
        if parent is not None:
            parent = _id(parent, "parent_id")
        if not isinstance(payload["deform"], bool):
            raise BlenderBoundaryError("deform must be boolean")
        return cls(_id(payload["bone_id"], "bone_id"), actual, parent, payload["deform"])

    def to_dict(self) -> dict[str, Any]:
        return {"bone_id": self.bone_id, "actual_name": self.actual_name, "parent_id": self.parent_id, "deform": self.deform}


@dataclass(frozen=True, slots=True)
class RigSemanticProfile:
    rig_id: str
    armature_id: str
    input_blend_sha256: str
    bones: tuple[SemanticBone, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RigSemanticProfile":
        if set(payload) != {"rig_id", "armature_id", "input_blend_sha256", "bones"}:
            raise BlenderBoundaryError("RigSemanticProfile has missing or unknown fields")
        raw = payload["bones"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= 256 or not all(isinstance(item, dict) for item in raw):
            raise BlenderBoundaryError("bones must contain 1-256 objects")
        bones = tuple(SemanticBone.from_dict(item) for item in raw)
        if len({item.bone_id for item in bones}) != len(bones):
            raise BlenderBoundaryError("semantic bone IDs must be unique")
        if len({item.actual_name for item in bones}) != len(bones):
            raise BlenderBoundaryError("actual bone names must be unique")
        by_id = {item.bone_id: item for item in bones}
        for index, bone in enumerate(bones):
            if bone.parent_id is not None:
                if bone.parent_id not in by_id:
                    raise BlenderBoundaryError(f"unknown semantic parent: {bone.parent_id}")
                if next(i for i, item in enumerate(bones) if item.bone_id == bone.parent_id) >= index:
                    raise BlenderBoundaryError("semantic parents must precede children")
        if not any(item.deform for item in bones):
            raise BlenderBoundaryError("semantic profile requires at least one deform bone")
        return cls(_id(payload["rig_id"], "rig_id"), _id(payload["armature_id"], "armature_id"), _sha(payload["input_blend_sha256"], "input_blend_sha256"), bones)

    def to_dict(self) -> dict[str, Any]:
        return {"rig_id": self.rig_id, "armature_id": self.armature_id, "input_blend_sha256": self.input_blend_sha256, "bones": [item.to_dict() for item in self.bones]}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())

    @property
    def deform_ids(self) -> tuple[str, ...]:
        return tuple(item.bone_id for item in self.bones if item.deform)


@dataclass(frozen=True, slots=True)
class Keyframe:
    frame: float
    value: tuple[float, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, width: int) -> "Keyframe":
        if set(payload) != {"frame", "value"}:
            raise BlenderBoundaryError("Keyframe requires exactly frame/value")
        frame = _number(payload["frame"], "frame", -1_000_000.0, 1_000_000.0)
        value = payload["value"]
        if not isinstance(value, list) or len(value) != width:
            raise BlenderBoundaryError(f"keyframe value must contain {width} numbers")
        values = tuple(_number(item, "keyframe value", -1_000_000.0, 1_000_000.0) for item in value)
        if width == 4:
            norm = math.sqrt(sum(item * item for item in values))
            if norm <= 1e-8:
                raise BlenderBoundaryError("quaternion keyframe cannot be zero length")
            values = tuple(item / norm for item in values)
        return cls(frame, values)

    def to_dict(self) -> dict[str, Any]:
        return {"frame": self.frame, "value": list(self.value)}


@dataclass(frozen=True, slots=True)
class AnimationChannel:
    bone_id: str
    path: ChannelPath
    keys: tuple[Keyframe, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnimationChannel":
        if set(payload) != {"bone_id", "path", "keys"}:
            raise BlenderBoundaryError("AnimationChannel has missing or unknown fields")
        try:
            path = ChannelPath(payload["path"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("unsupported animation channel path") from exc
        width = 4 if path is ChannelPath.ROTATION_QUATERNION else 3
        raw = payload["keys"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= 20_000 or not all(isinstance(item, dict) for item in raw):
            raise BlenderBoundaryError("keys must contain 1-20000 objects")
        keys = tuple(Keyframe.from_dict(item, width=width) for item in raw)
        frames = [item.frame for item in keys]
        if frames != sorted(frames) or len(set(frames)) != len(frames):
            raise BlenderBoundaryError("keyframes must be strictly ordered and unique by frame")
        return cls(_id(payload["bone_id"], "bone_id"), path, keys)

    def to_dict(self) -> dict[str, Any]:
        return {"bone_id": self.bone_id, "path": self.path.value, "keys": [item.to_dict() for item in self.keys]}


@dataclass(frozen=True, slots=True)
class AnimationClip:
    clip_id: str
    fps: float
    frame_start: float
    frame_end: float
    loop: bool
    root_motion: RootMotionPolicy
    channels: tuple[AnimationChannel, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnimationClip":
        required = {"clip_id", "fps", "frame_start", "frame_end", "loop", "root_motion", "channels"}
        if set(payload) != required:
            raise BlenderBoundaryError("AnimationClip has missing or unknown fields")
        fps = _number(payload["fps"], "fps", 1.0, 240.0)
        start = _number(payload["frame_start"], "frame_start", -1_000_000.0, 1_000_000.0)
        end = _number(payload["frame_end"], "frame_end", -1_000_000.0, 1_000_000.0)
        if end <= start:
            raise BlenderBoundaryError("frame_end must be greater than frame_start")
        if not isinstance(payload["loop"], bool):
            raise BlenderBoundaryError("loop must be boolean")
        try:
            root_motion = RootMotionPolicy(payload["root_motion"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("unsupported root motion policy") from exc
        raw = payload["channels"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= 4096 or not all(isinstance(item, dict) for item in raw):
            raise BlenderBoundaryError("channels must contain 1-4096 objects")
        channels = tuple(AnimationChannel.from_dict(item) for item in raw)
        if len({(item.bone_id, item.path.value) for item in channels}) != len(channels):
            raise BlenderBoundaryError("animation channels must be unique per bone/path")
        for channel in channels:
            for key in channel.keys:
                if key.frame < start - 1e-6 or key.frame > end + 1e-6:
                    raise BlenderBoundaryError("animation key falls outside clip frame range")
        return cls(_id(payload["clip_id"], "clip_id"), fps, start, end, payload["loop"], root_motion, channels)

    def to_dict(self) -> dict[str, Any]:
        return {"clip_id": self.clip_id, "fps": self.fps, "frame_start": self.frame_start, "frame_end": self.frame_end, "loop": self.loop, "root_motion": self.root_motion.value, "channels": [item.to_dict() for item in self.channels]}

    @property
    def key_count(self) -> int:
        return sum(len(item.keys) for item in self.channels)


@dataclass(frozen=True, slots=True)
class BoneMapping:
    source_bone_id: str
    target_bone_id: str
    copy_translation: bool
    copy_rotation: bool
    copy_scale: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BoneMapping":
        required = {"source_bone_id", "target_bone_id", "copy_translation", "copy_rotation", "copy_scale"}
        if set(payload) != required:
            raise BlenderBoundaryError("BoneMapping has missing or unknown fields")
        for name in ("copy_translation", "copy_rotation", "copy_scale"):
            if not isinstance(payload[name], bool):
                raise BlenderBoundaryError(f"{name} must be boolean")
        if not any(payload[name] for name in ("copy_translation", "copy_rotation", "copy_scale")):
            raise BlenderBoundaryError("BoneMapping must copy at least one transform component")
        return cls(_id(payload["source_bone_id"], "source_bone_id"), _id(payload["target_bone_id"], "target_bone_id"), payload["copy_translation"], payload["copy_rotation"], payload["copy_scale"])

    def to_dict(self) -> dict[str, Any]:
        return {"source_bone_id": self.source_bone_id, "target_bone_id": self.target_bone_id, "copy_translation": self.copy_translation, "copy_rotation": self.copy_rotation, "copy_scale": self.copy_scale}


@dataclass(frozen=True, slots=True)
class RetargetRecipe:
    version: int
    recipe_id: str
    input_blend_sha256: str
    source_rig: RigSemanticProfile
    target_rig: RigSemanticProfile
    clip: AnimationClip
    mappings: tuple[BoneMapping, ...]
    required_target_bones: tuple[str, ...]
    translation_scale: float
    max_keys: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RetargetRecipe":
        required = {"version", "recipe_id", "input_blend_sha256", "source_rig", "target_rig", "clip", "mappings", "required_target_bones", "translation_scale", "max_keys"}
        if set(payload) != required:
            raise BlenderBoundaryError("RetargetRecipe has missing or unknown fields")
        if payload["version"] != 1:
            raise BlenderBoundaryError("only RetargetRecipe version 1 is supported")
        source = RigSemanticProfile.from_dict(payload["source_rig"])
        target = RigSemanticProfile.from_dict(payload["target_rig"])
        source_sha = _sha(payload["input_blend_sha256"], "input_blend_sha256")
        if source.input_blend_sha256 != source_sha or target.input_blend_sha256 != source_sha:
            raise BlenderBoundaryError("source/target rig lineage must match recipe input blend")
        clip = AnimationClip.from_dict(payload["clip"])
        raw = payload["mappings"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= 256 or not all(isinstance(item, dict) for item in raw):
            raise BlenderBoundaryError("mappings must contain 1-256 objects")
        mappings = tuple(BoneMapping.from_dict(item) for item in raw)
        if len({item.source_bone_id for item in mappings}) != len(mappings):
            raise BlenderBoundaryError("source semantic bones may be mapped only once")
        if len({item.target_bone_id for item in mappings}) != len(mappings):
            raise BlenderBoundaryError("target semantic bones may be mapped only once")
        source_ids = {item.bone_id for item in source.bones}
        target_ids = {item.bone_id for item in target.bones}
        for item in mappings:
            if item.source_bone_id not in source_ids or item.target_bone_id not in target_ids:
                raise BlenderBoundaryError("mapping references unknown semantic bone")
        if any(channel.bone_id not in source_ids for channel in clip.channels):
            raise BlenderBoundaryError("clip references a bone absent from source semantic profile")
        required_raw = payload["required_target_bones"]
        if not isinstance(required_raw, list) or len(required_raw) > 256 or not all(isinstance(item, str) for item in required_raw):
            raise BlenderBoundaryError("required_target_bones must be a string array")
        required_ids = tuple(_id(item, "required_target_bone") for item in required_raw)
        if len(set(required_ids)) != len(required_ids):
            raise BlenderBoundaryError("required_target_bones must be unique")
        if any(item not in target_ids for item in required_ids):
            raise BlenderBoundaryError("required target bone is absent from target profile")
        mapped_target = {item.target_bone_id for item in mappings}
        if any(item not in mapped_target for item in required_ids):
            raise BlenderBoundaryError("required target bone is unmapped")
        scale = _number(payload["translation_scale"], "translation_scale", 1e-6, 1_000_000.0)
        max_keys = payload["max_keys"]
        if isinstance(max_keys, bool) or not isinstance(max_keys, int) or not 1 <= max_keys <= 250_000:
            raise BlenderBoundaryError("max_keys must be an integer in [1, 250000]")
        if clip.key_count > max_keys:
            raise BlenderBoundaryError("clip key count exceeds max_keys budget")
        return cls(1, _id(payload["recipe_id"], "recipe_id"), source_sha, source, target, clip, mappings, required_ids, scale, max_keys)

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "recipe_id": self.recipe_id, "input_blend_sha256": self.input_blend_sha256, "source_rig": self.source_rig.to_dict(), "target_rig": self.target_rig.to_dict(), "clip": self.clip.to_dict(), "mappings": [item.to_dict() for item in self.mappings], "required_target_bones": list(self.required_target_bones), "translation_scale": self.translation_scale, "max_keys": self.max_keys}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())
