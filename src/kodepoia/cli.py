from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
from urllib.parse import urlparse

from kodepoia.bench.baseline import BaselineBench, BenchmarkRole
from kodepoia.brain.ollama import OllamaClient
from kodepoia.intelligence.research.media import (
    AcceptanceStatus,
    LocalMediaAcceptance,
    MediaDoctor,
    build_governed_media_runner,
    write_json_report,
)
from kodepoia.project.dna import ApprovalPolicy, Dimension, Platform, ProjectType
from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState


PRESELECTION_REPEATS = 4
ACCEPTANCE_REPEATS = 5


def _project_init(args: argparse.Namespace) -> int:
    state = ProjectWizardState(
        name=args.name,
        project_type=ProjectType(args.type),
        platforms=[Platform(item) for item in args.platform],
        engine=args.engine,
        engine_version=args.engine_version,
        dimension=Dimension(args.dimension) if args.dimension else None,
        inputs=args.input,
        genres=args.genre,
        graphics_style=args.graphics_style,
        download_policy=ApprovalPolicy(args.download_policy),
        install_policy=ApprovalPolicy(args.install_policy),
        tools={"ollama": True, **{name: True for name in args.tool}},
    )
    result = ProjectInitializer().initialize(Path(args.directory), state.build())
    print(result.dna_path)
    return 0


