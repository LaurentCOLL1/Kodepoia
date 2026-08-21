from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path

from kodepoia.bench.baseline import BaselineBench
from kodepoia.brain.ollama import OllamaClient
from kodepoia.project.dna import ApprovalPolicy, Dimension, Platform, ProjectType
from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState


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


def _benchmark_metadata(client: OllamaClient, candidates: list[str], phase: str) -> dict[str, object]:
    return {
        "phase": phase,
        "ollama_version": client.version(),
        "candidates": candidates,
        "installed_models": client.list_models(),
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def _validate_installed_candidates(client: OllamaClient, candidates: list[str]) -> None:
    installed = set(client.list_models())
    missing = [model for model in candidates if model not in installed]
    if missing:
        raise SystemExit(f"Requested Ollama model(s) are not installed: {', '.join(missing)}")


def _bench_models(args: argparse.Namespace) -> int:
    client = OllamaClient(args.url)
    _validate_installed_candidates(client, args.model)
    results = BaselineBench(client).run(args.model)
    output = Path(args.output)
    BaselineBench.save(
        results,
        output,
        metadata=_benchmark_metadata(client, args.model, "baseline"),
    )
    print(
        json.dumps(
            {"output": str(output), "summary": BaselineBench.summarize(results)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _r3_accept(args: argparse.Namespace) -> int:
    candidates = list(dict.fromkeys(args.model))
    if not 2 <= len(candidates) <= 3:
        raise SystemExit("R3 local acceptance requires exactly two or three distinct models")
    client = OllamaClient(args.url)
    _validate_installed_candidates(client, candidates)
    results = BaselineBench(client).run(candidates)
    output = Path(args.output)
    metadata = _benchmark_metadata(client, candidates, "R3-local-acceptance")
    metadata["acceptance_completed"] = True
    metadata["candidate_count"] = len(candidates)
    BaselineBench.save(results, output, metadata=metadata)
    payload = {
        "R3_local_acceptance": "COMPLETED",
        "output": str(output),
        "candidates": candidates,
        "summary": BaselineBench.summarize(results),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


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
    bench.add_argument("--url", default="http://127.0.0.1:11434")
    bench.add_argument("--output", default=".kodepoia/benchmarks/r3-baseline.json")
    bench.set_defaults(func=_bench_models)

    r3 = commands.add_parser("r3-accept")
    r3.add_argument("--model", action="append", required=True)
    r3.add_argument("--url", default="http://127.0.0.1:11434")
    r3.add_argument("--output", default=".kodepoia/benchmarks/r3-local-acceptance.json")
    r3.set_defaults(func=_r3_accept)
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
