from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from kodepoia.brain.base import BrainResponse
from kodepoia.tuning.ollama_packaging import (
    OLLAMA_PACKAGE_SCHEMA,
    ArtifactKind,
    BenchScore,
    OllamaBinding,
    OllamaPackager,
    OllamaPackagingError,
    PackageDisposition,
    PackagingConfig,
    ToolRunResult,
    assess_packaged_quality,
    build_create_argv,
    build_remove_argv,
    candidate_tag,
    render_modelfile,
    require_loopback_origin,
)


def _write_gguf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sIQQ", b"GGUF", 3, 2, 3) + b"r15-13-fixture")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(artifact: Path, *, kind: ArtifactKind = ArtifactKind.GGUF) -> OllamaBinding:
    common: dict[str, Any] = {
        "candidate_id": "candidate-13",
        "artifact_kind": kind,
        "artifact_sha256": _digest(artifact) if artifact.is_file() else _directory_digest(artifact),
        "base_model": "fixture-base:immutable",
        "base_digest": "b" * 64,
        "export_manifest_digest": "1" * 64,
        "evaluation_digest": "2" * 64,
        "gguf_report_digest": "3" * 64,
        "architecture": "fixture",
    }
    if kind is ArtifactKind.SAFETENSORS_ADAPTER:
        common.update(
            trained_base_model="fixture-base:immutable",
            trained_base_digest="b" * 64,
            direct_adapter_authorized=True,
        )
    return OllamaBinding(**common)


def _directory_digest(path: Path) -> str:
    from kodepoia.tuning.gguf import digest_path

    return digest_path(path)


def _config(artifact: Path, *, kind: ArtifactKind = ArtifactKind.GGUF) -> PackagingConfig:
    return PackagingConfig(
        binding=_binding(artifact, kind=kind),
        artifact_path=artifact,
        license_text="Apache-2.0 fixture",
        parameters={"num_ctx": 4096, "seed": 1513, "temperature": 0},
        template="{{ .Prompt }}{{ .Response }}",
        expected_capabilities=("completion", "tools"),
        max_aggregate_loss=0.03,
        max_critical_loss=0.01,
    )


def _scores() -> tuple[BenchScore, ...]:
    return (
        BenchScore("code-1", "code", pre_import=0.91, packaged=0.905, critical=True),
        BenchScore("reason-1", "reasoning", pre_import=0.88, packaged=0.87),
    )


class FakeOllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url
        self.models: dict[str, str] = {"fixture-base:immutable": "b" * 64}
        self.version_value = "0.13.0-fixture"

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert method == "GET"
        assert path == "/api/tags"
        assert payload is None
        return {
            "models": [
                {"name": name, "model": name, "digest": digest}
                for name, digest in sorted(self.models.items())
            ]
        }

    def list_models(self) -> list[str]:
        return sorted(self.models)

    def show_model(self, model: str) -> dict[str, Any]:
        if model not in self.models:
            raise RuntimeError("missing fake model")
        return {
            "capabilities": ["completion", "tools"],
            "details": {
                "family": "fixture",
                "format": "gguf",
                "parameter_size": "tiny",
                "quantization_level": "Q4_K_M",
            },
            "license": "Apache-2.0 fixture",
        }

    def version(self) -> str:
        return self.version_value

    def chat(self, model: str, messages: list[Any], **kwargs: Any) -> BrainResponse:
        assert model in self.models
        assert messages
        if kwargs.get("tools"):
            return BrainResponse(
                content="",
                model=model,
                tool_calls=(
                    {
                        "function": {
                            "name": "kodepoia_probe",
                            "arguments": {"marker": "r15-13"},
                        }
                    },
                ),
            )
        if kwargs.get("response_schema"):
            return BrainResponse(content='{"ok": true}', model=model)
        return BrainResponse(content="ok", model=model)


class FakeRunner:
    def __init__(self, client: FakeOllamaClient, *, create_returncode: int = 0) -> None:
        self.client = client
        self.create_returncode = create_returncode
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv: tuple[str, ...]) -> ToolRunResult:
        self.calls.append(argv)
        if argv[1] == "create":
            if self.create_returncode:
                return ToolRunResult(returncode=self.create_returncode, stderr="fixture failure")
            self.client.models[argv[2]] = "a" * 64
            return ToolRunResult(returncode=0, stdout="success")
        if argv[1] == "rm":
            self.client.models.pop(argv[2], None)
            return ToolRunResult(returncode=0)
        raise AssertionError(f"unexpected fake argv: {argv}")


