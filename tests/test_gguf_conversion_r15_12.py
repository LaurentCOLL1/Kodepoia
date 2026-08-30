from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.tuning.gguf import (
    GGUF_SCHEMA,
    ConversionBinding,
    ConversionPlan,
    DomainScore,
    GgufConversionError,
    GgufToolchain,
    QualityDisposition,
    QuantizationTarget,
    SourceKind,
    ToolRunResult,
    assess_quantization_quality,
    build_quality_matrix_report,
    build_quantize_argv,
    digest_path,
    inspect_gguf,
    run_high_precision_conversion,
    run_quantization,
    verify_source,
)


def _write_gguf(path: Path, *, version: int = 3, tensors: int = 2, metadata: int = 3) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sIQQ", b"GGUF", version, tensors, metadata) + b"fixture-payload")


def _toolchain(tmp_path: Path) -> GgufToolchain:
    converter = tmp_path / "convert_hf_to_gguf.py"
    quantizer = tmp_path / "llama-quantize"
    converter.write_text("# fixture converter\n", encoding="utf-8")
    quantizer.write_text("fixture quantizer\n", encoding="utf-8")
    return GgufToolchain(converter=converter, quantizer=quantizer, revision="llama.cpp-fixture-r1")


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir(parents=True)
    (source / "config.json").write_text('{"model_type":"fixture"}', encoding="utf-8")
    (source / "model.safetensors").write_bytes(b"high-precision-fixture")
    return source


def _binding(source: Path) -> ConversionBinding:
    return ConversionBinding(
        candidate_id="candidate-12",
        architecture="fixture",
        source_digest=digest_path(source),
        export_manifest_digest="1" * 64,
        evaluation_digest="2" * 64,
        source_kind=SourceKind.HF_DIRECTORY,
        source_precision="F16",
    )


def _plan(binding: ConversionBinding) -> ConversionPlan:
    return ConversionPlan(
        binding=binding,
        targets=(
            QuantizationTarget("Q4_K_M", max_aggregate_loss=0.05, max_critical_loss=0.01),
            QuantizationTarget("Q8_0", max_aggregate_loss=0.02, max_critical_loss=0.005),
        ),
        max_artifact_bytes=1024 * 1024,
    )


def test_gguf_header_validation_rejects_malformed_and_budget_excess(tmp_path: Path) -> None:
    valid = tmp_path / "valid.gguf"
    _write_gguf(valid)
    header = inspect_gguf(valid, max_size_bytes=1024)
    assert header.version == 3
    assert header.tensor_count == 2
    assert header.metadata_kv_count == 3
    assert header.sha256 == hashlib.sha256(valid.read_bytes()).hexdigest()

    bad_magic = tmp_path / "bad-magic.gguf"
    bad_magic.write_bytes(struct.pack("<4sIQQ", b"NOPE", 3, 1, 1))
    with pytest.raises(GgufConversionError, match="magic"):
        inspect_gguf(bad_magic)

    unsupported = tmp_path / "unsupported.gguf"
    _write_gguf(unsupported, version=99)
    with pytest.raises(GgufConversionError, match="version"):
        inspect_gguf(unsupported)

    with pytest.raises(GgufConversionError, match="disk budget"):
        inspect_gguf(valid, max_size_bytes=24)


def test_source_lineage_is_exact_and_requantization_fails_closed(tmp_path: Path) -> None:
    source = _source(tmp_path)
    binding = _binding(source)
    assert verify_source(binding, source) == binding.source_digest

    (source / "config.json").write_text('{"model_type":"changed"}', encoding="utf-8")
    with pytest.raises(GgufConversionError, match="immutable export lineage"):
        verify_source(binding, source)

    gguf = tmp_path / "already-quantized.gguf"
    _write_gguf(gguf)
    quantized_binding = ConversionBinding(
        candidate_id="quantized-source",
        architecture="fixture",
        source_digest=digest_path(gguf),
        export_manifest_digest="3" * 64,
        evaluation_digest="4" * 64,
        source_kind=SourceKind.GGUF,
        source_precision="Q4_K_M",
        source_quantization="Q4_K_M",
    )
    with pytest.raises(GgufConversionError, match="refuses requantization"):
        verify_source(quantized_binding, gguf)


