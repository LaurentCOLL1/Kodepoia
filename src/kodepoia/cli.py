from __future__ import annotations

import argparse
from pathlib import Path

from kodepoia.project.dna import Dimension, Platform, ProjectType
from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState


def _project_init(args: argparse.Namespace) -> int:
    state = ProjectWizardState(name=args.name, project_type=ProjectType(args.type), platforms=[Platform(item) for item in args.platform], engine=args.engine, engine_version=args.engine_version, dimension=Dimension(args.dimension) if args.dimension else None, inputs=args.input)
    result = ProjectInitializer().initialize(Path(args.directory), state.build())
    print(result.dna_path)
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
