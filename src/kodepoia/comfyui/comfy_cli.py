from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .client import ComfyUIClient
from .serialization import make_envelope


def _confined_output(path_text: str) -> Path:
    requested = Path(path_text)
    if requested.is_absolute():
        raise SystemExit("comfy-probe output must be relative to the current workspace")
    root = Path.cwd().resolve(strict=False)
    destination = (root / requested).resolve(strict=False)
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise SystemExit("comfy-probe output must remain inside the current workspace") from exc
    return destination


def _write_atomic_json(destination: Path, document: dict[str, object]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(destination)


def _probe(args: argparse.Namespace) -> int:
    client = ComfyUIClient(args.endpoint)
    snapshot = client.probe()
    document = make_envelope(
        schema="kodepoia.comfy-protocol-probe",
        version=1,
        payload=snapshot.canonical(),
    )
    destination = _confined_output(args.output)
    _write_atomic_json(destination, document)
    print(
        json.dumps(
            {
                "output": str(destination),
                "ready": snapshot.ready,
                "probe": document,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if snapshot.ready else 2


def register_comfy_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    probe = commands.add_parser(
        "comfy-probe",
        help="Probe the fixed loopback ComfyUI R9.2 protocol surface",
    )
    probe.add_argument("--endpoint", default="http://127.0.0.1:8188")
    probe.add_argument(
        "--output",
        default=".kodepoia/evidence/r9-2-comfy-probe.json",
        help="workspace-relative versioned protocol evidence output",
    )
    probe.set_defaults(func=_probe)
