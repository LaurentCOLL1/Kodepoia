from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.brain.base import BrainMessage
from kodepoia.brain.ollama import OllamaClient
from kodepoia.exceptions import BrainUnavailable


class BenchmarkRole(StrEnum):
    BASELINE = "baseline"
    FAST = "fast"
    CORE = "core"
    CODER = "coder"


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
    thinking_mode: bool | str | None = None
    error: str | None = None


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
            if schema.get("additionalProperties") is False and set(payload) - set(properties):
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

    def _runtime_metrics(self, model: str) -> dict[str, object]:
        running_models = getattr(self.client, "running_models", None)
        if not callable(running_models):
            return {}
        try:
            running = running_models()
        except BrainUnavailable:
            return {}
        for item in running:
            if str(item.get("name")) != model:
                continue
            metrics: dict[str, object] = {}
            for key in ("size", "size_vram", "expires_at"):
                if key in item:
                    metrics[f"ollama_{key}"] = item[key]
            details = item.get("details")
            if isinstance(details, dict):
                for key in ("family", "parameter_size", "quantization_level"):
                    if key in details:
                        metrics[f"ollama_{key}"] = details[key]
            return metrics
        return {}

    def _thinking_mode(self, model: str, role: BenchmarkRole) -> bool | str | None:
        if role in {BenchmarkRole.BASELINE, BenchmarkRole.FAST}:
            return False
        show_model = getattr(self.client, "show_model", None)
        if not callable(show_model):
            return None
        try:
            details = show_model(model)
        except BrainUnavailable:
            return None
        capabilities = {str(value).lower() for value in details.get("capabilities", [])}
        if "thinking" not in capabilities:
            return None
        model_details = details.get("details", {})
        family = str(model_details.get("family", "")).lower() if isinstance(model_details, dict) else ""
        normalized = model.lower()
        if family == "gptoss" or normalized.startswith("gpt-oss"):
            return "medium"
        return True

    def run(
        self,
        models: list[str],
        *,
        role: BenchmarkRole | str = BenchmarkRole.BASELINE,
    ) -> list[BenchResult]:
        if len(models) < 2:
            raise ValueError("Baseline comparison requires at least two models")
        role = BenchmarkRole(role)
        results: list[BenchResult] = []
        for model in models:
            think = self._thinking_mode(model, role)
            for task in self.tasks:
                start = time.perf_counter()
                try:
                    response = self.client.chat(
                        model,
                        [BrainMessage("user", task.prompt)],
                        tools=list(task.tools) or None,
                        response_schema=task.response_schema,
                        think=think,
                        keep_alive="2m",
                    )
                except BrainUnavailable as exc:
                    results.append(
                        BenchResult(
                            model=model,
                            task_id=task.id,
                            elapsed_s=time.perf_counter() - start,
                            passed=False,
                            response="",
                            metrics={},
                            structured_valid=False if task.response_schema is not None else None,
                            tool_called=False if task.expect_tool_call else None,
                            thinking_mode=think,
                            error=str(exc),
                        )
                    )
                    continue

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
                metrics.update(self._runtime_metrics(model))
                if response.thinking:
                    metrics["thinking_chars"] = len(response.thinking)
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
                        thinking_mode=think,
                    )
                )
            unload = getattr(self.client, "unload", None)
            if callable(unload):
                try:
                    unload(model)
                except BrainUnavailable:
                    pass
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
                "errors": sum(item.error is not None for item in rows),
                "thinking_mode": rows[0].thinking_mode if rows else None,
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
