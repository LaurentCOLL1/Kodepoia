from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from .contracts import MobileToolKind

_ALLOWED_TOOL_NAMES: dict[MobileToolKind, frozenset[str]] = {
    MobileToolKind.JAVA: frozenset({"java", "java.exe"}),
    MobileToolKind.GRADLE: frozenset({"gradle", "gradle.bat", "gradle.cmd"}),
    MobileToolKind.ADB: frozenset({"adb", "adb.exe"}),
    MobileToolKind.SDKMANAGER: frozenset({"sdkmanager", "sdkmanager.bat"}),
    MobileToolKind.APKSIGNER: frozenset({"apksigner", "apksigner.bat"}),
    MobileToolKind.KEYTOOL: frozenset({"keytool", "keytool.exe"}),
    MobileToolKind.BUNDLETOOL: frozenset({"bundletool.jar"}),
    MobileToolKind.XCODEBUILD: frozenset({"xcodebuild"}),
    MobileToolKind.XCRUN: frozenset({"xcrun"}),
}

_GENERIC_ENV_KEYS = frozenset({"KODEPOIA_RUN_ID", "TEMP", "TMP"})
_PATH_ENV_KEYS = frozenset(
    {"JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "GRADLE_USER_HOME", "DEVELOPER_DIR"}
)
_MAX_ENV_VALUE = 4096


class MobileBoundaryError(ValueError):
    pass


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


class MobileToolchainBoundary:
    """R13.1 path/tool validation and typed argv construction; never launches a process."""

    def __init__(
        self,
        *,
        allowed_runtime_roots: Iterable[Path],
        project_root: Path,
        staging_root: Path,
    ) -> None:
        roots = tuple(Path(item).resolve(strict=False) for item in allowed_runtime_roots)
        if not roots:
            raise ValueError("at least one mobile runtime root is required")
        self.allowed_runtime_roots = roots
        self.project_root = Path(project_root).resolve(strict=False)
        self.staging_root = Path(staging_root).resolve(strict=False)

    def _allowed_path_root(self, path: Path) -> bool:
        return any(_within(path, root) for root in self.allowed_runtime_roots) or _within(
            path, self.staging_root
        )

    def validate_tool(self, kind: MobileToolKind, candidate: Path) -> Path:
        try:
            resolved = Path(candidate).resolve(strict=True)
        except OSError as exc:
            raise MobileBoundaryError(f"mobile tool is unavailable: {candidate}") from exc
        if not resolved.is_file():
            raise MobileBoundaryError("mobile tool must be a regular file")
        if resolved.name.casefold() not in _ALLOWED_TOOL_NAMES[kind]:
            raise MobileBoundaryError(f"unexpected tool for {kind.value}: {resolved.name}")
        if not any(_within(resolved, root) for root in self.allowed_runtime_roots):
            raise MobileBoundaryError("mobile tool escapes configured runtime roots")
        if kind is MobileToolKind.BUNDLETOOL and resolved.suffix.casefold() != ".jar":
            raise MobileBoundaryError("bundletool must be a repository-approved jar identity")
        return resolved

    def validate_project_file(
        self,
        path: Path,
        *,
        names: frozenset[str] = frozenset(),
        suffixes: frozenset[str] = frozenset(),
    ) -> Path:
        try:
            resolved = Path(path).resolve(strict=True)
        except OSError as exc:
            raise MobileBoundaryError("mobile project input is unavailable") from exc
        if not resolved.is_file() or not _within(resolved, self.project_root):
            raise MobileBoundaryError("mobile project input escapes project root")
        if names and resolved.name not in names:
            raise MobileBoundaryError("mobile project input name is not allowlisted")
        if suffixes and resolved.suffix.casefold() not in suffixes:
            raise MobileBoundaryError("mobile project input suffix is not allowlisted")
        return resolved

    def validate_staging_path(self, path: Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        if not _within(resolved, self.staging_root):
            raise MobileBoundaryError("mobile output escapes staging root")
        return resolved

    def validate_environment_overrides(
        self,
        overrides: Mapping[str, str] | None,
    ) -> dict[str, str]:
        if not overrides:
            return {}
        clean: dict[str, str] = {}
        for raw_key, raw_value in overrides.items():
            key = str(raw_key).upper()
            value = str(raw_value)
            if key not in _GENERIC_ENV_KEYS | _PATH_ENV_KEYS:
                raise MobileBoundaryError(f"environment override is not allowlisted: {raw_key}")
            if "\x00" in value or len(value) > _MAX_ENV_VALUE:
                raise MobileBoundaryError("environment value is invalid or too large")
            if key in _PATH_ENV_KEYS:
                resolved = Path(value).resolve(strict=False)
                if not self._allowed_path_root(resolved):
                    raise MobileBoundaryError(f"environment path escapes allowed roots: {key}")
                value = str(resolved)
            clean[key] = value
        return clean

    def build_probe_argv(
        self,
        kind: MobileToolKind,
        candidate: Path,
    ) -> tuple[str, ...]:
        tool = self.validate_tool(kind, candidate)
        if kind is MobileToolKind.JAVA:
            return (str(tool), "-version")
        if kind is MobileToolKind.GRADLE:
            return (str(tool), "--version")
        if kind is MobileToolKind.ADB:
            return (str(tool), "version")
        if kind is MobileToolKind.SDKMANAGER:
            return (str(tool), "--version")
        if kind is MobileToolKind.APKSIGNER:
            return (str(tool), "version")
        if kind is MobileToolKind.KEYTOOL:
            return (str(tool), "-help")
        if kind is MobileToolKind.XCODEBUILD:
            return (str(tool), "-version")
        if kind is MobileToolKind.XCRUN:
            return (str(tool), "--find", "xcodebuild")
        raise MobileBoundaryError("bundletool probe requires a validated Java tool")

    def build_bundletool_probe_argv(
        self,
        *,
        java: Path,
        bundletool_jar: Path,
    ) -> tuple[str, ...]:
        java_tool = self.validate_tool(MobileToolKind.JAVA, java)
        bundletool = self.validate_tool(MobileToolKind.BUNDLETOOL, bundletool_jar)
        return (str(java_tool), "-jar", str(bundletool), "version")

    def build_gradle_task_argv(
        self,
        gradle: Path,
        *,
        project_directory: Path,
        task: str,
    ) -> tuple[str, ...]:
        if task not in {
            "assembleDebug",
            "assembleRelease",
            "bundleRelease",
            "testDebugUnitTest",
            "lintDebug",
        }:
            raise MobileBoundaryError("Gradle task is not allowlisted")
        tool = self.validate_tool(MobileToolKind.GRADLE, gradle)
        project = Path(project_directory).resolve(strict=True)
        if not project.is_dir() or not _within(project, self.project_root):
            raise MobileBoundaryError("Gradle project directory escapes project root")
        return (
            str(tool),
            "--no-daemon",
            "--offline",
            "--console=plain",
            "-p",
            str(project),
            task,
        )

    def build_adb_devices_argv(self, adb: Path) -> tuple[str, ...]:
        tool = self.validate_tool(MobileToolKind.ADB, adb)
        return (str(tool), "devices", "-l")

    def build_xcodebuild_list_argv(
        self,
        xcodebuild: Path,
        *,
        project_file: Path,
    ) -> tuple[str, ...]:
        tool = self.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild)
        project = self.validate_project_file(
            project_file,
            suffixes=frozenset({".xcodeproj", ".xcworkspace"}),
        )
        selector = "-workspace" if project.suffix == ".xcworkspace" else "-project"
        return (str(tool), selector, str(project), "-list", "-json")

    def build_xcrun_simctl_list_argv(self, xcrun: Path) -> tuple[str, ...]:
        tool = self.validate_tool(MobileToolKind.XCRUN, xcrun)
        return (str(tool), "simctl", "list", "devices", "--json")
