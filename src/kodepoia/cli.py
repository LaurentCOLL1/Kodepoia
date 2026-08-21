from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.bench.baseline import BaselineBench
from kodepoia.brain.ollama import OllamaClient
from kodepoia.project.dna import Dimension, Platform, ProjectType
from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState


def _project_init(args: argparse.Namespace) -> int:
    state = ProjectWizardState(name=args.name, project_type=ProjectType(args.type), platforms=[Platform(item) for item in args.platform], engine=args.engine, engine_version=args.engine_version, dimension=Dimension(args.dimension) if args.dimension else None, inputs=args.input)
    result = ProjectInitializer().initialize(Path(args.directory), state.build())
    print(result.dna_path)
    return 0


def _ollama_status(args: argparse.Namespace) -> int:
    client = OllamaClient(args.url)
    print(json.dumps({"version": client.version(), "models": client.list_models()}, ensure_ascii=False, indent=2))
    return 0


def _bench_models(args: argparse.Namespace) -> int:
    client = OllamaClient(args.url)
    results = BaselineBench(client).run(args.model)
    output = Path(args.output)
    BaselineBench.save(results, output)
    summary = {}
    for model in args.model:
        rows = [item for item in results if item.model == model]
        summary[model] = {"passed": sum(item.passed for item in rows), "total": len(rows), "elapsed_s": round(sum(item.elapsed_s for item in rows), 3)}
    print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, indent=2))
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
    project.set_defaults(func=_project_init)
    ollama = commands.add_parser("ollama-status")
    ollama.add_argument("--url", default="http://127.0.0.1:11434")
    ollama.set_defaults(func=_ollama_status)
    bench = commands.add_parser("bench-models")
    bench.add_argument("--model", action="append", required=True)
    bench.add_argument("--url", default="http://127.0.0.1:11434")
    bench.add_argument("--output", default=".kodepoia/benchmarks/r3-baseline.json")
    bench.set_defaults(func=_bench_models)
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
