from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import struct
import subprocess
import tarfile
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

ZIP_CENTRAL_SIGNATURE = b"PK\x01\x02"
ZIP_EOCD_SIGNATURE = b"PK\x05\x06"
CANONICAL_ZIP_CREATE_SYSTEM = 3
REGULAR_FILE_MODE = 0o644
EXECUTABLE_FILE_MODE = 0o755
DIRECTORY_MODE = 0o755
SYMLINK_MODE = 0o777


class PackageCanonicalizationError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_bytes(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def canonicalize_wheel(path: str | Path) -> dict[str, Any]:
    wheel = Path(path)
    raw = bytearray(wheel.read_bytes())
    eocd = raw.rfind(ZIP_EOCD_SIGNATURE)
    if eocd < 0 or len(raw) - eocd < 22:
        raise PackageCanonicalizationError("wheel has no valid ZIP end-of-central-directory record")

    disk_number, central_disk, entries_on_disk, entries_total = struct.unpack_from(
        "<HHHH", raw, eocd + 4
    )
    central_size, central_offset = struct.unpack_from("<II", raw, eocd + 12)
    if disk_number or central_disk or entries_on_disk != entries_total:
        raise PackageCanonicalizationError("multi-disk wheel archives are not supported")
    if entries_total == 0xFFFF or central_size == 0xFFFFFFFF or central_offset == 0xFFFFFFFF:
        raise PackageCanonicalizationError("ZIP64 wheel archives are not supported")
    if central_offset + central_size != eocd:
        raise PackageCanonicalizationError("wheel central-directory boundary is not canonical")

    cursor = central_offset
    changed = 0
    for _ in range(entries_total):
        if raw[cursor : cursor + 4] != ZIP_CENTRAL_SIGNATURE:
            raise PackageCanonicalizationError("wheel central-directory entry is malformed")
        if raw[cursor + 5] != CANONICAL_ZIP_CREATE_SYSTEM:
            raw[cursor + 5] = CANONICAL_ZIP_CREATE_SYSTEM
            changed += 1
        name_length, extra_length, comment_length = struct.unpack_from("<HHH", raw, cursor + 28)
        cursor += 46 + name_length + extra_length + comment_length
    if cursor != central_offset + central_size:
        raise PackageCanonicalizationError("wheel central-directory size does not match its entries")

    _replace_bytes(wheel, bytes(raw))
    try:
        with zipfile.ZipFile(wheel) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise PackageCanonicalizationError(f"wheel CRC validation failed for {corrupt}")
            infos = archive.infolist()
            if len(infos) != entries_total:
                raise PackageCanonicalizationError("wheel entry count changed during canonicalization")
            if any(info.create_system != CANONICAL_ZIP_CREATE_SYSTEM for info in infos):
                raise PackageCanonicalizationError("wheel create_system metadata was not canonicalized")
    except zipfile.BadZipFile as exc:
        raise PackageCanonicalizationError(f"canonicalized wheel is invalid: {exc}") from exc

    return {
        "artifact": wheel.name,
        "kind": "wheel",
        "entries": entries_total,
        "metadata_entries_changed": changed,
        "sha256": _sha256(wheel),
    }


def tracked_git_modes(repo_root: str | Path) -> dict[str, int]:
    root = Path(repo_root).resolve(strict=True)
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-s", "-z"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.output.decode("utf-8", errors="replace")[-2000:]
        raise PackageCanonicalizationError(f"cannot read Git index modes: {detail}") from exc

    modes: dict[str, int] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, encoded_path = record.split(b"\t", 1)
            git_mode = metadata.split(b" ", 1)[0]
            relative = encoded_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise PackageCanonicalizationError("Git index mode record is malformed") from exc
        if git_mode == b"100755":
            modes[relative] = EXECUTABLE_FILE_MODE
        elif git_mode == b"100644":
            modes[relative] = REGULAR_FILE_MODE
    if not modes:
        raise PackageCanonicalizationError("Git index contains no canonical regular-file modes")
    return modes


def _relative_sdist_name(member_name: str, expected_root: str) -> str:
    pure = PurePosixPath(member_name)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts or pure.parts[0] != expected_root:
        raise PackageCanonicalizationError(f"unsafe or unexpected sdist member path: {member_name}")
    return PurePosixPath(*pure.parts[1:]).as_posix() if len(pure.parts) > 1 else ""


def _tar_mode_bytes(mode: int) -> bytes:
    encoded = f"{mode:07o}\0".encode("ascii")
    if len(encoded) != 8:
        raise PackageCanonicalizationError(f"tar mode cannot be encoded canonically: {mode:o}")
    return encoded


def _tar_checksum_bytes(header: bytearray) -> bytes:
    checksum_view = bytearray(header)
    checksum_view[148:156] = b"        "
    encoded = f"{sum(checksum_view):06o}\0 ".encode("ascii")
    if len(encoded) != 8:
        raise PackageCanonicalizationError("tar header checksum cannot be encoded canonically")
    return encoded


def _expected_member_mode(member: tarfile.TarInfo, relative: str, git_modes: Mapping[str, int]) -> int | None:
    if member.isfile():
        return git_modes.get(relative, REGULAR_FILE_MODE)
    if member.isdir():
        return DIRECTORY_MODE
    if member.issym():
        return SYMLINK_MODE
    return None


def canonicalize_sdist(
    path: str | Path,
    *,
    git_modes: Mapping[str, int],
    source_date_epoch: int,
) -> dict[str, Any]:
    sdist = Path(path)
    compressed = sdist.read_bytes()
    try:
        tar_bytes = bytearray(gzip.decompress(compressed))
    except (OSError, EOFError) as exc:
        raise PackageCanonicalizationError(f"sdist gzip stream is invalid: {exc}") from exc

    try:
        with tarfile.open(fileobj=io.BytesIO(bytes(tar_bytes)), mode="r:") as archive:
            members = archive.getmembers()
    except tarfile.TarError as exc:
        raise PackageCanonicalizationError(f"sdist tar stream is invalid: {exc}") from exc
    if not members:
        raise PackageCanonicalizationError("sdist contains no members")

    roots = {PurePosixPath(member.name).parts[0] for member in members if PurePosixPath(member.name).parts}
    if len(roots) != 1:
        raise PackageCanonicalizationError(f"sdist must contain one top-level root, got {sorted(roots)}")
    expected_root = next(iter(roots))

    changed = 0
    for member in members:
        relative = _relative_sdist_name(member.name, expected_root)
        expected_mode = _expected_member_mode(member, relative, git_modes)
        if expected_mode is None or member.mode == expected_mode:
            continue
        offset = member.offset
        header = bytearray(tar_bytes[offset : offset + 512])
        if len(header) != 512:
            raise PackageCanonicalizationError(f"sdist header is truncated for {member.name}")
        header[100:108] = _tar_mode_bytes(expected_mode)
        header[148:156] = _tar_checksum_bytes(header)
        tar_bytes[offset : offset + 512] = header
        changed += 1

    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=output,
        compresslevel=9,
        mtime=source_date_epoch,
    ) as stream:
        stream.write(tar_bytes)
    _replace_bytes(sdist, output.getvalue())

    try:
        with tarfile.open(sdist, mode="r:gz") as archive:
            verified = archive.getmembers()
            if len(verified) != len(members):
                raise PackageCanonicalizationError("sdist member count changed during canonicalization")
            for member in verified:
                relative = _relative_sdist_name(member.name, expected_root)
                expected_mode = _expected_member_mode(member, relative, git_modes)
                if expected_mode is not None and member.mode != expected_mode:
                    raise PackageCanonicalizationError(
                        f"sdist mode was not canonicalized for {member.name}: {member.mode:o}"
                    )
    except tarfile.TarError as exc:
        raise PackageCanonicalizationError(f"canonicalized sdist is invalid: {exc}") from exc

    raw = sdist.read_bytes()
    if len(raw) < 10 or int.from_bytes(raw[4:8], "little") != source_date_epoch or raw[9] != 255:
        raise PackageCanonicalizationError("sdist gzip header is not canonical")

    return {
        "artifact": sdist.name,
        "kind": "sdist",
        "entries": len(members),
        "metadata_entries_changed": changed,
        "source_date_epoch": source_date_epoch,
        "sha256": _sha256(sdist),
    }


