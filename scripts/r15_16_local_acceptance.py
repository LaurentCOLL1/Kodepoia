from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.tuning.contracts import (
    DTypeName,
    QuantizationMode,
    ResourceRequest,
    RuntimeRequest,
    SeedConfig,
    TrainingBackend,
)
from kodepoia.tuning.local_qualification import (
    LocalQualificationService,
    QualificationPolicy,
    save_report,
)

_MIB = 1024 * 1024


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the bounded, non-mutating R15.16 hardware-local qualification doctor."
    )
    parser.add_argument("--source-sha", required=True, help="exact 40-character repository HEAD required")
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--output",
        default="docs/roadmap/R15_16_LOCAL_ACCEPTANCE.json",
        help="JSON output path inside the project root",
    )
    parser.add_argument(
        "--backend",
        choices=[item.value for item in TrainingBackend],
        default=TrainingBackend.CPU.value,
    )
    parser.add_argument(
        "--dtype",
        choices=[item.value for item in DTypeName],
        default=DTypeName.FLOAT32.value,
    )
    parser.add_argument(
        "--quantization",
        choices=[item.value for item in QuantizationMode],
        default=QuantizationMode.NONE.value,
    )
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--data-seed", type=int, default=3407)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--disk-required-mb", type=int, default=0)
    parser.add_argument("--ram-required-mb", type=int, default=0)
    parser.add_argument("--vram-estimate-mb", type=int, default=0)
    parser.add_argument("--vram-reserve-mb", type=int, default=0)
    parser.add_argument("--vram-headroom-mb", type=int, default=0)
    parser.add_argument("--vram-total-limit-mb", type=int)
    parser.add_argument("--model-ref")
    parser.add_argument("--model-revision")
    parser.add_argument("--tokenizer-ref")
    parser.add_argument("--model-load-dry-run", action="store_true")
    parser.add_argument(
        "--training-required",
        action="store_true",
        help="block if the selected real training backend is unavailable",
    )
    parser.add_argument(
        "--ollama-required",
        action="store_true",
        help="block if local Ollama is unavailable",
    )
    return parser


def _mb(value: int | None) -> int | None:
    if value is None:
        return None
    return value * _MIB


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve(strict=False)
    request = RuntimeRequest(
        backend=TrainingBackend(args.backend),
        dtype=DTypeName(args.dtype),
        quantization=QuantizationMode(args.quantization),
        seeds=SeedConfig(seed=args.seed, data_seed=args.data_seed),
        resources=ResourceRequest(
            disk_required_bytes=_mb(args.disk_required_mb) or 0,
            ram_required_bytes=_mb(args.ram_required_mb) or 0,
            vram_estimate_bytes=_mb(args.vram_estimate_mb) or 0,
            vram_reserve_bytes=_mb(args.vram_reserve_mb) or 0,
            vram_headroom_bytes=_mb(args.vram_headroom_mb) or 0,
            vram_total_limit_bytes=_mb(args.vram_total_limit_mb),
        ),
        timeout_seconds=args.timeout_seconds,
        model_ref=args.model_ref,
        model_revision=args.model_revision,
        tokenizer_ref=args.tokenizer_ref,
        model_load_dry_run=args.model_load_dry_run,
    )
    report = LocalQualificationService(root).doctor(
        expected_source_sha=args.source_sha,
        runtime_request=request,
        policy=QualificationPolicy(
            training_required=args.training_required,
            ollama_required=args.ollama_required,
        ),
    )
    save_report(root, Path(args.output), report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
