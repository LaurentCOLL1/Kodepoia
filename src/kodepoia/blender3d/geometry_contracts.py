from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable

from .errors import BlenderBoundaryError
from .serialization import canonical_sha256

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_ALLOWED_PRIMITIVES = frozenset({"cube", "plane", "cylinder"})
_ALLOWED_MODIFIERS = frozenset({"triangulate", "mirror", "solidify", "bevel"})


class GeometryOperation(StrEnum):
    RESET_SCENE = "reset_scene"
    CREATE_PRIMITIVE = "create_primitive"
    TRANSFORM = "transform"
    APPLY_TRANSFORM = "apply_transform"
    TRIANGULATE = "triangulate"
    RECALCULATE_NORMALS = "recalculate_normals"
    ADD_MODIFIER = "add_modifier"
    APPLY_MODIFIER = "apply_modifier"
    JOIN = "join"
    SEPARATE_LOOSE = "separate_loose"
    SET_ORIGIN = "set_origin"


def _finite_number(value: Any, *, name: str, limit: float = 1_000_000.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderBoundaryError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or abs(result) > limit:
        raise BlenderBoundaryError(f"{name} is outside the R10.3 numeric budget")
    return result


def _vector3(value: Any, *, name: str, scale: bool = False) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise BlenderBoundaryError(f"{name} must contain exactly three numbers")
    result = tuple(_finite_number(item, name=name) for item in value)
    if scale and any(abs(item) < 1e-9 or abs(item) > 1000.0 for item in result):
        raise BlenderBoundaryError(f"{name} contains an invalid scale component")
    return result  # type: ignore[return-value]


def _object_id(value: Any) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError("Geometry object IDs must match ^[a-z][a-z0-9_.-]{0,63}$")
    return value


@dataclass(frozen=True, slots=True)
class GeometryStep:
    operation: GeometryOperation
    params: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GeometryStep":
        if set(payload) != {"operation", "params"}:
            raise BlenderBoundaryError("Geometry steps require exactly operation + params")
        try:
            operation = GeometryOperation(payload["operation"])
        except (ValueError, TypeError) as exc:
            raise BlenderBoundaryError("Unsupported R10.3 geometry operation") from exc
        params = payload["params"]
        if not isinstance(params, dict):
            raise BlenderBoundaryError("Geometry step params must be an object")
        return cls(operation=operation, params=dict(params))


@dataclass(frozen=True, slots=True)
class GeometryRecipe:
    version: int
    recipe_id: str
    steps: tuple[GeometryStep, ...]
    units: str = "METERS"
    forward_axis: str = "-Z"
    up_axis: str = "Y"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GeometryRecipe":
        allowed = {"version", "recipe_id", "steps", "units", "forward_axis", "up_axis"}
        if set(payload) - allowed:
            raise BlenderBoundaryError("Geometry recipe contains unknown fields")
        if payload.get("version") != 1:
            raise BlenderBoundaryError("Only geometry recipe version 1 is supported")
        recipe_id = _object_id(payload.get("recipe_id"))
        raw_steps = payload.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps or len(raw_steps) > 256:
            raise BlenderBoundaryError("Geometry recipe must contain 1-256 steps")
        steps = tuple(GeometryStep.from_dict(item) for item in raw_steps if isinstance(item, dict))
        if len(steps) != len(raw_steps):
            raise BlenderBoundaryError("Every geometry step must be an object")
        recipe = cls(
            version=1,
            recipe_id=recipe_id,
            steps=steps,
            units=str(payload.get("units", "METERS")),
            forward_axis=str(payload.get("forward_axis", "-Z")),
            up_axis=str(payload.get("up_axis", "Y")),
        )
        recipe.validate()
        return recipe

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "recipe_id": self.recipe_id,
            "units": self.units,
            "forward_axis": self.forward_axis,
            "up_axis": self.up_axis,
            "steps": [{"operation": step.operation.value, "params": step.params} for step in self.steps],
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())

    def validate(self) -> None:
        if self.units != "METERS" or self.forward_axis != "-Z" or self.up_axis != "Y":
            raise BlenderBoundaryError("R10.3 v1 freezes units=METERS, forward=-Z, up=Y")
        declared: set[str] = set()
        modifier_names: dict[str, set[str]] = {}
        for index, step in enumerate(self.steps):
            params = step.params
            op = step.operation
            if op is GeometryOperation.RESET_SCENE:
                if params:
                    raise BlenderBoundaryError("reset_scene accepts no params")
                declared.clear()
                modifier_names.clear()
                continue
            if op is GeometryOperation.CREATE_PRIMITIVE:
                expected = {"object_id", "primitive", "display_name"}
                if set(params) - expected:
                    raise BlenderBoundaryError("create_primitive contains unknown params")
                object_id = _object_id(params.get("object_id"))
                if object_id in declared:
                    raise BlenderBoundaryError(f"Duplicate geometry object_id: {object_id}")
                primitive = params.get("primitive")
                if primitive not in _ALLOWED_PRIMITIVES:
                    raise BlenderBoundaryError("Primitive is not allowlisted")
                display_name = params.get("display_name", object_id)
                if not isinstance(display_name, str) or not display_name or len(display_name) > 80:
                    raise BlenderBoundaryError("display_name must be 1-80 characters")
                declared.add(object_id)
                modifier_names[object_id] = set()
                continue

            object_id = _object_id(params.get("object_id")) if "object_id" in params else None
            if object_id is not None and object_id not in declared:
                raise BlenderBoundaryError(f"Step {index} references undeclared object_id: {object_id}")

            if op is GeometryOperation.TRANSFORM:
                allowed = {"object_id", "location", "rotation", "scale"}
                if set(params) - allowed:
                    raise BlenderBoundaryError("transform contains unknown params")
                if "location" in params:
                    _vector3(params["location"], name="location")
                if "rotation" in params:
                    _vector3(params["rotation"], name="rotation")
                if "scale" in params:
                    _vector3(params["scale"], name="scale", scale=True)
                if len(params) == 1:
                    raise BlenderBoundaryError("transform requires at least one transform value")
            elif op is GeometryOperation.APPLY_TRANSFORM:
                allowed = {"object_id", "location", "rotation", "scale"}
                if set(params) - allowed:
                    raise BlenderBoundaryError("apply_transform contains unknown params")
                for key in ("location", "rotation", "scale"):
                    if key in params and not isinstance(params[key], bool):
                        raise BlenderBoundaryError(f"{key} apply flag must be boolean")
            elif op is GeometryOperation.TRIANGULATE:
                if set(params) - {"object_id", "quad_method", "ngon_method"}:
                    raise BlenderBoundaryError("triangulate contains unknown params")
                if params.get("quad_method", "FIXED") not in {"FIXED", "ALTERNATE", "SHORT_EDGE", "LONG_EDGE", "BEAUTY"}:
                    raise BlenderBoundaryError("Unsupported triangulate quad_method")
                if params.get("ngon_method", "EAR_CLIP") not in {"EAR_CLIP", "BEAUTY"}:
                    raise BlenderBoundaryError("Unsupported triangulate ngon_method")
            elif op is GeometryOperation.RECALCULATE_NORMALS:
                if set(params) != {"object_id"}:
                    raise BlenderBoundaryError("recalculate_normals requires only object_id")
            elif op is GeometryOperation.ADD_MODIFIER:
                allowed = {"object_id", "name", "modifier", "settings"}
                if set(params) != allowed:
                    raise BlenderBoundaryError("add_modifier requires object_id/name/modifier/settings")
                name = _object_id(params["name"])
                modifier = params["modifier"]
                settings = params["settings"]
                if modifier not in _ALLOWED_MODIFIERS or not isinstance(settings, dict):
                    raise BlenderBoundaryError("Modifier/settings are not allowlisted")
                if name in modifier_names[object_id]:
                    raise BlenderBoundaryError("Modifier names must be unique per object")
                _validate_modifier_settings(str(modifier), settings)
                modifier_names[object_id].add(name)
            elif op is GeometryOperation.APPLY_MODIFIER:
                if set(params) != {"object_id", "name"}:
                    raise BlenderBoundaryError("apply_modifier requires object_id + name")
                name = _object_id(params["name"])
                if name not in modifier_names[object_id]:
                    raise BlenderBoundaryError("apply_modifier references an undeclared modifier")
            elif op is GeometryOperation.JOIN:
                if set(params) != {"object_id", "sources"}:
                    raise BlenderBoundaryError("join requires object_id + sources")
                sources = params["sources"]
                if not isinstance(sources, list) or not sources:
                    raise BlenderBoundaryError("join sources must be non-empty")
                resolved = [_object_id(item) for item in sources]
                if object_id in resolved or any(item not in declared for item in resolved):
                    raise BlenderBoundaryError("join sources must be declared and exclude the target")
                for item in resolved:
                    declared.remove(item)
                    modifier_names.pop(item, None)
            elif op is GeometryOperation.SEPARATE_LOOSE:
                if set(params) != {"object_id", "new_object_ids"}:
                    raise BlenderBoundaryError("separate_loose requires object_id + new_object_ids")
                new_ids = params["new_object_ids"]
                if not isinstance(new_ids, list) or not new_ids or len(new_ids) > 32:
                    raise BlenderBoundaryError("new_object_ids must contain 1-32 IDs")
                for item in new_ids:
                    new_id = _object_id(item)
                    if new_id in declared:
                        raise BlenderBoundaryError("separate_loose new IDs must be unique")
                    declared.add(new_id)
                    modifier_names[new_id] = set()
            elif op is GeometryOperation.SET_ORIGIN:
                if set(params) != {"object_id", "mode"} or params["mode"] not in {"GEOMETRY", "CURSOR_ZERO"}:
                    raise BlenderBoundaryError("set_origin mode must be GEOMETRY or CURSOR_ZERO")
            else:
                raise BlenderBoundaryError("Unsupported R10.3 geometry operation")


