from __future__ import annotations

import gzip
import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from kodepoia.quality.release_package import (
    CANONICAL_ZIP_CREATE_SYSTEM,
    PackageCanonicalizationError,
    canonicalize_release_packages,
    canonicalize_sdist,
    canonicalize_wheel,
    tracked_git_modes,
)

ROOT = Path(__file__).resolve().parents[1]
EPOCH = 946684800


def _write_wheel(path: Path, *, create_system: int) -> None:
    info = zipfile.ZipInfo("kodepoia/__init__.py", date_time=(2000, 1, 1, 0, 0, 0))
    info.create_system = create_system
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(info, b'__version__ = "1.0.0rc1"\n')


def _write_sdist(path: Path, *, script_mode: int) -> None:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        payload = b"print('ok')\n"
        info = tarfile.TarInfo("kodepoia-1.0.0rc1/scripts/check_repo.py")
        info.size = len(payload)
        info.mode = script_mode
        info.mtime = EPOCH
        archive.addfile(info, io.BytesIO(payload))
        generated = b"metadata\n"
        generated_info = tarfile.TarInfo("kodepoia-1.0.0rc1/PKG-INFO")
        generated_info.size = len(generated)
        generated_info.mode = 0o644
        generated_info.mtime = EPOCH
        archive.addfile(generated_info, io.BytesIO(generated))
    with path.open("wb") as handle:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=handle,
            compresslevel=9,
            mtime=EPOCH,
        ) as stream:
            stream.write(tar_buffer.getvalue())


def test_wheel_create_system_canonicalization_is_byte_identical(tmp_path: Path) -> None:
    unix = tmp_path / "unix.whl"
    windows = tmp_path / "windows.whl"
    _write_wheel(unix, create_system=CANONICAL_ZIP_CREATE_SYSTEM)
    _write_wheel(windows, create_system=0)

    unix_report = canonicalize_wheel(unix)
    windows_report = canonicalize_wheel(windows)

    assert unix.read_bytes() == windows.read_bytes()
    assert unix_report["sha256"] == windows_report["sha256"]
    assert unix_report["metadata_entries_changed"] == 0
    assert windows_report["metadata_entries_changed"] == 1
    with zipfile.ZipFile(windows) as archive:
        assert archive.testzip() is None
        assert all(
            info.create_system == CANONICAL_ZIP_CREATE_SYSTEM for info in archive.infolist()
        )


def test_sdist_git_mode_canonicalization_is_byte_identical(tmp_path: Path) -> None:
    unix = tmp_path / "unix.tar.gz"
    windows = tmp_path / "windows.tar.gz"
    _write_sdist(unix, script_mode=0o755)
    _write_sdist(windows, script_mode=0o644)
    modes = {"scripts/check_repo.py": 0o755}

    unix_report = canonicalize_sdist(unix, git_modes=modes, source_date_epoch=EPOCH)
    windows_report = canonicalize_sdist(windows, git_modes=modes, source_date_epoch=EPOCH)

    assert unix.read_bytes() == windows.read_bytes()
    assert unix_report["sha256"] == windows_report["sha256"]
    assert unix_report["metadata_entries_changed"] == 0
    assert windows_report["metadata_entries_changed"] == 1
    with tarfile.open(windows, mode="r:gz") as archive:
        assert archive.getmember("kodepoia-1.0.0rc1/scripts/check_repo.py").mode == 0o755


def test_repository_git_index_is_the_executable_mode_authority() -> None:
    modes = tracked_git_modes(ROOT)
    assert modes["scripts/check_repo.py"] == 0o755


def test_release_package_canonicalizer_requires_one_wheel_and_one_sdist(
    tmp_path: Path,
) -> None:
    with pytest.raises(PackageCanonicalizationError, match="exactly one wheel and one sdist"):
        canonicalize_release_packages(tmp_path, repo_root=ROOT, source_date_epoch=EPOCH)


def test_malformed_wheel_fails_closed(tmp_path: Path) -> None:
    wheel = tmp_path / "broken.whl"
    wheel.write_bytes(b"not-a-zip")
    with pytest.raises(PackageCanonicalizationError, match="end-of-central-directory"):
        canonicalize_wheel(wheel)
