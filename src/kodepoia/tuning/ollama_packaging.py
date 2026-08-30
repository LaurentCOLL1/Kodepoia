from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from kodepoia.brain.base import BrainMessage
from kodepoia.tuning.gguf import GgufConversionError, digest_path, inspect_gguf

OLLAMA_PACKAGE_SCHEMA = "kodepoia.r15.13.ollama-package"
OLLAMA_PACKAGE_SCHEMA_VERSION = 1
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost"})
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
_SAFE_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}(?::[A-Za-z0-9][A-Za-z0-9._-]{0,63})?$")
_SAFE_PARAMETER = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class OllamaPackagingError(ValueError):
    """Raised when R15.13 packaging cannot prove immutable local-model safety."""


class ArtifactKind(StrEnum):
    GGUF = "gguf"
    SAFETENSORS_ADAPTER = "safetensors_adapter"


class PackageDisposition(StrEnum):
    ACCEPT = "accept"
    REJECT_QUALITY = "reject_quality"
    REJECT_CRITICAL = "reject_critical"


@dataclass(frozen=True, slots=True)
class ToolRunResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


ToolRunner = Callable[[Sequence[str]], ToolRunResult]


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_digest(label: str, value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise OllamaPackagingError(f"{label} must be 64 lowercase hex characters")
    return value


def _require_safe_id(label: str, value: str) -> str:
    if _SAFE_ID.fullmatch(value) is None:
        raise OllamaPackagingError(f"{label} must be a stable safe identifier")
    return value


def _require_model_name(label: str, value: str) -> str:
    if _SAFE_MODEL.fullmatch(value) is None or ".." in value or value.startswith("/"):
        raise OllamaPackagingError(f"{label} must be a safe Ollama model name")
    return value


def _require_bounded_text(label: str, value: str, *, limit: int = 4096) -> str:
    if not value or len(value) > limit or "\x00" in value:
        raise OllamaPackagingError(f"{label} must be bounded non-empty text")
    return value


def require_loopback_origin(base_url: str) -> str:
    parsed = urlparse(base_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise OllamaPackagingError("Ollama endpoint requires a valid explicit port") from exc
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme not in {"http", "https"}
        or host not in _LOOPBACK
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise OllamaPackagingError(
            "R15.13 requires a credential-free explicit-port loopback Ollama origin"
        )
    return base_url.rstrip("/")


@dataclass(frozen=True, slots=True)
class OllamaBinding:
    candidate_id: str
    artifact_kind: ArtifactKind
    artifact_sha256: str
    base_model: str
    base_digest: str
    export_manifest_digest: str
    evaluation_digest: str
    gguf_report_digest: str
    architecture: str
    trained_base_model: str | None = None
    trained_base_digest: str | None = None
    direct_adapter_authorized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_safe_id("candidate_id", self.candidate_id))
        object.__setattr__(self, "architecture", _require_safe_id("architecture", self.architecture))
        object.__setattr__(self, "base_model", _require_model_name("base_model", self.base_model))
        for field in (
            "artifact_sha256",
            "base_digest",
            "export_manifest_digest",
            "evaluation_digest",
            "gguf_report_digest",
        ):
            _require_digest(field, getattr(self, field))
        if self.artifact_kind is ArtifactKind.SAFETENSORS_ADAPTER:
            if not self.direct_adapter_authorized:
                raise OllamaPackagingError(
                    "direct adapter packaging is not authorized; prefer validated merged/GGUF export"
                )
            if self.trained_base_model is None or self.trained_base_digest is None:
                raise OllamaPackagingError("adapter packaging requires immutable training-base identity")
            _require_model_name("trained_base_model", self.trained_base_model)
            _require_digest("trained_base_digest", self.trained_base_digest)
            if (
                self.trained_base_model != self.base_model
                or self.trained_base_digest != self.base_digest
            ):
                raise OllamaPackagingError("adapter/base identity mismatch")
        elif self.trained_base_model is not None or self.trained_base_digest is not None:
            raise OllamaPackagingError("merged/GGUF packaging must not claim a direct adapter binding")

    def descriptor(self) -> dict[str, object]:
        return {
            "architecture": self.architecture,
            "artifact_kind": self.artifact_kind.value,
            "artifact_sha256": self.artifact_sha256,
            "base_digest": self.base_digest,
            "base_model": self.base_model,
            "candidate_id": self.candidate_id,
            "direct_adapter_authorized": self.direct_adapter_authorized,
            "evaluation_digest": self.evaluation_digest,
            "export_manifest_digest": self.export_manifest_digest,
            "gguf_report_digest": self.gguf_report_digest,
            "trained_base_digest": self.trained_base_digest,
            "trained_base_model": self.trained_base_model,
        }


@dataclass(frozen=True, slots=True)
class PackagingConfig:
    binding: OllamaBinding
    artifact_path: Path
    license_text: str
    parameters: Mapping[str, int | float | str]
    template: str | None = None
    system: str | None = None
    expected_capabilities: tuple[str, ...] = ("completion",)
    max_aggregate_loss: float = 0.03
    max_critical_loss: float = 0.0

    def __post_init__(self) -> None:
        _require_bounded_text("license", self.license_text, limit=8192)
        if '"""' in self.license_text:
            raise OllamaPackagingError('license cannot contain triple-quote delimiter')
        if self.template is not None:
            _require_bounded_text("template", self.template, limit=32768)
            if '"""' in self.template:
                raise OllamaPackagingError('template cannot contain triple-quote delimiter')
        if self.system is not None:
            _require_bounded_text("system", self.system, limit=8192)
            if '"""' in self.system:
                raise OllamaPackagingError('system cannot contain triple-quote delimiter')
        if not 0.0 <= self.max_aggregate_loss <= 1.0:
            raise OllamaPackagingError("max_aggregate_loss must be within [0, 1]")
        if not 0.0 <= self.max_critical_loss <= 1.0:
            raise OllamaPackagingError("max_critical_loss must be within [0, 1]")
        normalized: list[str] = []
        for capability in self.expected_capabilities:
            normalized.append(_require_safe_id("capability", capability).lower())
        if not normalized:
            raise OllamaPackagingError("at least one expected capability is required")
        if len(set(normalized)) != len(normalized):
            raise OllamaPackagingError("duplicate expected capabilities are not allowed")
        for key, value in self.parameters.items():
            if _SAFE_PARAMETER.fullmatch(key) is None:
                raise OllamaPackagingError("parameter name is not a safe structured value")
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise OllamaPackagingError("parameter value must be int, float, or bounded string")
            if isinstance(value, str):
                _require_bounded_text("parameter value", value, limit=256)
                if "\n" in value or "\r" in value:
                    raise OllamaPackagingError("parameter string cannot contain newlines")

    def descriptor(self) -> dict[str, object]:
        return {
            "expected_capabilities": sorted(cap.lower() for cap in self.expected_capabilities),
            "max_aggregate_loss": self.max_aggregate_loss,
            "max_critical_loss": self.max_critical_loss,
            "parameters": {key: self.parameters[key] for key in sorted(self.parameters)},
            "system_present": self.system is not None,
            "template_present": self.template is not None,
        }


@dataclass(frozen=True, slots=True)
class BenchScore:
    task_id: str
    domain: str
    pre_import: float
    packaged: float
    critical: bool = False

    def __post_init__(self) -> None:
        _require_safe_id("task_id", self.task_id)
        _require_safe_id("domain", self.domain)
        if not 0.0 <= self.pre_import <= 1.0 or not 0.0 <= self.packaged <= 1.0:
            raise OllamaPackagingError("benchmark scores must be within [0, 1]")

    @property
    def loss(self) -> float:
        return max(0.0, self.pre_import - self.packaged)

    def descriptor(self) -> dict[str, object]:
        return {
            "critical": self.critical,
            "domain": self.domain,
            "loss": round(self.loss, 12),
            "packaged": self.packaged,
            "pre_import": self.pre_import,
            "task_id": self.task_id,
        }


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    disposition: PackageDisposition
    aggregate_loss: float
    critical_regressions: tuple[str, ...]

    def descriptor(self) -> dict[str, object]:
        return {
            "aggregate_loss": self.aggregate_loss,
            "critical_regressions": list(self.critical_regressions),
            "disposition": self.disposition.value,
        }


def assess_packaged_quality(
    scores: Iterable[BenchScore],
    *,
    max_aggregate_loss: float,
    max_critical_loss: float,
) -> QualityAssessment:
    rows = tuple(scores)
    if not rows:
        raise OllamaPackagingError("Ollama packaging comparison requires KodeBench evidence")
    if not 0.0 <= max_aggregate_loss <= 1.0 or not 0.0 <= max_critical_loss <= 1.0:
        raise OllamaPackagingError("quality thresholds must be within [0, 1]")
    critical = tuple(
        row.task_id for row in rows if row.critical and row.loss > max_critical_loss
    )
    aggregate_loss = round(sum(row.loss for row in rows) / len(rows), 12)
    if critical:
        disposition = PackageDisposition.REJECT_CRITICAL
    elif aggregate_loss > max_aggregate_loss:
        disposition = PackageDisposition.REJECT_QUALITY
    else:
        disposition = PackageDisposition.ACCEPT
    return QualityAssessment(disposition, aggregate_loss, critical)


def candidate_tag(binding: OllamaBinding) -> str:
    return f"kodepoia-candidate-{binding.candidate_id}:r15-13-{binding.artifact_sha256[:12]}"


def _artifact_reference(artifact: Path, modelfile: Path) -> str:
    relative = os.path.relpath(artifact.resolve(), modelfile.parent.resolve())
    return Path(relative).as_posix()


def verify_artifact(config: PackagingConfig) -> str:
    try:
        actual = digest_path(config.artifact_path)
        if actual != config.binding.artifact_sha256:
            raise OllamaPackagingError(
                "packaging artifact digest does not match immutable R15.11/R15.12 lineage"
            )
        if config.binding.artifact_kind is ArtifactKind.GGUF:
            inspect_gguf(config.artifact_path)
    except GgufConversionError as exc:
        raise OllamaPackagingError("packaging artifact failed R15.12 semantic validation") from exc
    return actual


def render_modelfile(config: PackagingConfig, modelfile_path: Path) -> str:
    verify_artifact(config)
    source_ref = _artifact_reference(config.artifact_path, modelfile_path)
    lines = [
        f"# Kodepoia R15.13 candidate {config.binding.candidate_id}",
        f"# base-sha256 {config.binding.base_digest}",
    ]
    if config.binding.artifact_kind is ArtifactKind.GGUF:
        lines.append(f"FROM {source_ref}")
    else:
        lines.append(f"FROM {config.binding.base_model}")
        lines.append(f"ADAPTER {source_ref}")
    lines.append(f'LICENSE """{config.license_text}"""')
    for key in sorted(config.parameters):
        lines.append(f"PARAMETER {key} {config.parameters[key]}")
    if config.template is not None:
        lines.append(f'TEMPLATE """{config.template}"""')
    if config.system is not None:
        lines.append(f'SYSTEM """{config.system}"""')
    return "\n".join(lines) + "\n"


def write_modelfile(config: PackagingConfig, modelfile_path: Path) -> tuple[str, str]:
    if modelfile_path.exists():
        raise OllamaPackagingError("immutable Modelfile destination already exists")
    text = render_modelfile(config, modelfile_path)
    modelfile_path.parent.mkdir(parents=True, exist_ok=True)
    modelfile_path.write_text(text, encoding="utf-8", newline="\n")
    return text, _sha256_text(text)


def build_create_argv(candidate: str, modelfile_path: Path) -> tuple[str, ...]:
    _require_model_name("candidate tag", candidate)
    return ("ollama", "create", candidate, "-f", str(modelfile_path))


def build_remove_argv(candidate: str) -> tuple[str, ...]:
    if not candidate.startswith("kodepoia-candidate-"):
        raise OllamaPackagingError("governed cleanup only removes R15.13 candidate tags")
    _require_model_name("candidate tag", candidate)
    return ("ollama", "rm", candidate)


def _argv_shape(argv: Sequence[str]) -> tuple[str, ...]:
    shape: list[str] = []
    for index, value in enumerate(argv):
        if index == 0:
            shape.append("tool")
        elif value in {"create", "rm", "-f"}:
            shape.append(value)
        else:
            shape.append("arg")
    return tuple(shape)


def _runtime_digest(client: Any, model: str) -> str:
    data = client._request("GET", "/api/tags")
    models = data.get("models", ())
    if not isinstance(models, list):
        raise OllamaPackagingError("Ollama tags response is invalid")
    for item in models:
        if not isinstance(item, Mapping):
            continue
        names = {str(item.get("name", "")), str(item.get("model", ""))}
        if model not in names:
            continue
        digest = item.get("digest")
        if not isinstance(digest, str):
            break
        return _require_digest("Ollama model digest", digest)
    raise OllamaPackagingError("Ollama model digest is unavailable")


def _require_expected_capabilities(show: Mapping[str, Any], expected: Sequence[str]) -> tuple[str, ...]:
    raw = show.get("capabilities", ())
    if not isinstance(raw, list):
        raise OllamaPackagingError("Ollama show capabilities must be a list")
    actual = tuple(sorted(str(value).lower() for value in raw))
    missing = sorted(set(cap.lower() for cap in expected) - set(actual))
    if missing:
        raise OllamaPackagingError(f"Ollama packaged candidate is missing capabilities: {','.join(missing)}")
    return actual


def _run_behavior_probes(client: Any, candidate: str, expected: Sequence[str]) -> dict[str, bool]:
    result = {"structured_output": False, "tool_call": False}
    structured = client.chat(
        candidate,
        [BrainMessage("user", "Return JSON with ok=true.")],
        response_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        },
        think=False,
        options={"temperature": 0, "seed": 1513},
    )
    try:
        payload = json.loads(structured.content)
    except json.JSONDecodeError as exc:
        raise OllamaPackagingError("structured-output probe returned invalid JSON") from exc
    if payload != {"ok": True}:
        raise OllamaPackagingError("structured-output probe did not preserve fixed contract")
    result["structured_output"] = True

    if "tools" in {cap.lower() for cap in expected}:
        tool = {
            "type": "function",
            "function": {
                "name": "kodepoia_probe",
                "description": "Return a fixed local probe marker.",
                "parameters": {
                    "type": "object",
                    "properties": {"marker": {"type": "string"}},
                    "required": ["marker"],
                },
            },
        }
        tool_response = client.chat(
            candidate,
            [BrainMessage("user", "Call kodepoia_probe with marker r15-13.")],
            tools=[tool],
            think=False,
            options={"temperature": 0, "seed": 1513},
        )
        if not tool_response.tool_calls:
            raise OllamaPackagingError("tool-call probe did not preserve claimed capability")
        result["tool_call"] = True
    return result


