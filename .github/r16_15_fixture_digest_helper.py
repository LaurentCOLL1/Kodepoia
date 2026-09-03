from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TECHNICAL_SHA = "6b42a4c41c8cb89a464ec45236aea6fee2709101"
SOURCE = Path("src/kodepoia/project/r16_15_acceptance.py")
TEST = Path("tests/test_r16_15_project_durability.py")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    root = Path(sys.argv[1]).resolve(strict=True)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, encoding="utf-8"
    ).strip()
    if head != TECHNICAL_SHA:
        raise SystemExit(f"wrong technical source: expected {TECHNICAL_SHA}, got {head}")

    source_path = root / SOURCE
    source = source_path.read_text(encoding="utf-8")
    source = replace_once(
        source,
        "    return validate_fixture_payload(payload), raw\n",
        "    return validate_fixture_payload(payload), _canonical(payload).encode(\"utf-8\")\n",
        label="canonical fixture bytes",
    )
    source_path.write_text(source, encoding="utf-8", newline="\n")

    test_path = root / TEST
    test = test_path.read_text(encoding="utf-8")
    test = replace_once(
        test,
        "import copy\nimport json\n",
        "import copy\nimport hashlib\nimport json\n",
        label="hashlib import",
    )
    test = replace_once(
        test,
        "    FIXTURE_RELATIVE,\n    DurabilityGovernanceError,\n",
        "    FIXTURE_RELATIVE,\n    DurabilityGovernanceError,\n    _load_fixture,\n",
        label="fixture loader import",
    )
    anchor = (
        "    assert validated[\"authority\"][\"permission_epoch\"] == 7\n\n\n"
        "@pytest.mark.parametrize(\n"
    )
    addition = (
        "    assert validated[\"authority\"][\"permission_epoch\"] == 7\n\n\n"
        "def test_r16_15_fixture_digest_is_line_ending_independent(tmp_path: Path) -> None:\n"
        "    raw = (ROOT / FIXTURE_RELATIVE).read_bytes().replace(b\"\\r\\n\", b\"\\n\")\n"
        "    digests: list[str] = []\n"
        "    for name, content in (\n"
        "        (\"lf\", raw),\n"
        "        (\"crlf\", raw.replace(b\"\\n\", b\"\\r\\n\")),\n"
        "    ):\n"
        "        root = tmp_path / name\n"
        "        fixture_path = root / FIXTURE_RELATIVE\n"
        "        fixture_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "        fixture_path.write_bytes(content)\n"
        "        _payload, canonical_bytes = _load_fixture(root)\n"
        "        digests.append(hashlib.sha256(canonical_bytes).hexdigest())\n"
        "    assert digests[0] == digests[1]\n\n\n"
        "@pytest.mark.parametrize(\n"
    )
    test = replace_once(test, anchor, addition, label="line-ending regression test")
    test_path.write_text(test, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
