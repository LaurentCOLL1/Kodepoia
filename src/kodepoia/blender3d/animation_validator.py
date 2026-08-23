from __future__ import annotations

from typing import Any

from .animation_contracts import RetargetRecipe
from .serialization import canonical_sha256

_REST_DIRECTION_TOLERANCE_DEGREES = 30.0
_REST_LENGTH_RELATIVE_TOLERANCE = 0.50


def evaluate_animation_measurements(recipe: RetargetRecipe, measurements: dict[str, Any]) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []

    def add(rule_id: str, state: str, measured: Any, expected: Any, reason: str) -> None:
        rules.append({"rule_id": rule_id, "state": state, "measured": measured, "expected": expected, "reason": reason})

    mapping = measurements.get("mapping") if isinstance(measurements.get("mapping"), dict) else {}
    mapped = int(mapping.get("mapped_bones", -1)) if isinstance(mapping.get("mapped_bones"), int) else -1
    required_missing = mapping.get("missing_required", [])
    ambiguous = mapping.get("ambiguous", [])
    add("mapping_coverage", "PASS" if mapped == len(recipe.mappings) else "BLOCK", mapped, len(recipe.mappings), "all explicit mappings must resolve exactly once")
    add("required_target_mapping", "PASS" if required_missing == [] else "BLOCK", required_missing, [], "required target bones must be mapped")
    add("mapping_ambiguity", "PASS" if ambiguous == [] else "BLOCK", ambiguous, [], "retarget mapping must remain unambiguous")

    rest = measurements.get("rest_pose") if isinstance(measurements.get("rest_pose"), dict) else {}
    angle = rest.get("max_direction_angle_degrees")
    length_error = rest.get("max_scaled_length_relative_error")
    add(
        "rest_direction_compatibility",
        "PASS" if isinstance(angle, (int, float)) and float(angle) <= _REST_DIRECTION_TOLERANCE_DEGREES else "BLOCK",
        angle,
        f"<= {_REST_DIRECTION_TOLERANCE_DEGREES}",
        "mapped bone rest directions must be compatible after the frozen R10 coordinate basis",
    )
    add(
        "rest_length_compatibility",
        "PASS" if isinstance(length_error, (int, float)) and float(length_error) <= _REST_LENGTH_RELATIVE_TOLERANCE else "BLOCK",
        length_error,
        f"<= {_REST_LENGTH_RELATIVE_TOLERANCE}",
        "mapped rest lengths must remain compatible after translation_scale normalization",
    )

    clip = measurements.get("clip") if isinstance(measurements.get("clip"), dict) else {}
    key_count = clip.get("key_count")
    frame_start = clip.get("frame_start")
    frame_end = clip.get("frame_end")
    loop = clip.get("loop")
    add("key_budget", "PASS" if isinstance(key_count, int) and 0 < key_count <= recipe.max_keys else "BLOCK", key_count, f"1..{recipe.max_keys}", "retargeted key count must remain inside budget")
    add("frame_start", "PASS" if frame_start == recipe.clip.frame_start else "BLOCK", frame_start, recipe.clip.frame_start, "clip start must be deterministic")
    add("frame_end", "PASS" if frame_end == recipe.clip.frame_end else "BLOCK", frame_end, recipe.clip.frame_end, "clip end must be deterministic")
    add("loop_policy", "PASS" if loop is recipe.clip.loop else "BLOCK", loop, recipe.clip.loop, "loop policy must match recipe")

    nla = measurements.get("nla") if isinstance(measurements.get("nla"), dict) else {}
    add("nla_track_count", "PASS" if nla.get("track_count") == 1 else "BLOCK", nla.get("track_count"), 1, "R10.7 fixture produces exactly one governed NLA track")
    add("nla_strip_count", "PASS" if nla.get("strip_count") == 1 else "BLOCK", nla.get("strip_count"), 1, "R10.7 fixture produces exactly one governed action strip")

    root = measurements.get("root_motion") if isinstance(measurements.get("root_motion"), dict) else {}
    drift = root.get("translation_delta")
    if recipe.clip.root_motion.value == "zero":
        root_state = "PASS" if isinstance(drift, (int, float)) and abs(float(drift)) <= 1e-6 else "BLOCK"
        root_expected: Any = 0.0
    else:
        root_state = "PASS" if isinstance(drift, (int, float)) and float(drift) >= 0.0 else "BLOCK"
        root_expected = ">=0"
    add("root_motion_policy", root_state, drift, root_expected, "root-motion policy must be explicit and measurable")

    summary = {"pass": sum(item["state"] == "PASS" for item in rules), "warn": sum(item["state"] == "WARN" for item in rules), "block": sum(item["state"] == "BLOCK" for item in rules)}
    status = "block" if summary["block"] else ("warn" if summary["warn"] else "pass")
    report = {"schema": "kodepoia.blender.animation_report", "version": 1, "recipe_id": recipe.recipe_id, "recipe_digest": recipe.digest, "status": status, "summary": summary, "rules": rules}
    report["report_digest"] = canonical_sha256(report)
    return report
