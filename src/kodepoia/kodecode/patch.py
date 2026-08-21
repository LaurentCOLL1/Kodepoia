from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from kodepoia.kodecode.workspace import WorkspaceBoundary


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PatchResult:
    path: str
    before_sha256: str
    after_sha256: str
    replacements: int


class PatchTool:
    """Apply a guarded exact-text patch using an atomic same-directory replace.

    The old text must occur exactly once, preventing ambiguous multi-location
    edits. An optional expected SHA-256 protects against stale-agent patches.
    """

    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self.boundary = boundary

    def replace_once(
        self,
        path: str,
        *,
        old_text: str,
        new_text: str,
        expected_sha256: str | None = None,
    ) -> PatchResult:
        if old_text == "":
            raise ValueError("old_text cannot be empty")

        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise IsADirectoryError(path)

        original = target.read_text(encoding="utf-8")
        before_hash = _sha256_text(original)
        if expected_sha256 is not None and expected_sha256.lower() != before_hash:
            raise ValueError("Patch precondition failed: file SHA-256 does not match expected_sha256")

        occurrences = original.count(old_text)
        if occurrences != 1:
            raise ValueError(f"Patch requires exactly one old_text occurrence, found {occurrences}")

        updated = original.replace(old_text, new_text, 1)
        after_hash = _sha256_text(updated)
        self._atomic_write(target, updated)
        return PatchResult(
            path=self.boundary.relative(target),
            before_sha256=before_hash,
            after_sha256=after_hash,
            replacements=1,
        )

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=target.parent,
                prefix=".kodepoia-patch-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            os.replace(temp_path, target)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