def _validate_modifier_settings(modifier: str, settings: dict[str, Any]) -> None:
    if modifier == "triangulate":
        allowed = {"quad_method", "ngon_method", "keep_custom_normals", "min_vertices"}
        if set(settings) - allowed:
            raise BlenderBoundaryError("triangulate modifier contains unknown settings")
        min_vertices = settings.get("min_vertices", 4)
        if not isinstance(min_vertices, int) or isinstance(min_vertices, bool) or not 4 <= min_vertices <= 64:
            raise BlenderBoundaryError("triangulate min_vertices must be 4-64")
    elif modifier == "mirror":
        if set(settings) - {"axis", "merge", "merge_threshold"}:
            raise BlenderBoundaryError("mirror modifier contains unknown settings")
        axis = settings.get("axis", "X")
        if axis not in {"X", "Y", "Z"}:
            raise BlenderBoundaryError("mirror axis must be X/Y/Z")
        threshold = _finite_number(settings.get("merge_threshold", 0.001), name="merge_threshold", limit=1.0)
        if threshold < 0:
            raise BlenderBoundaryError("merge_threshold cannot be negative")
    elif modifier == "solidify":
        if set(settings) - {"thickness", "offset"}:
            raise BlenderBoundaryError("solidify modifier contains unknown settings")
        _finite_number(settings.get("thickness", 0.01), name="thickness", limit=100.0)
        offset = _finite_number(settings.get("offset", 0.0), name="offset", limit=1.0)
        if not -1.0 <= offset <= 1.0:
            raise BlenderBoundaryError("solidify offset must be -1..1")
    elif modifier == "bevel":
        if set(settings) - {"width", "segments"}:
            raise BlenderBoundaryError("bevel modifier contains unknown settings")
        width = _finite_number(settings.get("width", 0.01), name="width", limit=100.0)
        segments = settings.get("segments", 1)
        if width < 0 or not isinstance(segments, int) or isinstance(segments, bool) or not 1 <= segments <= 16:
            raise BlenderBoundaryError("Invalid bevel settings")


def geometry_recipe_digest(payload: dict[str, Any]) -> str:
    return GeometryRecipe.from_dict(payload).digest


def validate_geometry_recipes(recipes: Iterable[dict[str, Any]]) -> tuple[GeometryRecipe, ...]:
    return tuple(GeometryRecipe.from_dict(item) for item in recipes)
