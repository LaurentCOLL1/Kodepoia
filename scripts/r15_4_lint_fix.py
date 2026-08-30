from pathlib import Path

path = Path("src/kodepoia/experience/dedup.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from typing import Iterable, Mapping\n",
    "from collections.abc import Iterable, Mapping\n",
    1,
)
old = '            raise DedupError(f"holdout_id already registered with different fingerprint: {holdout.holdout_id}")\n'
new = (
    '            raise DedupError(\n'
    '                f"holdout_id already registered with different fingerprint: {holdout.holdout_id}"\n'
    '            )\n'
)
assert text.count(old) == 1
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8", newline="\n")