def canonicalize_release_packages(
    dist_dir: str | Path,
    *,
    repo_root: str | Path,
    source_date_epoch: int,
) -> dict[str, Any]:
    dist = Path(dist_dir).resolve(strict=True)
    wheels = sorted(path for path in dist.glob("*.whl") if path.is_file())
    sdists = sorted(path for path in dist.glob("*.tar.gz") if path.is_file())
    if len(wheels) != 1 or len(sdists) != 1:
        raise PackageCanonicalizationError(
            f"expected exactly one wheel and one sdist, got wheels={wheels}, sdists={sdists}"
        )
    modes = tracked_git_modes(repo_root)
    wheel = canonicalize_wheel(wheels[0])
    sdist = canonicalize_sdist(
        sdists[0],
        git_modes=modes,
        source_date_epoch=source_date_epoch,
    )
    return {
        "schema_version": 1,
        "source_date_epoch": source_date_epoch,
        "artifacts": [wheel, sdist],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonicalize R16.17 RC package archive metadata")
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--source-date-epoch", type=int)
    args = parser.parse_args()
    epoch = args.source_date_epoch
    if epoch is None:
        raw_epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
        if not raw_epoch.isdigit():
            raise PackageCanonicalizationError("SOURCE_DATE_EPOCH must be an explicit non-negative integer")
        epoch = int(raw_epoch)
    report = canonicalize_release_packages(
        args.dist,
        repo_root=args.repo_root,
        source_date_epoch=epoch,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
