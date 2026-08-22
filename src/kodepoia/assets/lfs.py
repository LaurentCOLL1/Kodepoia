from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable

from kodepoia.core.audit import AuditLog
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.kodecode.workspace import WorkspaceBoundary


LFS_VERSION_URL = "https://git-lfs.github.com/spec/v1"
_OID_RE = re.compile(r"^[0-9a-f]{64}$")
_EXTENSION_RE = re.compile(r"^ext-(?P<priority>\d+)-(?P<name>[A-Za-z0-9_.-]+) sha256:(?P<oid>[0-9a-f]{64})$")

REQUIRED_HEAVY_PATTERNS = (
    "*.blend", "*.fbx", "*.glb", "*.psd", "*.kra", "*.exr", "*.hdr", "*.tif", "*.tiff",
    "*.wav", "*.flac", "*.mp4", "*.mov", "*.mkv", "*.zip", "*.7z",
)


class LfsPointerError(ValueError):
    pass


class LfsCapabilityState(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class LfsPointerState(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    NOT_POINTER = "not_pointer"


class LfsObjectState(StrEnum):
    PRESENT = "present"
    MISSING = "missing"
    MISMATCH = "mismatch"
    UNAVAILABLE = "unavailable"


class LfsWorkingState(StrEnum):
    HYDRATED_MATCH = "hydrated_match"
    HYDRATED_MISMATCH = "hydrated_mismatch"
    POINTER_ONLY = "pointer_only"
    MISSING = "missing"
    NOT_CHECKED = "not_checked"


@dataclass(frozen=True, slots=True)
class LfsPointerExtension:
    priority: int
    name: str
    oid_sha256: str

    def line(self) -> str:
        return f"ext-{self.priority}-{self.name} sha256:{self.oid_sha256}"


@dataclass(frozen=True, slots=True)
class LfsPointer:
    oid_sha256: str
    size: int
    extensions: tuple[LfsPointerExtension, ...] = ()

    def __post_init__(self) -> None:
        if not _OID_RE.fullmatch(self.oid_sha256):
            raise LfsPointerError("Git LFS OID must be 64 lowercase SHA-256 hex characters")
        if self.size < 0:
            raise LfsPointerError("Git LFS size must be non-negative")
        priorities = [item.priority for item in self.extensions]
        if priorities != sorted(priorities) or len(priorities) != len(set(priorities)):
            raise LfsPointerError("Git LFS pointer extension priorities must be unique and sorted")

    def canonical_text(self) -> str:
        lines = [f"version {LFS_VERSION_URL}"]
        lines.extend(item.line() for item in self.extensions)
        lines.extend((f"oid sha256:{self.oid_sha256}", f"size {self.size}"))
        return "\n".join(lines) + "\n"

    def canonical_bytes(self) -> bytes:
        return self.canonical_text().encode("utf-8")


def parse_lfs_pointer(data: bytes, *, strict: bool = True) -> LfsPointer:
    if not data or len(data) > 1024:
        raise LfsPointerError("Git LFS pointer must be non-empty and at most 1024 bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LfsPointerError("Git LFS pointer must be UTF-8") from exc
    if "\r" in text or "\x00" in text:
        raise LfsPointerError("Git LFS pointer contains forbidden control bytes")
    raw_lines = text.split("\n")
    if raw_lines[-1] == "":
        raw_lines.pop()
    if not raw_lines or raw_lines[0] != f"version {LFS_VERSION_URL}":
        raise LfsPointerError("Unsupported Git LFS pointer version")
    if any(not line for line in raw_lines):
        raise LfsPointerError("Git LFS pointer contains an empty interior line")

    oid: str | None = None
    size: int | None = None
    extensions: list[LfsPointerExtension] = []
    seen_priorities: set[int] = set()
    seen_required: set[str] = set()
    for line in raw_lines[1:]:
        if line.startswith("oid "):
            if "oid" in seen_required:
                raise LfsPointerError("Duplicate Git LFS oid field")
            seen_required.add("oid")
            prefix = "oid sha256:"
            if not line.startswith(prefix):
                raise LfsPointerError("Git LFS OID algorithm must be sha256")
            candidate = line[len(prefix):]
            if not _OID_RE.fullmatch(candidate):
                raise LfsPointerError("Malformed Git LFS SHA-256 OID")
            oid = candidate
            continue
        if line.startswith("size "):
            if "size" in seen_required:
                raise LfsPointerError("Duplicate Git LFS size field")
            seen_required.add("size")
            raw_size = line[5:]
            if not raw_size.isdecimal():
                raise LfsPointerError("Malformed Git LFS size")
            size = int(raw_size)
            continue
        match = _EXTENSION_RE.fullmatch(line)
        if match is None:
            raise LfsPointerError(f"Unsupported Git LFS pointer field: {line}")
        priority = int(match.group("priority"))
        if priority in seen_priorities:
            raise LfsPointerError("Duplicate Git LFS extension priority")
        seen_priorities.add(priority)
        extensions.append(LfsPointerExtension(priority, match.group("name"), match.group("oid")))

    if oid is None or size is None:
        raise LfsPointerError("Git LFS pointer requires oid and size")
    extensions.sort(key=lambda item: item.priority)
    pointer = LfsPointer(oid, size, tuple(extensions))
    if strict and data != pointer.canonical_bytes():
        raise LfsPointerError("Git LFS pointer is valid-looking but non-canonical")
    return pointer


@dataclass(frozen=True, slots=True)
class LfsCapability:
    state: LfsCapabilityState
    version: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class LfsTrackingRule:
    pattern: str
    filter_lfs: bool
    diff_lfs: bool
    merge_lfs: bool
    binary_text: bool

    @property
    def canonical(self) -> bool:
        return self.filter_lfs and self.diff_lfs and self.merge_lfs and self.binary_text


@dataclass(frozen=True, slots=True)
class LfsFileDiagnostic:
    path: str
    tracked: bool
    pointer_state: LfsPointerState
    object_state: LfsObjectState
    working_state: LfsWorkingState
    oid_sha256: str | None
    expected_size: int | None
    detail: str


class GitLfsService:
    """Offline-first Git LFS diagnostics with a fixed local command surface."""

    def __init__(
        self,
        boundary: WorkspaceBoundary,
        *,
        sandbox: ProcessSandbox | None = None,
        audit: AuditLog | None = None,
        safe_change: SafeChangeManager | None = None,
    ) -> None:
        self.boundary = boundary
        self.sandbox = sandbox or ProcessSandbox(boundary.root, {"git", "git.exe"})
        self.audit = audit or AuditLog(boundary.resolve(".kodepoia/audit/lfs.jsonl"))
        self.safe_change = safe_change or SafeChangeManager(
            boundary.root,
            boundary.resolve(".kodepoia/snapshots/lfs"),
        )

    def _run(self, args: list[str], *, allow_failure: bool = False) -> SandboxResult:
        result = self.sandbox.run(["git", *args], cwd=self.boundary.root, timeout=120.0)
        if result.timed_out:
            raise TimeoutError("Git LFS diagnostic timed out")
        if result.cancelled:
            raise RuntimeError("Git LFS diagnostic cancelled by Kodepoia kill switch")
        if result.returncode != 0 and not allow_failure:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise RuntimeError(f"Structured Git LFS operation failed: {detail}")
        return result

    def _path(self, value: str, *, must_exist: bool = False) -> str:
        if not value or "\x00" in value or "\n" in value or "\r" in value:
            raise ValueError("Git LFS path must be a non-empty relative path")
        path = Path(value)
        if path.is_absolute() or ":" in value:
            raise ValueError("Git LFS path must be an unambiguous relative path")
        resolved = self.boundary.resolve(path, must_exist=must_exist)
        relative = self.boundary.relative(resolved).replace("\\", "/")
        if relative == ".git" or relative.startswith(".git/"):
            raise ValueError("Git metadata paths are not valid LFS asset paths")
        return relative

    def capability(self) -> LfsCapability:
        result = self._run(["lfs", "version"], allow_failure=True)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "git-lfs unavailable"
            return LfsCapability(LfsCapabilityState.UNAVAILABLE, None, detail)
        line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        version = line.split("/", 1)[1].split(" ", 1)[0] if line.startswith("git-lfs/") else line or None
        return LfsCapability(LfsCapabilityState.AVAILABLE, version, line)

    def lfs_files(self) -> tuple[str, ...]:
        if self.capability().state is LfsCapabilityState.UNAVAILABLE:
            return ()
        result = self._run(["lfs", "ls-files", "--name-only"])
        return tuple(sorted({line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}))

    def tracking_rules(self) -> tuple[LfsTrackingRule, ...]:
        path = self.boundary.resolve(".gitattributes")
        if not path.exists():
            return ()
        rules: list[LfsTrackingRule] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            pattern, attrs = parts[0], set(parts[1:])
            if "filter=lfs" not in attrs and "diff=lfs" not in attrs and "merge=lfs" not in attrs:
                continue
            rules.append(
                LfsTrackingRule(
                    pattern,
                    "filter=lfs" in attrs,
                    "diff=lfs" in attrs,
                    "merge=lfs" in attrs,
                    "-text" in attrs,
                )
            )
        return tuple(rules)

    def required_policy_gaps(self) -> tuple[str, ...]:
        rules = {item.pattern: item for item in self.tracking_rules()}
        return tuple(pattern for pattern in REQUIRED_HEAVY_PATTERNS if pattern not in rules or not rules[pattern].canonical)

    def path_is_lfs_tracked(self, path: str) -> bool:
        relative = self._path(path)
        result = self._run(["check-attr", "-z", "filter", "diff", "merge", "text", "--", relative])
        fields = result.stdout.split("\x00")
        values: dict[str, str] = {}
        for index in range(0, len(fields) - 2, 3):
            _record_path, attr, value = fields[index:index + 3]
            if attr:
                values[attr] = value
        return (
            values.get("filter") == "lfs"
            and values.get("diff") == "lfs"
            and values.get("merge") == "lfs"
            and values.get("text") == "unset"
        )

    def propose_tracking(self, pattern: str) -> str:
        if pattern not in REQUIRED_HEAVY_PATTERNS:
            raise ValueError("Tracking proposals are restricted to the frozen heavy-asset policy")
        rules = {item.pattern: item for item in self.tracking_rules()}
        if pattern in rules and rules[pattern].canonical:
            return "already-tracked"
        return f"{pattern} filter=lfs diff=lfs merge=lfs -text"

    def apply_tracking(self, pattern: str, *, confirmed: bool, actor: str = "user") -> str:
        proposal = self.propose_tracking(pattern)
        if proposal == "already-tracked":
            return proposal
        if not confirmed:
            raise PermissionError("Explicit confirmation is required before changing .gitattributes")
        attributes = self.boundary.resolve(".gitattributes")
        if not attributes.exists():
            attributes.write_text("", encoding="utf-8")
        snapshot = self.safe_change.snapshot([attributes])
        original = attributes.read_text(encoding="utf-8")
        suffix = "" if not original or original.endswith("\n") else "\n"
        replacement = original + suffix + proposal + "\n"
        temp = attributes.with_name(attributes.name + ".kodepoia-lfs-tmp")
        try:
            temp.write_text(replacement, encoding="utf-8", newline="\n")
            os.replace(temp, attributes)
        except Exception:
            if temp.exists():
                temp.unlink()
            self.audit.append("asset_lfs", "track", actor, "failure", {"pattern": pattern})
            raise
        self.audit.append(
            "asset_lfs",
            "track",
            actor,
            "success",
            {"pattern": pattern, "snapshot": self.boundary.relative(snapshot).replace("\\", "/")},
        )
        return proposal

    @staticmethod
    def _sha256(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
                total += len(chunk)
        return digest.hexdigest(), total

    def _local_object_path(self, pointer: LfsPointer) -> Path | None:
        result = self._run(["rev-parse", "--git-common-dir"], allow_failure=True)
        if result.returncode != 0 or not result.stdout.strip():
            return None
        common = Path(result.stdout.strip())
        try:
            resolved_common = common.resolve(strict=False) if common.is_absolute() else self.boundary.resolve(common)
            if resolved_common != self.boundary.root and self.boundary.root not in resolved_common.parents:
                return None
            object_path = resolved_common / "lfs" / "objects" / pointer.oid_sha256[:2] / pointer.oid_sha256[2:4] / pointer.oid_sha256
            resolved = object_path.resolve(strict=False)
            if resolved_common != resolved and resolved_common not in resolved.parents:
                return None
            return resolved
        except (ValueError, OSError):
            return None

    def diagnose(self, path: str) -> LfsFileDiagnostic:
        relative = self._path(path)
        tracked = self.path_is_lfs_tracked(relative)
        size_result = self._run(["cat-file", "-s", f":{relative}"], allow_failure=True)
        if size_result.returncode != 0:
            return LfsFileDiagnostic(relative, tracked, LfsPointerState.NOT_POINTER, LfsObjectState.UNAVAILABLE, LfsWorkingState.MISSING, None, None, "path is not present in the Git index")
        try:
            blob_size = int(size_result.stdout.strip())
        except ValueError:
            blob_size = 1025
        if blob_size > 1024:
            return LfsFileDiagnostic(relative, tracked, LfsPointerState.NOT_POINTER, LfsObjectState.UNAVAILABLE, LfsWorkingState.NOT_CHECKED, None, None, "index blob is not an LFS pointer-sized object")
        blob_result = self._run(["cat-file", "blob", f":{relative}"])
        blob = blob_result.stdout.encode("utf-8")
        try:
            pointer = parse_lfs_pointer(blob, strict=True)
        except LfsPointerError as exc:
            return LfsFileDiagnostic(relative, tracked, LfsPointerState.INVALID, LfsObjectState.UNAVAILABLE, LfsWorkingState.NOT_CHECKED, None, None, str(exc))

        object_path = self._local_object_path(pointer)
        if object_path is None:
            object_state = LfsObjectState.UNAVAILABLE
        elif not object_path.is_file():
            object_state = LfsObjectState.MISSING
        else:
            digest, length = self._sha256(object_path)
            object_state = LfsObjectState.PRESENT if (digest, length) == (pointer.oid_sha256, pointer.size) else LfsObjectState.MISMATCH

        working = self.boundary.resolve(relative)
        if not working.exists():
            working_state = LfsWorkingState.MISSING
        elif not working.is_file():
            working_state = LfsWorkingState.NOT_CHECKED
        else:
            probe = working.read_bytes() if working.stat().st_size <= 1024 else b""
            try:
                working_pointer = parse_lfs_pointer(probe, strict=True) if probe else None
            except LfsPointerError:
                working_pointer = None
            if working_pointer is not None and working_pointer == pointer:
                working_state = LfsWorkingState.POINTER_ONLY
            else:
                digest, length = self._sha256(working)
                working_state = LfsWorkingState.HYDRATED_MATCH if (digest, length) == (pointer.oid_sha256, pointer.size) else LfsWorkingState.HYDRATED_MISMATCH

        return LfsFileDiagnostic(relative, tracked, LfsPointerState.VALID, object_state, working_state, pointer.oid_sha256, pointer.size, "canonical Git LFS pointer parsed")

    def local_fsck(self) -> tuple[bool, str]:
        capability = self.capability()
        if capability.state is LfsCapabilityState.UNAVAILABLE:
            return False, "UNAVAILABLE"
        result = self._run(["lfs", "fsck", "--objects", "--dry-run"], allow_failure=True)
        detail = (result.stdout + "\n" + result.stderr).strip()
        return result.returncode == 0, detail
