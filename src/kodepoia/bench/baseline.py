from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kodepoia.brain.base import BrainMessage
from kodepoia.brain.ollama import OllamaClient


@dataclass(frozen=True, slots=True)
class BenchTask:
    id: str
    prompt: str
    expected_contains: tuple[str, ...] = ()
    response_schema: dict[str, Any] | None = None
    tools: tuple[dict[str, Any], ...] = ()
    expect_tool_call: bool = False


@dataclass(frozen=True, slots=True)
class BenchResult:
    model: str
    task_id: str
    elapsed_s: float
    passed: bool
    response: str
    metrics: dict[str, object]
    tokens_per_second: float | None = None
    structured_valid: bool | None = None
    tool_called: bool | None = None


STRUCTURED_STATUS_SCHEMA = {
    "type": "object",
    "properties": {"status": {"type": "string", "enum": ["ok"]}},
    "required": ["status"],
    "additionalProperties": False,
}

PROJECT_DNA_TOOL = {
    "type": "function",
    "function": {
        "name": "get_project_dna",
        "description": "Return the current Kodepoia project DNA.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


DEFAULT_TASKS = (
    BenchTask("exact-instruction", "Reply with exactly KODEPOIA_OK", ("KODEPOIA_OK",)),
    BenchTask(
        "python-reasoning",
        "In one sentence, explain why mutable default arguments in Python functions are risky.",
        ("mutable",),
    ),
    BenchTask(
        "godot-awareness",
        "Name the Godot 4 node used for a kinematic 3D character body.",
        ("CharacterBody3D",),
    ),
    BenchTask(
        "gdscript-typing",
        "Write one Godot 4 GDScript declaration for an integer variable named count initialized to 0, with an explicit type.",
        ("int", "count"),
    ),
    BenchTask(
        "debugging",
        "What value is commonly used instead of [] as a safe Python function default when the function may mutate the list?",
        ("None",),
    ),
    BenchTask(
        "structured-output",
        "Return a JSON object whose status is ok.",
        response_schema=STRUCTURED_STATUS_SCHEMA,
    ),
    BenchTask(
        "tool-calling",
        "Use the get_project_dna tool now. Do not invent the project DNA yourself.",
        tools=(PROJECT_DNA_TOOL,),
        expect_tool_call=True,
    ),
    BenchTask(
        "software-engineering",
        "Name the Git feature that lets one repository have multiple working directories attached to different branches.",
        ("worktree",),
    ),
)


class BaselineBench:
    def __init__(self, client: OllamaClient, tasks: tuple[BenchTask, ...] = DEFAULT_TASKS) -> None:
        self.client = client
        self.tasks = tasks

    @staticmethod
    def _structured_matches(content: str, schema: dict[str, Any]) -> bool:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return False
        if schema.get("type") == "object" and not isinstance(payload, dict):
            return False
        if isinstance(payload, dict):
            for key in schema.get("required", []):
                if key not in payload:
                    return False
            properties = schema.get("properties", {})
            for key, definition in properties.items():
                if key not in payload:
                    continue
                if "enum" in definition and payload[key] not in definition["enum"]:
                    return False
                if definition.get("type") == "string" and not isinstance(payload[key], str):
                    return False
            if schema.get("additionalProperties") is False:
                if set(payload) - set(properties):
                    return False
        return True

    @staticmethod
    def _tokens_per_second(metrics: dict[str, object]) -> float | None:
        count = metrics.get("eval_count")
        duration = metrics.get("eval_duration")
        if not isinstance(count, (int, float)) or not isinstance(duration, (int, float)):
            return None
        if duration <= 0:
            return None
        return float(count) / (float(duration) / 1_000_000_000.0)

    def run(self, models: list[str]) -> list[BenchResult]:
        if len(models) < 2:
            raise ValueError("Baseline comparison requires at least two models")
        results: list[BenchResult] = []
        for model in models:
            for task in self.tasks:
                start = time.perf_counter()
                response = self.client.chat(
                    model,
                    [BrainMessage("user", task.prompt)],
                    tools=list(task.tools) or None,
                    response_schema=task.response_schema,
                    think=False,
                    keep_alive="2m",
                )
                elapsed = time.perf_counter() - start
                lowered = response.content.lower()
                contains_ok = all(
                    expected.lower() in lowered for expected in task.expected_contains
                )
                structured_valid = (
                    self._structured_matches(response.content, task.response_schema)
                    if task.response_schema is not None
                    else None
                )
                tool_called = bool(response.tool_calls) if task.expect_tool_call else None
                passed = contains_ok
                if structured_valid is not None:
                    passed = passed and structured_valid
                if tool_called is not None:
                    passed = passed and tool_called
                metrics = dict(response.metrics or {})
                results.append(
                    BenchResult(
                        model=model,
                        task_id=task.id,
                        elapsed_s=elapsed,
                        passed=passed,
                        response=response.content,
                        metrics=metrics,
                        tokens_per_second=self._tokens_per_second(metrics),
                        structured_valid=structured_valid,
                        tool_called=tool_called,
                    )
                )
            unload = getattr(self.client, "unload", None)
            if callable(unload):
                unload(model)
        return results

    @staticmethod
    def summarize(results: list[BenchResult]) -> dict[str, dict[str, object]]:
        summary: dict[str, dict[str, object]] = {}
        models = list(dict.fromkeys(item.model for item in results))
        for model in models:
            rows = [item for item in results if item.model == model]
            speeds = [item.tokens_per_second for item in rows if item.tokens_per_second is not None]
            summary[model] = {
                "passed": sum(item.passed for item in rows),
                "total": len(rows),
                "score": round(sum(item.passed for item in rows) / len(rows), 4) if rows else 0.0,
                "elapsed_s": round(sum(item.elapsed_s for item in rows), 3),
                "avg_tokens_per_second": round(sum(speeds) / len(speeds), 3) if speeds else None,
            }
        return summary

    @staticmethod
    def save(
        results: list[BenchResult],
        path: Path,
        *,
        metadata: dict[str, object] | None = None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "host": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "processor": platform.processor(),
            },
            "metadata": metadata or {},
            "summary": BaselineBench.summarize(results),
            "results": [asdict(item) for item in results],
        }
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
