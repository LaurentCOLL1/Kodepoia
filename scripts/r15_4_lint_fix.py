from pathlib import Path

path = Path("src/kodepoia/experience/dedup.py")
text = path.read_text(encoding="utf-8")
old_imports = (
    "from dataclasses import dataclass, field\n"
    "from enum import StrEnum\n"
    "from typing import Iterable, Mapping\n"
)
new_imports = (
    "from collections.abc import Iterable, Mapping\n"
    "from dataclasses import dataclass, field\n"
    "from enum import StrEnum\n"
)
assert text.count(old_imports) == 1
text = text.replace(old_imports, new_imports, 1)
old = '            raise DedupError(f"holdout_id already registered with different fingerprint: {holdout.holdout_id}")\n'
new = (
    '            raise DedupError(\n'
    '                f"holdout_id already registered with different fingerprint: {holdout.holdout_id}"\n'
    '            )\n'
)
assert text.count(old) == 1
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8", newline="\n")