def _safe_show_details(show: Mapping[str, Any]) -> dict[str, object]:
    details = show.get("details", {})
    if not isinstance(details, Mapping):
        details = {}
    return {
        "capabilities": sorted({str(value).lower() for value in show.get("capabilities", [])}),
        "family": str(details.get("family", ""))[:128],
        "format": str(details.get("format", ""))[:64],
        "parameter_size": str(details.get("parameter_size", ""))[:64],
        "quantization_level": str(details.get("quantization_level", ""))[:64],
    }


def build_package_report(
    *,
    config: PackagingConfig,
    candidate: str,
    ollama_version: str,
    modelfile_digest: str,
    model_digest: str,
    show: Mapping[str, Any],
    behavior: Mapping[str, bool],
    bench_scores: Sequence[BenchScore],
    quality: QualityAssessment,
    argv_shape: Sequence[str],
    manual_state: str = "conditional_not_triggered",
) -> dict[str, object]:
    report: dict[str, object] = {
        "schema": OLLAMA_PACKAGE_SCHEMA,
        "schema_version": OLLAMA_PACKAGE_SCHEMA_VERSION,
        "binding": config.binding.descriptor(),
        "config": config.descriptor(),
        "candidate_tag": candidate,
        "ollama_version": _require_bounded_text("Ollama version", ollama_version, limit=128),
        "modelfile_digest": _require_digest("modelfile_digest", modelfile_digest),
        "model_digest": _require_digest("model_digest", model_digest),
        "show": _safe_show_details(show),
        "behavior": {
            "structured_output": bool(behavior.get("structured_output")),
            "tool_call": bool(behavior.get("tool_call")),
        },
        "benchmark": [row.descriptor() for row in bench_scores],
        "quality": quality.descriptor(),
        "create_argv_shape": list(argv_shape),
        "manual_state": manual_state,
        "provider_live_claim": False,
        "public_push": False,
        "secrets_exposed": False,
    }
    report["report_digest"] = _sha256_text(_canonical_json(report))
    return report


