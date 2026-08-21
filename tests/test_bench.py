from pathlib import Path

from kodepoia.bench.baseline import BaselineBench, BenchTask
from kodepoia.brain.base import BrainResponse


class FakeBrain:
    def chat(self, model, messages, **kwargs):
        return BrainResponse("KODEPOIA_OK mutable CharacterBody3D", model, metrics={"eval_count": 3})


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
