from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from kodepoia.brain.base import BrainMessage
from kodepoia.brain.ollama import OllamaClient


@dataclass(frozen=True, slots=True)
class BenchTask:
    id: str
    prompt: str
    expected_contains: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BenchResult:
    model: str
    task_id: str
    elapsed_s: float
    passed: bool
    response: str
    metrics: dict[str, object]


DEFAULT_TASKS = (
    BenchTask("structured-reply", "Reply with exactly KODEPOIA_OK", ("KODEPOIA_OK",)),
    BenchTask("python-reasoning", "In one sentence, explain why mutable default arguments in Python functions are risky.", ("mutable",)),
    BenchTask("godot-awareness", "Name the Godot 4 node used for a kinematic 3D character body.", ("CharacterBody3D",)),
)


class BaselineBench:
    def __init__(self, client: OllamaClient, tasks: tuple[BenchTask, ...] = DEFAULT_TASKS) -> None:
        self.client = client
        self.tasks = tasks

    def run(self, models: list[str]) -> list[BenchResult]:
        if len(models) < 2:
            raise ValueError("Baseline comparison requires at least two models")
        results: list[BenchResult] = []
        for model in models:
            for task in self.tasks:
                start = time.perf_counter()
                response = self.client.chat(model, [BrainMessage("user", task.prompt)], think=False, keep_alive="2m")
                elapsed = time.perf_counter() - start
                lowered = response.content.lower()
                passed = all(expected.lower() in lowered for expected in task.expected_contains)
                results.append(BenchResult(model, task.id, elapsed, passed, response.content, response.metrics or {}))
        return results

    @staticmethod
    def save(results: list[BenchResult], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2), encoding="utf-8")