def test_conversion_and_quantization_use_structured_runner_and_validate_outputs(tmp_path: Path) -> None:
    source = _source(tmp_path)
    binding = _binding(source)
    plan = _plan(binding)
    toolchain = _toolchain(tmp_path)
    observed: list[tuple[str, ...]] = []

    def runner(argv: tuple[str, ...]) -> ToolRunResult:
        observed.append(argv)
        output = Path(argv[argv.index("--outfile") + 1]) if "--outfile" in argv else Path(argv[-2])
        _write_gguf(output)
        return ToolRunResult(returncode=0)

    high_path = tmp_path / "artifacts" / "candidate-f16.gguf"
    high = run_high_precision_conversion(
        toolchain=toolchain,
        plan=plan,
        source=source,
        output=high_path,
        runner=runner,
    )
    assert high.operation == "convert"
    assert high.quant_type == "F16"
    assert high.argv_shape.count("--outfile") == 1

    target = plan.targets[0]
    quant_path = tmp_path / "artifacts" / "candidate-q4.gguf"
    quant = run_quantization(
        toolchain=toolchain,
        plan=plan,
        source=high_path,
        output=quant_path,
        target=target,
        runner=runner,
    )
    assert quant.operation == "quantize"
    assert quant.quant_type == "Q4_K_M"
    assert quant.input_sha256 == high.output.sha256
    assert len(observed) == 2
    assert all(isinstance(argv, tuple) for argv in observed)


def test_tool_failures_and_missing_capabilities_fail_closed(tmp_path: Path) -> None:
    source = _source(tmp_path)
    binding = _binding(source)
    plan = _plan(binding)
    toolchain = _toolchain(tmp_path)

    with pytest.raises(GgufConversionError, match="tool failed"):
        run_high_precision_conversion(
            toolchain=toolchain,
            plan=plan,
            source=source,
            output=tmp_path / "failed.gguf",
            runner=lambda _: ToolRunResult(returncode=2),
        )

    toolchain.converter.unlink()
    with pytest.raises(GgufConversionError, match="capability is unavailable"):
        run_high_precision_conversion(
            toolchain=toolchain,
            plan=plan,
            source=source,
            output=tmp_path / "missing.gguf",
            runner=lambda _: ToolRunResult(returncode=0),
        )


def test_importance_matrix_requires_exact_digest(tmp_path: Path) -> None:
    toolchain = _toolchain(tmp_path)
    source = tmp_path / "source.gguf"
    output = tmp_path / "output.gguf"
    matrix = tmp_path / "imatrix.dat"
    _write_gguf(source)
    matrix.write_bytes(b"importance-fixture")
    target = QuantizationTarget(
        "Q4_K_M",
        max_aggregate_loss=0.05,
        importance_matrix_digest="f" * 64,
    )
    with pytest.raises(GgufConversionError, match="matrix digest mismatch"):
        build_quantize_argv(toolchain, source, output, target, importance_matrix=matrix)


def test_quality_matrix_preserves_critical_veto_and_aggregate_threshold() -> None:
    target = QuantizationTarget("Q4_K_M", max_aggregate_loss=0.04, max_critical_loss=0.01)
    accepted = assess_quantization_quality(
        (
            DomainScore("code", baseline=0.9, candidate=0.895, critical=True),
            DomainScore("writing", baseline=0.8, candidate=0.78),
        ),
        target,
    )
    assert accepted.disposition is QualityDisposition.ACCEPT

    critical = assess_quantization_quality(
        (DomainScore("security", baseline=0.95, candidate=0.90, critical=True),),
        target,
    )
    assert critical.disposition is QualityDisposition.REJECT_CRITICAL
    assert critical.critical_regressions == ("security",)

    aggregate = assess_quantization_quality(
        (
            DomainScore("code", baseline=0.9, candidate=0.84),
            DomainScore("writing", baseline=0.8, candidate=0.74),
        ),
        target,
    )
    assert aggregate.disposition is QualityDisposition.REJECT_QUALITY


def test_quality_matrix_report_is_deterministic_and_schema_valid(tmp_path: Path) -> None:
    source = _source(tmp_path)
    plan = _plan(_binding(source))
    toolchain = _toolchain(tmp_path)

    def runner(argv: tuple[str, ...]) -> ToolRunResult:
        output = Path(argv[argv.index("--outfile") + 1]) if "--outfile" in argv else Path(argv[-2])
        _write_gguf(output)
        return ToolRunResult(returncode=0)

    high_path = tmp_path / "high.gguf"
    high = run_high_precision_conversion(
        toolchain=toolchain,
        plan=plan,
        source=source,
        output=high_path,
        runner=runner,
    )
    quantized = {}
    for target in plan.targets:
        output = tmp_path / f"{target.quant_type}.gguf"
        artifact = run_quantization(
            toolchain=toolchain,
            plan=plan,
            source=high_path,
            output=output,
            target=target,
            runner=runner,
        )
        quality = assess_quantization_quality(
            (DomainScore("code", baseline=0.9, candidate=0.895, critical=True),),
            target,
        )
        quantized[target.quant_type] = (artifact, quality)

    report = build_quality_matrix_report(plan=plan, high_precision=high, quantized=quantized)
    second = build_quality_matrix_report(plan=plan, high_precision=high, quantized=quantized)
    assert report == second
    assert report["schema"] == GGUF_SCHEMA

    schema_path = Path(__file__).parents[1] / "schemas" / "r15-12-gguf-conversion.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report)
