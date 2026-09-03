from __future__ import annotations

import subprocess
from pathlib import Path

SOURCE_SHA = "1a05f94accee401cfca5d9f361c4191821db0fd6"
TARGET = Path("src/kodepoia/quality/resource_soak.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != SOURCE_SHA:
        raise SystemExit("R16.16 fix helper is not on the expected rejected source")

    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from concurrent.futures import ThreadPoolExecutor\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n",
        "from collections.abc import Mapping\nfrom concurrent.futures import ThreadPoolExecutor\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Any\n",
        "Mapping import",
    )
    text = replace_once(
        text,
        "    with Path(os.path.abspath(repo_root)).resolve():\n        pass\n    import tempfile\n",
        "    import tempfile\n",
        "invalid Path context manager",
    )
    text = replace_once(
        text,
        '        cases.append(_case("absolute_resource_budgets", all_budgeted, "all bounded repetitions fit hard budgets"))\n',
        '        cases.append(\n            _case(\n                "absolute_resource_budgets",\n                all_budgeted,\n                "all bounded repetitions fit hard budgets",\n            )\n        )\n',
        "absolute resource budget formatting",
    )
    text = replace_once(
        text,
        '                all(item.thread_delta_after <= int(budgets["max_thread_delta_after"]) for item in repetitions),\n',
        '                all(\n                    item.thread_delta_after <= int(budgets["max_thread_delta_after"])\n                    for item in repetitions\n                ),\n',
        "thread count formatting",
    )
    text = replace_once(
        text,
        '            "required resource probes are available" if required_ok else f"missing={\',\'.join(missing_required)}",\n',
        '            (\n                "required resource probes are available"\n                if required_ok\n                else f"missing={\',\'.join(missing_required)}"\n            ),\n',
        "capacity preflight formatting",
    )
    text = replace_once(
        text,
        '    vram_truthful = availability["vram"]["state"] == "INCONCLUSIVE" and "vram" in policy["optional_capacities"]\n',
        '    vram_truthful = (\n        availability["vram"]["state"] == "INCONCLUSIVE"\n        and "vram" in policy["optional_capacities"]\n    )\n',
        "VRAM formatting",
    )
    text = replace_once(
        text,
        '    orphan_budget_ok = 1 <= int(budgets["max_active_processes_after"])\n',
        '    orphan_budget_ok = int(budgets["max_active_processes_after"]) >= 1\n',
        "orphan negative control",
    )
    text = replace_once(
        text,
        '    temp_leak_ok = 1 <= int(budgets["max_temp_files_after"])\n',
        '    temp_leak_ok = int(budgets["max_temp_files_after"]) >= 1\n',
        "temp negative control",
    )
    TARGET.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
