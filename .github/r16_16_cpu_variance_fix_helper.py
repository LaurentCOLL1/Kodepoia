from __future__ import annotations

import subprocess
from pathlib import Path

SOURCE_SHA = "3e2c9ec39f19664ba51a81f3b09e6a67cd4f77c9"
POLICY = Path("configs/r16_16_resource_soak_policy.json")
HARNESS = Path("src/kodepoia/quality/resource_soak.py")
TESTS = Path("tests/test_r16_16_resource_soak.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != SOURCE_SHA:
        raise SystemExit("R16.16 CPU variance helper is not on the expected rejected source")

    policy = POLICY.read_text(encoding="utf-8")
    policy = replace_once(
        policy,
        '    "max_repeat_cpu_ratio": 20.0,\n    "timeout_seconds": 30.0\n',
        '    "max_repeat_cpu_ratio": 20.0,\n    "min_repeat_cpu_sample_ms": 50.0,\n    "timeout_seconds": 30.0\n',
        "policy CPU significance floor",
    )
    POLICY.write_text(policy, encoding="utf-8", newline="\n")

    harness = HARNESS.read_text(encoding="utf-8")
    shared = '        "max_repeat_cpu_ratio",\n        "timeout_seconds",\n'
    if harness.count(shared) != 2:
        raise SystemExit("budget key contract: expected exactly two anchors")
    harness = harness.replace(
        shared,
        '        "max_repeat_cpu_ratio",\n        "min_repeat_cpu_sample_ms",\n        "timeout_seconds",\n',
    )
    harness = replace_once(
        harness,
        '    if float(budgets["max_wall_ms"]) > 60000 or float(budgets["timeout_seconds"]) > 60:\n        raise ResourceSoakGovernanceError("wall-clock budgets exceed bounded CI authority")\n',
        '    if float(budgets["max_wall_ms"]) > 60000 or float(budgets["timeout_seconds"]) > 60:\n        raise ResourceSoakGovernanceError("wall-clock budgets exceed bounded CI authority")\n    if float(budgets["min_repeat_cpu_sample_ms"]) > float(budgets["max_cpu_ms"]):\n        raise ResourceSoakGovernanceError("CPU significance floor exceeds the absolute CPU budget")\n',
        "CPU significance validation",
    )
    harness = replace_once(
        harness,
        'def _repeat_ratio(values: list[float], floor: float) -> float:\n    high = max(values)\n    low = min(values)\n    return round(high / max(low, floor), 6)\n\n\ndef sanitize_diagnostic',
        'def _repeat_ratio(values: list[float], floor: float) -> float:\n    high = max(values)\n    low = min(values)\n    return round(high / max(low, floor), 6)\n\n\ndef classify_cpu_repeatability(\n    values: list[float], budgets: Mapping[str, Any]\n) -> dict[str, Any]:\n    if not values:\n        raise ValueError("CPU repeatability requires at least one sample")\n    floor = float(budgets["min_repeat_cpu_sample_ms"])\n    if min(values) < floor:\n        return {\n            "state": "INCONCLUSIVE",\n            "ratio": None,\n            "significance_floor_ms": floor,\n            "detail": "CPU samples are below the frozen significance floor",\n        }\n    ratio = _repeat_ratio(values, floor)\n    state = "PASS" if ratio <= float(budgets["max_repeat_cpu_ratio"]) else "FAIL"\n    return {\n        "state": state,\n        "ratio": ratio,\n        "significance_floor_ms": floor,\n        "detail": "CPU repeat ratio evaluated from significant samples",\n    }\n\n\ndef sanitize_diagnostic',
        "CPU repeatability classifier",
    )
    harness = replace_once(
        harness,
        '        wall_ratio = _repeat_ratio([item.wall_ms for item in repetitions], 1.0)\n        cpu_ratio = _repeat_ratio([item.cpu_ms for item in repetitions], 1.0)\n        repeat_ok = (\n            wall_ratio <= float(budgets["max_repeat_wall_ratio"])\n            and cpu_ratio <= float(budgets["max_repeat_cpu_ratio"])\n        )\n        cases.append(\n            _case(\n                "repeat_runtime_variance_bounded",\n                repeat_ok,\n                f"normalized wall ratio={wall_ratio}; cpu ratio={cpu_ratio}",\n            )\n        )\n',
        '        wall_ratio = _repeat_ratio([item.wall_ms for item in repetitions], 1.0)\n        cpu_repeatability = classify_cpu_repeatability(\n            [item.cpu_ms for item in repetitions], budgets\n        )\n        repeat_ok = (\n            wall_ratio <= float(budgets["max_repeat_wall_ratio"])\n            and cpu_repeatability["state"] != "FAIL"\n        )\n        cases.append(\n            _case(\n                "repeat_runtime_variance_bounded",\n                repeat_ok,\n                (\n                    f"normalized wall ratio={wall_ratio}; "\n                    f"cpu state={cpu_repeatability[\'state\']}; "\n                    f"cpu ratio={cpu_repeatability[\'ratio\']}"\n                ),\n            )\n        )\n',
        "repeatability evaluation",
    )
    harness = replace_once(
        harness,
        '        "repeatability": {"wall_ratio": wall_ratio, "cpu_ratio": cpu_ratio},\n',
        '        "repeatability": {\n            "wall_ratio": wall_ratio,\n            "cpu": cpu_repeatability,\n        },\n',
        "repeatability evidence",
    )
    HARNESS.write_text(harness, encoding="utf-8", newline="\n")

    tests = TESTS.read_text(encoding="utf-8")
    tests = replace_once(
        tests,
        '    build_resource_soak_report,\n    canonical_sha256,\n',
        '    build_resource_soak_report,\n    canonical_sha256,\n    classify_cpu_repeatability,\n',
        "classifier test import",
    )
    anchor = (
        'def test_budget_evaluator_rejects_overrun() -> None:\n'
        '    policy = load_policy(ROOT)\n'
        '    budgets = policy["budgets"]\n'
        '    metrics = {\n'
        '        "wall_ms": budgets["max_wall_ms"] + 1,\n'
        '        "cpu_ms": 0,\n'
        '        "rss_growth_bytes": 0,\n'
        '        "heap_growth_bytes": 0,\n'
        '        "peak_heap_bytes": 0,\n'
        '        "peak_temp_bytes": 0,\n'
        '        "temp_bytes_after": 0,\n'
        '        "temp_files_after": 0,\n'
        '        "thread_delta_after": 0,\n'
        '    }\n'
        '    assert metrics_within_budget(metrics, budgets) is False\n\n\n'
    )
    addition = anchor + (
        'def test_cpu_repeatability_is_inconclusive_below_significance_floor() -> None:\n'
        '    budgets = load_policy(ROOT)["budgets"]\n'
        '    result = classify_cpu_repeatability([31.25, 0.0], budgets)\n'
        '    assert result["state"] == "INCONCLUSIVE"\n'
        '    assert result["ratio"] is None\n'
        '    assert result["significance_floor_ms"] == 50.0\n\n\n'
        'def test_cpu_repeatability_fails_when_significant_samples_regress() -> None:\n'
        '    budgets = load_policy(ROOT)["budgets"]\n'
        '    result = classify_cpu_repeatability([50.0, 1100.0], budgets)\n'
        '    assert result["state"] == "FAIL"\n'
        '    assert result["ratio"] == 22.0\n\n\n'
    )
    tests = replace_once(tests, anchor, addition, "CPU repeatability tests")
    TESTS.write_text(tests, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
