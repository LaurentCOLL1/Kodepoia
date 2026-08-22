from __future__ import annotations

import base64
import binascii
import hashlib
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from kodepoia.intelligence.research.media import (
    LocalMediaAcceptance,
    MediaAcceptanceReport,
    MediaProcessingError,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary


_MAX_FIXTURE_PARTS = 16


def _read_multipart_payload(
    boundary: WorkspaceBoundary,
    logical_fixture: str | Path,
    *,
    max_decoded_bytes: int,
) -> bytes:
    logical = boundary.resolve(logical_fixture, must_exist=False)
    logical_relative = boundary.relative(logical)
    prefix = f"{logical_relative}.b64."
    encoded_parts: list[str] = []
    encoded_total = 0

    for index in range(1, _MAX_FIXTURE_PARTS + 1):
        part = boundary.resolve(f"{prefix}{index:03d}", must_exist=False)
        if not part.exists():
            if index == 1:
                break
            break
        if not part.is_file():
            raise MediaProcessingError("media fixture payload part must be a file")
        try:
            text = part.read_text(encoding="ascii").strip()
        except (OSError, UnicodeError) as exc:
            raise MediaProcessingError("media fixture payload part is not ASCII") from exc
        if not text or len(text) % 4 != 0:
            raise MediaProcessingError("media fixture payload part has invalid base64 alignment")
        encoded_total += len(text)
        if encoded_total > ((max_decoded_bytes * 4) // 3) + 8192:
            raise MediaProcessingError("encoded media fixture exceeds configured byte budget")
        encoded_parts.append(text)

    if not encoded_parts:
        single = boundary.resolve(f"{logical_relative}.b64", must_exist=False)
        if not single.exists() or not single.is_file():
            raise MediaProcessingError("media fixture payload is unavailable")
        try:
            encoded_parts.append(single.read_text(encoding="ascii").strip())
        except (OSError, UnicodeError) as exc:
            raise MediaProcessingError("media fixture payload is not ASCII") from exc

    try:
        decoded = base64.b64decode("".join(encoded_parts), validate=True)
    except binascii.Error as exc:
        raise MediaProcessingError("media fixture payload is invalid base64") from exc
    if len(decoded) > max_decoded_bytes:
        raise MediaProcessingError("decoded media fixture exceeds configured byte budget")
    return decoded


def run_fixture_acceptance(
    acceptance: LocalMediaAcceptance,
    logical_fixture: str | Path,
) -> MediaAcceptanceReport:
    """Run R7.7 acceptance for an actual fixture or its strict multipart payload.

    Multipart materialization is an acceptance-evidence concern only. The normal
    LocalMediaAcceptance path continues to process ordinary, already-existing
    project-relative media files without this wrapper.
    """

    boundary = WorkspaceBoundary(acceptance.project_root)
    logical = boundary.resolve(logical_fixture, must_exist=False)
    logical_relative = boundary.relative(logical)
    if logical.exists():
        return acceptance.run(logical_relative)

    payload = _read_multipart_payload(
        boundary,
        logical_relative,
        max_decoded_bytes=acceptance.policy.max_input_bytes,
    )
    temp_root = boundary.resolve(".kodepoia/research/tmp", must_exist=False)
    temp_root.mkdir(parents=True, exist_ok=True)
    outer = Path(tempfile.mkdtemp(prefix="r7_7_fixture_", dir=temp_root))
    try:
        materialized = outer / logical.name
        materialized.write_bytes(payload)
        relative_materialized = boundary.relative(materialized)
        report = acceptance.run(relative_materialized)
        return replace(report, fixture_relative_path=logical_relative)
    finally:
        shutil.rmtree(outer, ignore_errors=True)


def multipart_fixture_sha256(
    project_root: Path,
    logical_fixture: str | Path,
    *,
    max_decoded_bytes: int,
) -> tuple[int, str]:
    boundary = WorkspaceBoundary(project_root)
    payload = _read_multipart_payload(
        boundary,
        logical_fixture,
        max_decoded_bytes=max_decoded_bytes,
    )
    return len(payload), hashlib.sha256(payload).hexdigest()
