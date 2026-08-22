from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.kodegodot.acceptance import R5AcceptanceRunner
from kodepoia.kodegodot.services import GodotServicePorts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kodepoia-r5-accept")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--output", default=".kodepoia/benchmarks/r5-local-acceptance.json")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--lsp-port", type=int, default=6005)
    parser.add_argument("--dap-port", type=int, default=6006)
    parser.add_argument("--debug-port", type=int, default=6007)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.repo_root).resolve(strict=False)
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    runner = R5AcceptanceRunner(
        root,
        executable=args.godot,
        output=output,
        ports=GodotServicePorts(args.lsp_port, args.dap_port, args.debug_port),
    )
    payload = runner.probe() if args.probe_only else runner.run()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.probe_only:
        engine = next((item for item in payload["steps"] if item["name"] == "engine_version"), None)
        return 0 if engine and engine["passed"] else 2
    return 0 if payload["metadata"]["acceptance_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
