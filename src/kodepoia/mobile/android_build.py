from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Mapping
from urllib.parse import urlparse

from kodepoia.mobile.android_scaffold import AndroidScaffoldEngine
from kodepoia.mobile.contracts import canonical_json_bytes

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")
_KOTLIN_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){2}(?:[-A-Za-z0-9.]+)?$")
_BUILD_TOOLS_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){2}$")
_APP_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_DANGEROUS_ENV = {"GRADLE_OPTS", "JAVA_TOOL_OPTIONS", "JAVA_OPTS", "_JAVA_OPTIONS"}
_ALLOWED_ENV = {"JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "HOME", "USERPROFILE", "TEMP", "TMP"}
_MAX_ZIP_ENTRIES = 100_000
_MAX_ENTRY_BYTES = 512 * 1024 * 1024
_MAX_TOTAL_UNCOMPRESSED = 4 * 1024 * 1024 * 1024


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha(value: str, label: str) -> None:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _safe_relative(value: str) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise ValueError("unsafe Android build path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("unsafe Android build path")
    return path.as_posix()


def _inside(root: Path, relative: str) -> Path:
    relative = _safe_relative(relative)
    target = root.joinpath(*PurePosixPath(relative).parts)
    ancestor = target
    tail: list[str] = []
    while not ancestor.exists() and ancestor != root:
        tail.append(ancestor.name)
        ancestor = ancestor.parent
    resolved = ancestor.resolve(strict=False)
    for part in reversed(tail):
        resolved = resolved / part
    try:
        resolved.relative_to(root.resolve(strict=False))
    except ValueError as exc:
        raise ValueError("Android build path escapes workspace root") from exc
    return resolved


def _replace_exact_line(text: str, prefix: str, replacement: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    matches = [index for index, line in enumerate(lines) if line.strip().startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one controlled build line for {prefix!r}")
    lines[matches[0]] = replacement
    return "\n".join(lines) + "\n"


class AndroidBuildTask(StrEnum):
    UNIT_TEST = "unit_test"
    APK_DEBUG = "apk_debug"
    AAB_RELEASE = "aab_release"

    @property
    def gradle_task(self) -> str:
        return {
            AndroidBuildTask.UNIT_TEST: ":app:testDebugUnitTest",
            AndroidBuildTask.APK_DEBUG: ":app:assembleDebug",
            AndroidBuildTask.AAB_RELEASE: ":app:bundleRelease",
        }[self]


class AndroidArtifactKind(StrEnum):
    APK = "apk"
    AAB = "aab"


class AndroidBuildStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AndroidBuildToolchainEvidence:
    evidence_id: str
    android_gradle_plugin: str
    gradle_version: str
    kotlin_version: str
    compose_bom: str
    compile_sdk: int
    build_tools_version: str
    jdk_major: int
    observed_on: str
    source_urls: tuple[str, ...]

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{0,127}", self.evidence_id):
            raise ValueError("invalid Android build evidence id")
        for label, value in (
            ("android_gradle_plugin", self.android_gradle_plugin),
            ("gradle_version", self.gradle_version),
        ):
            if _VERSION_RE.fullmatch(value) is None:
                raise ValueError(f"{label} must be explicit numeric dotted form")
        if _KOTLIN_VERSION_RE.fullmatch(self.kotlin_version) is None:
            raise ValueError("kotlin_version must be explicit semantic version")
        if not re.fullmatch(r"[0-9]{4}\.[0-9]{2}\.[0-9]{2}", self.compose_bom):
            raise ValueError("compose_bom must be explicit YYYY.MM.DD")
        if _BUILD_TOOLS_RE.fullmatch(self.build_tools_version) is None:
            raise ValueError("build_tools_version must be explicit numeric triplet")
        if not isinstance(self.compile_sdk, int) or not 1 <= self.compile_sdk <= 1000:
            raise ValueError("compile_sdk outside bounded range")
        if not isinstance(self.jdk_major, int) or not 8 <= self.jdk_major <= 99:
            raise ValueError("jdk_major outside bounded range")
        try:
            date.fromisoformat(self.observed_on)
        except ValueError as exc:
            raise ValueError("observed_on must be ISO date") from exc
        urls = tuple(sorted(set(self.source_urls)))
        if not urls or len(urls) > 12:
            raise ValueError("toolchain evidence requires bounded official sources")
        for raw in urls:
            parsed = urlparse(raw)
            if parsed.scheme != "https" or parsed.hostname != "developer.android.com":
                raise ValueError("Android build sources must be developer.android.com HTTPS URLs")
        object.__setattr__(self, "source_urls", urls)

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "android_gradle_plugin": self.android_gradle_plugin,
            "gradle_version": self.gradle_version,
            "kotlin_version": self.kotlin_version,
            "compose_bom": self.compose_bom,
            "compile_sdk": self.compile_sdk,
            "build_tools_version": self.build_tools_version,
            "jdk_major": self.jdk_major,
            "observed_on": self.observed_on,
            "source_urls": list(self.source_urls),
        }

    def digest(self) -> str:
        return _sha_bytes(canonical_json_bytes(self.to_dict()))


@dataclass(frozen=True, slots=True)
class AndroidBuildRequest:
    source_workspace_manifest_sha256: str
    application_id: str
    min_sdk: int
    target_sdk: int
    tasks: tuple[AndroidBuildTask, ...] = (
        AndroidBuildTask.UNIT_TEST,
        AndroidBuildTask.APK_DEBUG,
        AndroidBuildTask.AAB_RELEASE,
    )
    timeout_seconds: int = 900
    max_artifact_bytes: int = 2 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        _require_sha(self.source_workspace_manifest_sha256, "source workspace manifest digest")
        if _APP_ID_RE.fullmatch(self.application_id) is None:
            raise ValueError("invalid Android application_id")
        if not (1 <= self.min_sdk <= self.target_sdk <= 1000):
            raise ValueError("invalid min/target SDK range")
        tasks = tuple(sorted(set(self.tasks), key=lambda item: item.value))
        if not tasks or len(tasks) > 3:
            raise ValueError("Android build request requires 1..3 fixed tasks")
        object.__setattr__(self, "tasks", tasks)
        if not 1 <= self.timeout_seconds <= 3600:
            raise ValueError("timeout_seconds outside bounded range")
        if not 1 <= self.max_artifact_bytes <= 20 * 1024 * 1024 * 1024:
            raise ValueError("max_artifact_bytes outside bounded range")

    def argv(self) -> tuple[str, ...]:
        return (
            "--no-daemon",
            "--stacktrace",
            *(task.gradle_task for task in self.tasks),
        )


@dataclass(frozen=True, slots=True)
class AndroidBuildOverlayManifest:
    schema_version: int
    source_workspace_manifest_sha256: str
    toolchain_sha256: str
    files: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_workspace_manifest_sha256": self.source_workspace_manifest_sha256,
            "toolchain_sha256": self.toolchain_sha256,
            "files": [{"path": path, "sha256": digest} for path, digest in self.files],
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class AndroidArtifactEvidence:
    kind: AndroidArtifactKind
    sha256: str
    size_bytes: int
    entry_count: int
    total_uncompressed_bytes: int
    abis: tuple[str, ...]
    required_entries: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "entry_count": self.entry_count,
            "total_uncompressed_bytes": self.total_uncompressed_bytes,
            "abis": list(self.abis),
            "required_entries": list(self.required_entries),
        }


@dataclass(frozen=True, slots=True)
class AndroidBuildEvidence:
    schema_version: int
    source_sha: str
    runner_os: str
    source_workspace_manifest_sha256: str
    overlay_manifest_sha256: str
    toolchain: AndroidBuildToolchainEvidence
    request: AndroidBuildRequest
    status: AndroidBuildStatus
    duration_seconds: float
    artifacts: tuple[AndroidArtifactEvidence, ...]
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_sha):
            raise ValueError("source_sha must be exact lowercase Git SHA")
        if self.runner_os not in {"Linux", "Windows"}:
            raise ValueError("runner_os must be Linux or Windows")
        _require_sha(self.source_workspace_manifest_sha256, "source workspace manifest digest")
        _require_sha(self.overlay_manifest_sha256, "overlay manifest digest")
        if not 0 <= self.duration_seconds <= 7200:
            raise ValueError("duration_seconds outside bounded range")
        blockers = tuple(sorted(set(self.blockers)))
        artifacts = tuple(sorted(self.artifacts, key=lambda item: item.kind.value))
        if self.status is AndroidBuildStatus.PASS:
            if blockers:
                raise ValueError("PASS cannot contain blockers")
            kinds = {item.kind for item in artifacts}
            if kinds != {AndroidArtifactKind.APK, AndroidArtifactKind.AAB}:
                raise ValueError("PASS requires validated APK and AAB evidence")
            if self.request.target_sdk < 36:
                raise ValueError("PASS store-ready fixture requires target SDK 36+")
        elif not blockers:
            raise ValueError("non-PASS Android build evidence requires blockers")
        object.__setattr__(self, "blockers", blockers)
        object.__setattr__(self, "artifacts", artifacts)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "runner_os": self.runner_os,
            "source_workspace_manifest_sha256": self.source_workspace_manifest_sha256,
            "overlay_manifest_sha256": self.overlay_manifest_sha256,
            "toolchain": self.toolchain.to_dict(),
            "request": {
                "application_id": self.request.application_id,
                "min_sdk": self.request.min_sdk,
                "target_sdk": self.request.target_sdk,
                "tasks": [item.value for item in self.request.tasks],
                "timeout_seconds": self.request.timeout_seconds,
                "max_artifact_bytes": self.request.max_artifact_bytes,
            },
            "status": self.status.value,
            "duration_seconds": round(self.duration_seconds, 3),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "blockers": list(self.blockers),
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha_bytes(self.canonical_bytes())


def sanitize_build_environment(source: Mapping[str, str]) -> dict[str, str]:
    for name in source:
        upper = name.upper()
        if upper in _DANGEROUS_ENV or upper.startswith("ORG_GRADLE_PROJECT_"):
            raise ValueError(f"unsafe Android build environment variable: {name}")
    result: dict[str, str] = {}
    for name in sorted(_ALLOWED_ENV):
        value = source.get(name)
        if value is not None:
            if "\x00" in value or len(value) > 4096:
                raise ValueError(f"invalid Android build environment value: {name}")
            result[name] = value
    return result


def verify_source_workspace(root: Path) -> tuple[dict[str, object], str]:
    root = root.resolve(strict=False)
    manifest_path = _inside(root, AndroidScaffoldEngine.MANIFEST_PATH)
    if not manifest_path.is_file():
        raise ValueError("missing R13.3 Android workspace manifest")
    raw_bytes = manifest_path.read_bytes()
    try:
        raw = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid R13.3 Android workspace manifest JSON") from exc
    if raw.get("schema_version") != 1 or not isinstance(raw.get("files"), list):
        raise ValueError("unsupported R13.3 Android workspace manifest")
    seen: set[str] = set()
    for item in raw["files"]:
        if not isinstance(item, dict):
            raise ValueError("invalid workspace manifest file entry")
        relative = _safe_relative(str(item.get("path", "")))
        if relative in seen:
            raise ValueError("duplicate workspace manifest path")
        seen.add(relative)
        expected = str(item.get("sha256", ""))
        _require_sha(expected, "workspace file digest")
        path = _inside(root, relative)
        if not path.is_file() or _sha_bytes(path.read_bytes()) != expected:
            raise ValueError(f"workspace file digest mismatch: {relative}")
    return raw, _sha_bytes(raw_bytes.rstrip(b"\n"))


def prepare_build_staging(
    source_root: Path,
    staging_root: Path,
    toolchain: AndroidBuildToolchainEvidence,
) -> AndroidBuildOverlayManifest:
    source_root = source_root.resolve(strict=False)
    staging_root = staging_root.resolve(strict=False)
    source_manifest, source_manifest_sha = verify_source_workspace(source_root)
    if staging_root == source_root or source_root in staging_root.parents:
        raise ValueError("build staging must be isolated from source workspace")
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True)

    copied: list[str] = []
    for item in source_manifest["files"]:
        relative = _safe_relative(str(item["path"]))
        source = _inside(source_root, relative)
        target = _inside(staging_root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.append(relative)
    source_manifest_target = _inside(staging_root, AndroidScaffoldEngine.MANIFEST_PATH)
    source_manifest_target.parent.mkdir(parents=True, exist_ok=True)
    source_manifest_target.write_bytes(canonical_json_bytes(source_manifest) + b"\n")

    catalog_path = _inside(staging_root, "gradle/libs.versions.toml")
    catalog = catalog_path.read_text(encoding="utf-8")
    catalog = _replace_exact_line(
        catalog, "agp =", f'agp = "{toolchain.android_gradle_plugin}"'
    )
    catalog = _replace_exact_line(
        catalog, "compose-bom =", f'compose-bom = "{toolchain.compose_bom}"'
    )
    lines = catalog.splitlines()
    versions_index = lines.index("[versions]") + 1
    lines.insert(versions_index, f'kotlin = "{toolchain.kotlin_version}"')
    plugins_index = lines.index("[plugins]") + 1
    lines.insert(
        plugins_index,
        'compose-compiler = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }',
    )
    catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    root_build_path = _inside(staging_root, "build.gradle.kts")
    root_build = root_build_path.read_text(encoding="utf-8")
    marker = "    alias(libs.plugins.android.application) apply false\n"
    if root_build.count(marker) != 1:
        raise ValueError("unexpected root Gradle plugin block")
    root_build = root_build.replace(
        marker,
        marker + "    alias(libs.plugins.compose.compiler) apply false\n",
    )
    root_build_path.write_text(root_build, encoding="utf-8", newline="\n")

    app_build_path = _inside(staging_root, "app/build.gradle.kts")
    app_build = app_build_path.read_text(encoding="utf-8")
    plugin_marker = "    alias(libs.plugins.android.application)\n"
    if app_build.count(plugin_marker) != 1:
        raise ValueError("unexpected app Gradle plugin block")
    app_build = app_build.replace(
        plugin_marker,
        plugin_marker + "    alias(libs.plugins.compose.compiler)\n",
    )
    app_build = re.sub(
        r"(?m)^\s*compileSdk\s*=\s*\d+\s*$",
        f"    compileSdk = {toolchain.compile_sdk}",
        app_build,
        count=1,
    )
    app_build_path.write_text(app_build, encoding="utf-8", newline="\n")

    files: list[tuple[str, str]] = []
    for relative in sorted(set(copied)):
        path = _inside(staging_root, relative)
        files.append((relative, _sha_bytes(path.read_bytes())))
    overlay = AndroidBuildOverlayManifest(
        schema_version=1,
        source_workspace_manifest_sha256=source_manifest_sha,
        toolchain_sha256=toolchain.digest(),
        files=tuple(files),
    )
    overlay_path = _inside(staging_root, ".kodepoia/mobile/android/build-overlay-manifest.json")
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_bytes(overlay.canonical_bytes() + b"\n")
    return overlay


def inspect_android_artifact(
    path: Path,
    kind: AndroidArtifactKind,
    *,
    max_bytes: int = 2 * 1024 * 1024 * 1024,
) -> AndroidArtifactEvidence:
    if not path.is_file():
        raise ValueError(f"missing Android {kind.value.upper()} artifact")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes:
        raise ValueError("Android artifact size outside bounded range")
    blob = path.read_bytes()
    names: set[str] = set()
    total_uncompressed = 0
    abis: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if not infos or len(infos) > _MAX_ZIP_ENTRIES:
            raise ValueError("Android artifact entry count outside bounded range")
        for info in infos:
            name = info.filename
            normalized = _safe_relative(name.rstrip("/")) if name.rstrip("/") else None
            if normalized is None:
                continue
            if normalized in names:
                raise ValueError("duplicate Android artifact ZIP path")
            names.add(normalized)
            if info.file_size > _MAX_ENTRY_BYTES:
                raise ValueError("Android artifact contains oversized entry")
            total_uncompressed += info.file_size
            if total_uncompressed > _MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("Android artifact uncompressed size exceeds budget")
            parts = PurePosixPath(normalized).parts
            if kind is AndroidArtifactKind.APK and len(parts) >= 3 and parts[0] == "lib":
                abis.add(parts[1])
            if kind is AndroidArtifactKind.AAB and len(parts) >= 4 and parts[0] == "base" and parts[1] == "lib":
                abis.add(parts[2])

    if kind is AndroidArtifactKind.APK:
        required = ("AndroidManifest.xml", "classes.dex", "resources.arsc")
    else:
        required = (
            "base/manifest/AndroidManifest.xml",
            "base/dex/classes.dex",
            "base/resources.pb",
        )
    missing = [item for item in required if item not in names]
    if missing:
        raise ValueError(f"Android {kind.value.upper()} missing required entries: {missing}")
    return AndroidArtifactEvidence(
        kind=kind,
        sha256=_sha_bytes(blob),
        size_bytes=size,
        entry_count=len(names),
        total_uncompressed_bytes=total_uncompressed,
        abis=tuple(sorted(abis)),
        required_entries=required,
    )


__all__ = [
    "AndroidArtifactEvidence",
    "AndroidArtifactKind",
    "AndroidBuildEvidence",
    "AndroidBuildOverlayManifest",
    "AndroidBuildRequest",
    "AndroidBuildStatus",
    "AndroidBuildTask",
    "AndroidBuildToolchainEvidence",
    "inspect_android_artifact",
    "prepare_build_staging",
    "sanitize_build_environment",
    "verify_source_workspace",
]