def test_loopback_policy_matches_existing_explicit_port_boundary() -> None:
    assert require_loopback_origin("http://127.0.0.1:11434") == "http://127.0.0.1:11434"
    assert require_loopback_origin("https://localhost:11434/") == "https://localhost:11434"

    for bad in (
        "http://example.com:11434",
        "http://127.0.0.1",
        "http://user:pass@127.0.0.1:11434",
        "http://127.0.0.1:11434/api",
        "http://127.0.0.1:11434?x=1",
    ):
        with pytest.raises(OllamaPackagingError, match="loopback"):
            require_loopback_origin(bad)


def test_candidate_tag_is_namespaced_and_create_remove_argv_are_structured(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "model.gguf"
    _write_gguf(artifact)
    binding = _binding(artifact)
    tag = candidate_tag(binding)
    modelfile = tmp_path / "package" / "Modelfile"

    assert tag == f"kodepoia-candidate-candidate-13:r15-13-{_digest(artifact)[:12]}"
    assert build_create_argv(tag, modelfile) == ("ollama", "create", tag, "-f", str(modelfile))
    assert build_remove_argv(tag) == ("ollama", "rm", tag)
    with pytest.raises(OllamaPackagingError, match="candidate tags"):
        build_remove_argv("production:latest")


def test_modelfile_is_deterministic_and_binds_gguf_license_parameters(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "model.gguf"
    _write_gguf(artifact)
    config = _config(artifact)
    modelfile = tmp_path / "package" / "Modelfile"

    first = render_modelfile(config, modelfile)
    second = render_modelfile(config, modelfile)
    assert first == second
    assert "FROM ../artifacts/model.gguf" in first
    assert "ADAPTER " not in first
    assert 'LICENSE """Apache-2.0 fixture"""' in first
    assert "PARAMETER num_ctx 4096" in first
    assert "PARAMETER temperature 0" in first
    assert "# base-sha256 " + "b" * 64 in first


def test_wrong_adapter_base_is_rejected_before_create(tmp_path: Path) -> None:
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "adapter_model.safetensors").write_bytes(b"adapter")
    config = _config(adapter, kind=ArtifactKind.SAFETENSORS_ADAPTER)
    client = FakeOllamaClient()
    client.models["fixture-base:immutable"] = "c" * 64
    runner = FakeRunner(client)
    packager = OllamaPackager(client=client, runner=runner)

    with pytest.raises(OllamaPackagingError, match="base digest drifted"):
        packager.package_and_verify(
            config=config,
            modelfile_path=tmp_path / "package" / "Modelfile",
            bench_scores=_scores(),
        )
    assert runner.calls == []


def test_adapter_binding_constructor_rejects_training_base_mismatch(tmp_path: Path) -> None:
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "adapter_model.safetensors").write_bytes(b"adapter")
    digest = _directory_digest(adapter)

    with pytest.raises(OllamaPackagingError, match="adapter/base identity mismatch"):
        OllamaBinding(
            candidate_id="candidate-13",
            artifact_kind=ArtifactKind.SAFETENSORS_ADAPTER,
            artifact_sha256=digest,
            base_model="fixture-base:immutable",
            base_digest="b" * 64,
            export_manifest_digest="1" * 64,
            evaluation_digest="2" * 64,
            gguf_report_digest="3" * 64,
            architecture="fixture",
            trained_base_model="other-base:immutable",
            trained_base_digest="b" * 64,
            direct_adapter_authorized=True,
        )


