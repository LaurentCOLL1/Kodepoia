from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path("/tmp/r16_14_implementation_helper.py", run_name="__main__")

runner = Path("scripts/r16_14_media_beta_acceptance.py")
data = runner.read_bytes()
old = b'json.dumps(report, indent=2, sort_keys=True) + "' + b"\n" + b'", encoding='
new = b'json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding='
if data.count(old) != 1:
    raise RuntimeError(f"runner newline escape anchor count={data.count(old)}")
runner.write_bytes(data.replace(old, new, 1))

test = Path("tests/test_r16_14_media_beta.py")
data = test.read_bytes()
old = b'raw.replace(b"' + b"\n" + b'", b"' + b"\r\n" + b'").decode("utf-8")'
new = b'raw.replace(b"\\n", b"\\r\\n").decode("utf-8")'
if data.count(old) != 1:
    raise RuntimeError(f"test line-ending escape anchor count={data.count(old)}")
test.write_bytes(data.replace(old, new, 1))
