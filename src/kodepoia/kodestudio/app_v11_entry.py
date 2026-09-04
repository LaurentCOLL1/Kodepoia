from __future__ import annotations

import sys
import traceback
from pathlib import Path


def _smoke_report_path() -> Path | None:
    prefix = "--smoke-report="
    for arg in sys.argv[1:]:
        if arg.startswith(prefix):
            raw = arg[len(prefix) :].strip()
            if raw:
                return Path(raw)
    return None


def _write_smoke_report(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError:
        # Diagnostic output must never change normal application behavior.
        pass


def main() -> int:
    report = _smoke_report_path()
    try:
        from kodepoia.kodestudio.app_v11 import main as app_main

        return int(app_main())
    except BaseException:
        if report is not None:
            _write_smoke_report(report, traceback.format_exc())
            return 1
        raise


if __name__ == "__main__":
    raise SystemExit(main())
