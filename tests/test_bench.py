from pathlib import Path

from kodepoia.bench.baseline import BaselineBench, BenchmarkRole, BenchTask
from kodepoia.brain.base import BrainResponse


class FakeBrain:
    def __init__(self):
        self.calls = []
        self.unloaded = []

    def chat(self, model, messages, **kwargs):
        self.calls.append((model, messages[0].content, kwargs))
        prompt = messages[0].content
        if "exactly KODEPOIA_OK" in prompt:
            content = "KODEPOIA_OK"
        elif "script-controlled 3D character body" in prompt:
            content = "CharacterBody3D"
        elif "integer variable named count" in prompt:
            content = "var count: int = 0"
        elif "multiple working directories" in prompt:
            content = "git worktree"
        elif "status is ok" in prompt:
            content = '{"status":"ok"}'
        elif "get_project_dna" in prompt:
            content = ""
        elif "mutable default" in prompt:
            content = "mutable defaults share state"
        elif "safe Python function default" in prompt:
            content = "None"
        else:
            content = "KODEPOIA_OK"
        thinking = "reasoning" if kwargs.get("think") in {True, "medium"} else None
        tool_calls = ({"function": {"name": "get_project_dna", "arguments": {}}},) if "get_project_dna" in prompt else ()
        return BrainResponse(
            content,
            model,
            thinking=thinking,
            tool_calls=tool_calls,
            metrics={"eval_count": 3, "eval_duration": 1_000_000_000, "load_duration": 2_000_000_000},
        )

    def show_model(self, model):
        if model == "plain":
            return {"capabilities": ["completion"], "details": {"family": "plain"}}
        if model == "gpt-oss:20b":
            return {"capabilities": ["completion", "thinking", "tools"], "details": {"family": "gptoss"}}
        return {"capabilities": ["completion", "thinking", "tools"], "details": {"family": "qwen35"}}

    def running_models(self):
        return []

    def unload(self, model):
        self.unloaded.append(model)


def test_baseline_requires_multiple_models() -> None:
    bench = BaselineBench(FakeBrain(), (BenchTask("x", "x", exact_response="KODEPOIA_OK"),))
    try:
        bench.run(["one"])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_baseline_rejects_invalid_repeat_count() -> None:
    bench = BaselineBench(FakeBrain(), (BenchTask("x", "x", exact_response="KODEPOIA_OK"),))
    for repeats in (0, 9):
        try:
            bench.run(["one", "two"], repeats=repeats)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_baseline_runs_repeated_and_saves(tmp_path: Path) -> None:
    brain = FakeBrain()
    bench = BaselineBench(brain, (BenchTask("x", "x", exact_response="KODEPOIA_OK"),))
    results = bench.run(["one", "two"], repeats=4)
    assert len(results) == 8
    assert all(item.passed for item in results)
    assert {item.repeat for item in results} == {1, 2, 3, 4}
    assert {item.seed for item in results} == {101, 102, 103, 104}
    assert len(brain.unloaded) == 8
    assert all(call[2]["options"]["temperature"] == 0.0 for call in brain.calls)
    assert all(call[2]["options"]["num_predict"] == 256 for call in brain.calls)
    summary = BaselineBench.summarize(results)
    assert summary["one"]["repeats"] == 4
    assert summary["one"]["min_repeat_score"] == 1.0
    assert summary["one"]["score_stddev"] == 0.0
    assert summary["one"]["task_pass_rates"]["x"] == 1.0
    path = tmp_path / "bench.json"
    bench.save(results, path)
    assert path.exists()
    assert '"schema_version": 2' in path.read_text(encoding="utf-8")


def test_strict_content_validators_reject_false_positives() -> None:
    godot = BenchTask(
        "godot",
        "x",
        ("CharacterBody3D",),
        ("KinematicBody3D",),
    )
    assert BaselineBench._content_matches("CharacterBody3D", godot)
    assert not BaselineBench._content_matches(
        "KinematicBody3D is the answer; CharacterBody3D is mentioned later",
        godot,
    )

    gdscript = BenchTask("gdscript", "x", response_regex=r"\bvar\s+count\s*:\s*int\s*=\s*0\b")
    assert BaselineBench._content_matches("var count: int = 0", gdscript)
    assert not BaselineBench._content_matches("int count = 0;", gdscript)
    assert not BaselineBench._content_matches("count: int = 0", gdscript)

    exact = BenchTask("exact", "x", exact_response="KODEPOIA_OK")
    assert BaselineBench._content_matches("KODEPOIA_OK", exact)
    assert not BaselineBench._content_matches("Answer: KODEPOIA_OK", exact)


def test_fast_profile_disables_thinking() -> None:
    brain = FakeBrain()
    bench = BaselineBench(brain, (BenchTask("x", "x", exact_response="KODEPOIA_OK"),))
    results = bench.run(["qwen3.5:4b", "plain"], role=BenchmarkRole.FAST)
    assert [item.thinking_mode for item in results] == [False, False]
    assert all(call[2]["think"] is False for call in brain.calls)


def test_core_profile_auto_enables_supported_thinking() -> None:
    brain = FakeBrain()
    bench = BaselineBench(brain, (BenchTask("x", "x", exact_response="KODEPOIA_OK"),))
    results = bench.run(["qwen3.6:27b", "gpt-oss:20b", "plain"], role=BenchmarkRole.CORE)
    modes = {item.model: item.thinking_mode for item in results}
    assert modes["qwen3.6:27b"] is True
    assert modes["gpt-oss:20b"] == "medium"
    assert modes["plain"] is None
