from pathlib import Path

from kodepoia.bench.baseline import BaselineBench, BenchmarkRole, BenchTask
from kodepoia.brain.base import BrainResponse


class FakeBrain:
    def __init__(self):
        self.calls = []

    def chat(self, model, messages, **kwargs):
        self.calls.append((model, kwargs))
        thinking = "reasoning" if kwargs.get("think") in {True, "medium"} else None
        return BrainResponse(
            "KODEPOIA_OK mutable CharacterBody3D",
            model,
            thinking=thinking,
            metrics={"eval_count": 3},
        )

    def show_model(self, model):
        if model == "plain":
            return {"capabilities": ["completion"], "details": {"family": "plain"}}
        if model == "gpt-oss:20b":
            return {"capabilities": ["completion", "thinking", "tools"], "details": {"family": "gptoss"}}
        return {"capabilities": ["completion", "thinking", "tools"], "details": {"family": "qwen35"}}


def test_baseline_requires_multiple_models() -> None:
    bench = BaselineBench(FakeBrain(), (BenchTask("x", "x", ("KODEPOIA_OK",)),))
    try:
        bench.run(["one"])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_baseline_runs_and_saves(tmp_path: Path) -> None:
    bench = BaselineBench(FakeBrain(), (BenchTask("x", "x", ("KODEPOIA_OK",)),))
    results = bench.run(["one", "two"])
    assert all(item.passed for item in results)
    path = tmp_path / "bench.json"
    bench.save(results, path)
    assert path.exists()


def test_fast_profile_disables_thinking() -> None:
    brain = FakeBrain()
    bench = BaselineBench(brain, (BenchTask("x", "x", ("KODEPOIA_OK",)),))
    results = bench.run(["qwen3.5:4b", "plain"], role=BenchmarkRole.FAST)
    assert [item.thinking_mode for item in results] == [False, False]
    assert all(call[1]["think"] is False for call in brain.calls)


def test_core_profile_auto_enables_supported_thinking() -> None:
    brain = FakeBrain()
    bench = BaselineBench(brain, (BenchTask("x", "x", ("KODEPOIA_OK",)),))
    results = bench.run(["qwen3.6:27b", "gpt-oss:20b", "plain"], role=BenchmarkRole.CORE)
    modes = {item.model: item.thinking_mode for item in results}
    assert modes["qwen3.6:27b"] is True
    assert modes["gpt-oss:20b"] == "medium"
    assert modes["plain"] is None
