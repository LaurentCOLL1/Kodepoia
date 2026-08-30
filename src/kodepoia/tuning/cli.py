from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import (
    DTypeName,
    QuantizationMode,
    ResourceRequest,
    RuntimeRequest,
    SeedConfig,
    TrainingBackend,
)
from .runtime import TrainingRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m kodepoia.tuning")
    parser.add_argument("--backend", choices=[item.value for item in TrainingBackend], default="cpu")
    parser.add_argument("--dtype", choices=[item.value for item in DTypeName], default="float32")
    parser.add_argument(
        "--quantization",
        choices=[item.value for item in QuantizationMode],
        default="none",
    )
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--data-seed", type=int, default=3407)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--disk-required-bytes", type=int, default=0)
    parser.add_argument("--ram-required-bytes", type=int, default=0)
    parser.add_argument("--vram-estimate-bytes", type=int, default=0)
    parser.add_argument("--vram-reserve-bytes", type=int, default=0)
    parser.add_argument("--vram-headroom-bytes", type=int, default=0)
    parser.add_argument("--vram-total-limit-bytes", type=int)
    parser.add_argument("--model")
    parser.add_argument("--model-revision")
    parser.add_argument("--tokenizer")
    parser.add_argument("--load-model", action="store_true")
    parser.add_argument(
        "--output",
        default=".kodepoia/tuning/r15_8_capability.json",
        help="project-relative redacted capability report",
    )
    return parser


def _inside(root: Path, value: str) -> Path:
    path = (root / value).resolve(strict=False)
    if path != root and root not in path.parents:
        raise SystemExit("R15.8 output path must remain inside the current project root")
    return path


def main() -> int:
    args = build_parser().parse_args()
    root = Path.cwd().resolve(strict=False)
    request = RuntimeRequest(
        backend=TrainingBackend(args.backend),
        dtype=DTypeName(args.dtype),
        quantization=QuantizationMode(args.quantization),
        seeds=SeedConfig(args.seed, args.data_seed),
        resources=ResourceRequest(
            disk_required_bytes=args.disk_required_bytes,
            ram_required_bytes=args.ram_required_bytes,
            vram_estimate_bytes=args.vram_estimate_bytes,
            vram_reserve_bytes=args.vram_reserve_bytes,
            vram_headroom_bytes=args.vram_headroom_bytes,
            vram_total_limit_bytes=args.vram_total_limit_bytes,
        ),
        timeout_seconds=args.timeout,
        model_ref=args.model,
        model_revision=args.model_revision,
        tokenizer_ref=args.tokenizer,
        model_load_dry_run=args.load_model,
    )
    report = TrainingRuntime(root).probe(request)
    output = _inside(root, args.output)
    report.save(output)
    print(
        json.dumps(
            {
                "backend_capability": report.backend_capability.value,
                "disposition": report.disposition.value,
                "output": str(output.relative_to(root)),
                "report_digest": report.digest,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report.disposition.value == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
