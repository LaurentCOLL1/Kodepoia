from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .core.paths import AppPaths
from .runtime import KodeRuntime


def main() -> int:
    parser = argparse.ArgumentParser(prog="kodepoia")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("core-check", help="construct the Protected Core and print status")
    studio = sub.add_parser("studio", help="start KodeStudio")
    studio.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.command == "studio":
        from .kodestudio.app import main as studio_main
        return studio_main(["--smoke-test"] if args.smoke_test else [])

    with tempfile.TemporaryDirectory(prefix="kodepoia-core-check-") as tmp:
        base = Path(tmp)
        runtime = KodeRuntime.build(AppPaths(base / "data", base / "config", base / "cache"), sandbox_roots=(base,))
        print(json.dumps({"guardian": "stopped" if runtime.guardian.stopped else "active", "sandbox": "active", "audit": str(runtime.audit.path), "recovery_pending": len(runtime.recovery.pending())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