class OllamaPackager:
    def __init__(
        self,
        *,
        client: Any,
        runner: ToolRunner,
        active_model_tags: Iterable[str] = (),
    ) -> None:
        self.client = client
        self.runner = runner
        self.active_model_tags = frozenset(active_model_tags)
        require_loopback_origin(str(client.base_url))

    def _verify_adapter_base(self, config: PackagingConfig) -> None:
        if config.binding.artifact_kind is not ArtifactKind.SAFETENSORS_ADAPTER:
            return
        observed = _runtime_digest(self.client, config.binding.base_model)
        if observed != config.binding.base_digest:
            raise OllamaPackagingError("installed Ollama base digest drifted from training base")

    def _ensure_candidate_is_new(self, candidate: str) -> None:
        if candidate in self.active_model_tags:
            raise OllamaPackagingError("candidate tag collides with an active role tag")
        if candidate in set(self.client.list_models()):
            raise OllamaPackagingError("candidate tag already exists; silent replacement is forbidden")

    def cleanup_candidate(self, candidate: str) -> None:
        result = self.runner(build_remove_argv(candidate))
        if result.returncode != 0:
            raise OllamaPackagingError("governed Ollama candidate cleanup failed")

    def package_and_verify(
        self,
        *,
        config: PackagingConfig,
        modelfile_path: Path,
        bench_scores: Sequence[BenchScore],
    ) -> dict[str, object]:
        verify_artifact(config)
        self._verify_adapter_base(config)
        candidate = candidate_tag(config.binding)
        self._ensure_candidate_is_new(candidate)
        _, modelfile_digest = write_modelfile(config, modelfile_path)
        argv = build_create_argv(candidate, modelfile_path)
        result = self.runner(argv)
        if result.returncode != 0:
            raise OllamaPackagingError("ollama create failed")
        created = True
        try:
            show = self.client.show_model(candidate)
            if not isinstance(show, Mapping):
                raise OllamaPackagingError("Ollama show returned invalid details")
            _require_expected_capabilities(show, config.expected_capabilities)
            model_digest = _runtime_digest(self.client, candidate)
            behavior = _run_behavior_probes(self.client, candidate, config.expected_capabilities)
            quality = assess_packaged_quality(
                bench_scores,
                max_aggregate_loss=config.max_aggregate_loss,
                max_critical_loss=config.max_critical_loss,
            )
            if quality.disposition is not PackageDisposition.ACCEPT:
                raise OllamaPackagingError(
                    f"Ollama packaged candidate rejected by KodeBench: {quality.disposition.value}"
                )
            return build_package_report(
                config=config,
                candidate=candidate,
                ollama_version=str(self.client.version()),
                modelfile_digest=modelfile_digest,
                model_digest=model_digest,
                show=show,
                behavior=behavior,
                bench_scores=bench_scores,
                quality=quality,
                argv_shape=_argv_shape(argv),
            )
        except Exception:
            if created:
                self.cleanup_candidate(candidate)
            raise
