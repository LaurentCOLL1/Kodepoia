from __future__ import annotations

from pathlib import Path

import pytest

import kodepoia.mobile.android_build as android_build


def test_r13_4_staging_parent_of_source_is_rejected_before_delete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "staging"
    source = staging / "source"
    source.mkdir(parents=True)
    marker = source / "must-survive.txt"
    marker.write_text("source-owned\n", encoding="utf-8")

    monkeypatch.setattr(
        android_build,
        "verify_source_workspace",
        lambda _root: ({"files": []}, "a" * 64),
    )

    with pytest.raises(ValueError, match="isolated"):
        android_build.prepare_build_staging(source, staging, object())  # type: ignore[arg-type]

    assert marker.read_text(encoding="utf-8") == "source-owned\n"
    assert source.is_dir()