def test_malformed_or_tampered_gguf_fails_before_ollama_create(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "model.gguf"
    _write_gguf(artifact)
    config = _config(artifact)
    artifact.write_bytes(b"not-gguf")
    client = FakeOllamaClient()
    runner = FakeRunner(client)
    packager = OllamaPackager(client=client, runner=runner)

    with pytest.raises(OllamaPackagingError, match="immutable R15.11/R15.12 lineage"):
        packager.package_and_verify(
            config=config,
            modelfile_path=tmp_path / "package" / "Modelfile",
            bench_scores=_scores(),
        )
    assert runner.calls == []


def test_create_show_digest_structured_tool_and_benchmark_lifecycle(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "model.gguf"
    _write_gguf(artifact)
    config = _config(artifact)
    client = FakeOllamaClient()
    runner = FakeRunner(client)
    packager = OllamaPackager(client=client, runner=runner, active_model_tags=("core:active",))

    report = packager.package_and_verify(
        config=config,
        modelfile_path=tmp_path / "package" / "Modelfile",
        bench_scores=_scores(),
    )

    assert report["schema"] == OLLAMA_PACKAGE_SCHEMA
    assert report["model_digest"] == "a" * 64
    assert report["ollama_version"] == client.version_value
    assert report["behavior"] == {"structured_output": True, "tool_call": True}
    assert report["quality"]["disposition"] == "accept"
    assert report["manual_state"] == "conditional_not_triggered"
    assert report["provider_live_claim"] is False
    assert report["public_push"] is False
    assert report["secrets_exposed"] is False
    assert runner.calls == [
        (
            "ollama",
            "create",
            candidate_tag(config.binding),
            "-f",
            str(tmp_path / "package" / "Modelfile"),
        )
    ]
    assert all("push" not in call for call in runner.calls)


def test_existing_or_active_candidate_never_gets_silently_replaced(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "model.gguf"
    _write_gguf(artifact)
    config = _config(artifact)
    candidate = candidate_tag(config.binding)

    client = FakeOllamaClient()
    runner = FakeRunner(client)
    with pytest.raises(OllamaPackagingError, match="active role"):
        OllamaPackager(
            client=client,
            runner=runner,
            active_model_tags=(candidate,),
        ).package_and_verify(
            config=config,
            modelfile_path=tmp_path / "active" / "Modelfile",
            bench_scores=_scores(),
        )

    client.models[candidate] = "d" * 64
    with pytest.raises(OllamaPackagingError, match="silent replacement"):
        OllamaPackager(client=client, runner=runner).package_and_verify(
            config=config,
            modelfile_path=tmp_path / "installed" / "Modelfile",
            bench_scores=_scores(),
        )
    assert runner.calls == []


def test_quality_veto_cleans_up_created_candidate(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "model.gguf"
    _write_gguf(artifact)
    config = _config(artifact)
    client = FakeOllamaClient()
    runner = FakeRunner(client)
    candidate = candidate_tag(config.binding)
    bad_scores = (
        BenchScore("security-1", "security", pre_import=0.95, packaged=0.80, critical=True),
    )

    with pytest.raises(OllamaPackagingError, match="reject_critical"):
        OllamaPackager(client=client, runner=runner).package_and_verify(
            config=config,
            modelfile_path=tmp_path / "package" / "Modelfile",
            bench_scores=bad_scores,
        )
    assert runner.calls[0][1] == "create"
    assert runner.calls[1] == ("ollama", "rm", candidate)
    assert candidate not in client.models


def test_quality_assessment_preserves_critical_and_aggregate_vetoes() -> None:
    accepted = assess_packaged_quality(_scores(), max_aggregate_loss=0.03, max_critical_loss=0.01)
    assert accepted.disposition is PackageDisposition.ACCEPT

    critical = assess_packaged_quality(
        (BenchScore("security-1", "security", 0.95, 0.90, True),),
        max_aggregate_loss=0.20,
        max_critical_loss=0.01,
    )
    assert critical.disposition is PackageDisposition.REJECT_CRITICAL

    aggregate = assess_packaged_quality(
        (
            BenchScore("code-1", "code", 0.90, 0.80),
            BenchScore("reason-1", "reasoning", 0.90, 0.80),
        ),
        max_aggregate_loss=0.05,
        max_critical_loss=0.01,
    )
    assert aggregate.disposition is PackageDisposition.REJECT_QUALITY


def test_report_is_deterministic_and_schema_valid(tmp_path: Path) -> None:
    def build_once(root: Path) -> dict[str, Any]:
        root.mkdir()
        local_artifact = root / "artifacts" / "model.gguf"
        _write_gguf(local_artifact)
        config = _config(local_artifact)
        client = FakeOllamaClient()
        runner = FakeRunner(client)
        return OllamaPackager(client=client, runner=runner).package_and_verify(
            config=config,
            modelfile_path=root / "package" / "Modelfile",
            bench_scores=_scores(),
        )

    first = build_once(tmp_path / "one")
    second = build_once(tmp_path / "two")
    assert first == second

    schema_path = Path(__file__).parents[1] / "schemas" / "r15-13-ollama-package.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(first)
