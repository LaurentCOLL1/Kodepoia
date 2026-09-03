from __future__ import annotations

import subprocess
from pathlib import Path

SOURCE_SHA = "532cb5b0f1d87da987fb0d6ab197d297623566f9"
TARGET = Path("tests/test_supply_chain_r16_9.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != SOURCE_SHA:
        raise SystemExit("R16.16 supply-chain fix helper is not on the expected source")
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    assert len(policy.immutable_authority_workflows) == 18\n",
        "    assert len(policy.immutable_authority_workflows) == 19\n",
        "authority workflow count",
    )
    anchor = (
        "    assert (\n"
        "        \".github/workflows/r16-15-project-durability-acceptance.yml\"\n"
        "        in policy.immutable_authority_workflows\n"
        "    )\n"
    )
    replacement = anchor + (
        "    assert (\n"
        "        \".github/workflows/r16-16-resource-soak-acceptance.yml\"\n"
        "        in policy.immutable_authority_workflows\n"
        "    )\n"
    )
    text = replace_once(text, anchor, replacement, "R16.16 authority assertion")
    TARGET.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
