from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path("/tmp/r16_14_implementation_helper.py", run_name="__main__")


def replace_exact(data: bytes, old: bytes, new: bytes, *, label: str) -> bytes:
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"{label} anchor count={count}")
    return data.replace(old, new, 1)


runner = Path("scripts/r16_14_media_beta_acceptance.py")
data = runner.read_bytes()
data = replace_exact(
    data,
    b'json.dumps(report, indent=2, sort_keys=True) + "' + b"\n" + b'", encoding=',
    b'json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding=',
    label="runner newline escape",
)
data = replace_exact(
    data,
    b'newline="' + b"\n" + b'"',
    b'newline="\\n"',
    label="runner newline parameter",
)
data = replace_exact(
    data,
    b'help="Record that an optional human/device listening claim was requested; core CI then reports MANUAL_REQUIRED.",',
    (
        b'help=(\n'
        b'            "Record that an optional human/device listening claim was requested; "\n'
        b'            "core CI then reports MANUAL_REQUIRED."\n'
        b'        ),'
    ),
    label="runner human listening help",
)
runner.write_bytes(data)

acceptance = Path("src/kodepoia/media/r16_14_acceptance.py")
data = acceptance.read_bytes()
data = replace_exact(
    data,
    b'"detail": "an explicitly requested listening/device-quality claim requires a human/device qualification outside core CI",',
    (
        b'"detail": (\n'
        b'            "an explicitly requested listening/device-quality claim requires a "\n'
        b'            "human/device qualification outside core CI"\n'
        b'        ),'
    ),
    label="manual listening detail",
)
data = replace_exact(
    data,
    b'"existing local TTS registry/request contracts are exercised without claiming a live synthesis runtime",',
    (
        b'(\n'
        b'                "existing local TTS registry/request contracts are exercised without "\n'
        b'                "claiming a live synthesis runtime"\n'
        b'            ),'
    ),
    label="TTS contract detail",
)
data = replace_exact(
    data,
    b'"visemes are deterministically derived from the exact alignment and bounded coarticulation policy",',
    (
        b'(\n'
        b'                "visemes are deterministically derived from the exact alignment and "\n'
        b'                "bounded coarticulation policy"\n'
        b'            ),'
    ),
    label="viseme detail",
)
data = replace_exact(
    data,
    b'"media evidence binds exact source, fixture, text, voice, request, audio, alignment, viseme and cinematic digests",',
    (
        b'(\n'
        b'                "media evidence binds exact source, fixture, text, voice, request, audio, "\n'
        b'                "alignment, viseme and cinematic digests"\n'
        b'            ),'
    ),
    label="evidence binding detail",
)
acceptance.write_bytes(data)

test = Path("tests/test_r16_14_media_beta.py")
data = test.read_bytes()
data = replace_exact(
    data,
    b'raw.replace(b"' + b"\n" + b'", b"' + b"\r\n" + b'").decode("utf-8")',
    b'raw.replace(b"\\n", b"\\r\\n").decode("utf-8")',
    label="test line-ending escape",
)
test.write_bytes(data)