def _ollama_status(args: argparse.Namespace) -> int:
    client = OllamaClient(args.url)
    print(
        json.dumps(
            {
                "version": client.version(),
                "models": client.list_models(),
                "running": client.running_models(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _benchmark_metadata(
    client: OllamaClient,
    candidates: list[str],
    phase: str,
    *,
    role: BenchmarkRole | None = None,
    repeats: int = 1,
    num_predict: int = BaselineBench.FAST_NUM_PREDICT,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "phase": phase,
        "ollama_version": client.version(),
        "candidates": candidates,
        "installed_models": client.list_models(),
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "repeats": repeats,
        "generation_controls": {
            "seed_base": 101,
            "temperature": 0.0,
            "num_predict": num_predict,
        },
    }
    if role is not None:
        metadata["benchmark_role"] = role.value
    return metadata


def _validate_installed_candidates(client: OllamaClient, candidates: list[str]) -> None:
    installed = set(client.list_models())
    missing = [model for model in candidates if model not in installed]
    if missing:
        raise SystemExit(f"Requested Ollama model(s) are not installed: {', '.join(missing)}")


def _require_loopback_url(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit(
            "R3 hardware-local acceptance only accepts a loopback Ollama URL "
            "(127.0.0.1, localhost or ::1)"
        )


def _validate_repeats(repeats: int, *, acceptance: bool = False) -> None:
    minimum = 4 if acceptance else 1
    if not minimum <= repeats <= 8:
        if acceptance:
            raise SystemExit("R3 local acceptance requires between 4 and 8 repetitions")
        raise SystemExit("Benchmark repetitions must be between 1 and 8")


def _bench_models(args: argparse.Namespace) -> int:
    _validate_repeats(args.repeats)
    client = OllamaClient(args.url)
    candidates = list(dict.fromkeys(args.model))
    _validate_installed_candidates(client, candidates)
    role = BenchmarkRole(args.role)
    num_predict = BaselineBench.num_predict_for_role(role)
    results = BaselineBench(client).run(
        candidates,
        role=role,
        repeats=args.repeats,
        num_predict=num_predict,
    )
    output = Path(args.output)
    BaselineBench.save(
        results,
        output,
        metadata=_benchmark_metadata(
            client,
            candidates,
            "baseline",
            role=role,
            repeats=args.repeats,
            num_predict=num_predict,
        ),
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "role": role.value,
                "repeats": args.repeats,
                "num_predict": num_predict,
                "summary": BaselineBench.summarize(results),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _r3_accept(args: argparse.Namespace) -> int:
    _require_loopback_url(args.url)
    _validate_repeats(args.repeats, acceptance=True)
    candidates = list(dict.fromkeys(args.model))
    if not 2 <= len(candidates) <= 3:
        raise SystemExit("R3 local acceptance requires exactly two or three distinct models")
    client = OllamaClient(args.url)
    _validate_installed_candidates(client, candidates)
    acceptance_role = BenchmarkRole.CORE
    num_predict = BaselineBench.num_predict_for_role(acceptance_role)
    results = BaselineBench(client).run(
        candidates,
        role=acceptance_role,
        repeats=args.repeats,
        num_predict=num_predict,
    )
    output = Path(args.output)
    metadata = _benchmark_metadata(
        client,
        candidates,
        "R3-local-acceptance",
        role=acceptance_role,
        repeats=args.repeats,
        num_predict=num_predict,
    )
    metadata["acceptance_completed"] = True
    metadata["candidate_count"] = len(candidates)
    metadata["ollama_url"] = args.url
    metadata["loopback_verified"] = True
    metadata["acceptance_profile"] = "full-capability-thinking-aware"
    BaselineBench.save(results, output, metadata=metadata)
    payload = {
        "R3_local_acceptance": "COMPLETED",
        "output": str(output),
        "candidates": candidates,
        "repeats": args.repeats,
        "num_predict": num_predict,
        "summary": BaselineBench.summarize(results),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _research_media_doctor(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve(strict=False)
    runner = build_governed_media_runner(root)
    report = MediaDoctor(root, runner).run()
    payload = report.to_dict()
    destination = write_json_report(root, args.json, payload)
    print(json.dumps({"output": str(destination), **payload}, ensure_ascii=False, indent=2))
    return 0 if report.ready else 2


def _research_media_acceptance(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve(strict=False)
    runner = build_governed_media_runner(root)
    doctor = MediaDoctor(root, runner)
    report = LocalMediaAcceptance(root, runner, doctor).run(args.fixture)
    payload = report.to_dict()
    destination = write_json_report(root, args.output, payload)
    print(json.dumps({"output": str(destination), **payload}, ensure_ascii=False, indent=2))
    return 0 if report.status is AcceptanceStatus.PASS else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kodepoia")
    commands = parser.add_subparsers(dest="command", required=True)

    project = commands.add_parser("project-init")
    project.add_argument("name")
    project.add_argument("--directory", default=".")
    project.add_argument("--type", choices=[item.value for item in ProjectType], default="game")
    project.add_argument("--platform", action="append", choices=[item.value for item in Platform], default=None)
    project.add_argument("--engine", default="Godot")
    project.add_argument("--engine-version", default="4.7")
    project.add_argument("--dimension", choices=[item.value for item in Dimension], default="3d")
    project.add_argument("--input", action="append", default=None)
    project.add_argument("--genre", action="append", default=[])
    project.add_argument("--graphics-style")
    project.add_argument("--tool", action="append", default=[])
    project.add_argument(
        "--download-policy",
        choices=[item.value for item in ApprovalPolicy],
        default=ApprovalPolicy.ASK.value,
    )
    project.add_argument(
        "--install-policy",
        choices=[item.value for item in ApprovalPolicy],
        default=ApprovalPolicy.ASK.value,
    )
    project.set_defaults(func=_project_init)

    ollama = commands.add_parser("ollama-status")
    ollama.add_argument("--url", default="http://127.0.0.1:11434")
    ollama.set_defaults(func=_ollama_status)

    bench = commands.add_parser("bench-models")
    bench.add_argument("--model", action="append", required=True)
    bench.add_argument(
        "--role",
        choices=[item.value for item in BenchmarkRole],
        default=BenchmarkRole.BASELINE.value,
        help="FAST disables thinking; CORE/CODER enable supported thinking with a larger output budget",
    )
    bench.add_argument(
        "--repeats",
        type=int,
        default=PRESELECTION_REPEATS,
        help="repeat each model benchmark 1-8 times (official preselection default: 4)",
    )
    bench.add_argument("--url", default="http://127.0.0.1:11434")
    bench.add_argument("--output", default=".kodepoia/benchmarks/r3-baseline.json")
    bench.set_defaults(func=_bench_models)

    r3 = commands.add_parser("r3-accept")
    r3.add_argument("--model", action="append", required=True)
    r3.add_argument(
        "--repeats",
        type=int,
        default=ACCEPTANCE_REPEATS,
        help="repeat each finalist 4-8 times (official acceptance default: 5)",
    )
    r3.add_argument("--url", default="http://127.0.0.1:11434")
    r3.add_argument("--output", default=".kodepoia/benchmarks/r3-local-acceptance.json")
    r3.set_defaults(func=_r3_accept)

    media_doctor = commands.add_parser("research-media-doctor")
    media_doctor.add_argument(
        "--json",
        default=".kodepoia/research/r7_7_media_doctor.json",
        help="project-relative output path for the redacted capability report",
    )
    media_doctor.set_defaults(func=_research_media_doctor)

    media_accept = commands.add_parser("research-media-acceptance")
    media_accept.add_argument("--fixture", required=True)
    media_accept.add_argument(
        "--output",
        default=".kodepoia/research/r7_7_local_acceptance.json",
        help="project-relative output path for the local acceptance report",
    )
    media_accept.set_defaults(func=_research_media_acceptance)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if getattr(args, "platform", None) is None:
        args.platform = ["windows"]
    if getattr(args, "input", None) is None:
        args.input = ["keyboard", "mouse"]
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
