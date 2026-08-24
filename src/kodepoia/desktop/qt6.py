from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult

from .app_model import DesktopAppModel
from .boundary import DesktopBoundaryError, DesktopToolchainBoundary
from .contracts import (
    DesktopArchitecture,
    DesktopCapabilityReport,
    DesktopCapabilityState,
    DesktopFramework,
    DesktopOS,
    DesktopToolKind,
    DesktopToolchainIdentity,
    canonical_sha256,
)

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?")
_STABLE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")


class QtLicenseState(StrEnum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class QtDependencyDeclaration:
    component: str
    version: str
    license_state: QtLicenseState = QtLicenseState.REVIEW_REQUIRED
    redistribution_rights_inferred: bool = False

    def __post_init__(self) -> None:
        if self.component not in {"Qt6::Core", "Qt6::Widgets"}:
            raise ValueError("Qt dependency component is not allowlisted")
        if _VERSION_RE.match(self.version) is None:
            raise ValueError("Qt dependency version is invalid")
        if self.redistribution_rights_inferred:
            raise ValueError("Kodepoia must not infer Qt redistribution rights")

    def canonical(self) -> dict[str, object]:
        return {
            "component": self.component,
            "version": self.version,
            "license_state": self.license_state.value,
            "redistribution_rights_inferred": self.redistribution_rights_inferred,
        }


@dataclass(frozen=True, slots=True)
class QtGeneratedFile:
    path: str
    sha256: str

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith(("/", "\\")) or ".." in Path(self.path).parts:
            raise ValueError("Qt generated file path must be relative and bounded")
        if re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
            raise ValueError("Qt generated file hash must be SHA-256")

    def canonical(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class QtProjectManifest:
    model_sha256: str
    cmake_minimum: str
    cxx_standard: int
    required_components: tuple[str, ...]
    files: tuple[QtGeneratedFile, ...]

    def __post_init__(self) -> None:
        if re.fullmatch(r"[0-9a-f]{64}", self.model_sha256) is None:
            raise ValueError("model_sha256 must be SHA-256")
        if self.cmake_minimum != "3.22":
            raise ValueError("R12.8 fixture CMake minimum is frozen at 3.22")
        if self.cxx_standard != 17:
            raise ValueError("Qt 6 fixture requires C++17")
        components = tuple(sorted(set(self.required_components)))
        if components != ("Core", "Widgets"):
            raise ValueError("R12.8 Qt components are frozen to Core + Widgets")
        ordered = tuple(sorted(self.files, key=lambda item: item.path))
        if len({item.path for item in ordered}) != len(ordered):
            raise ValueError("Qt generated file manifest contains duplicate paths")
        object.__setattr__(self, "required_components", components)
        object.__setattr__(self, "files", ordered)

    def canonical(self) -> dict[str, object]:
        return {
            "model_sha256": self.model_sha256,
            "cmake_minimum": self.cmake_minimum,
            "cxx_standard": self.cxx_standard,
            "required_components": list(self.required_components),
            "files": [item.canonical() for item in self.files],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class QtKitIdentity:
    qt_version: str
    platform: DesktopOS
    architecture: DesktopArchitecture
    generator: str
    cmake_version: str
    cmake_sha256: str
    qtpaths_sha256: str
    compiler_name: str
    compiler_id: str
    compiler_version: str
    compiler_sha256: str
    components: tuple[str, ...]
    license_state: QtLicenseState = QtLicenseState.REVIEW_REQUIRED

    def __post_init__(self) -> None:
        for label, value in (
            ("qt_version", self.qt_version),
            ("cmake_version", self.cmake_version),
            ("compiler_name", self.compiler_name),
            ("compiler_id", self.compiler_id),
            ("compiler_version", self.compiler_version),
        ):
            if not value or len(value) > 128 or "\x00" in value:
                raise ValueError(f"{label} is invalid")
        if self.generator not in {"Visual Studio 17 2022", "Ninja"}:
            raise ValueError("Qt generator is not allowlisted")
        for digest in (self.cmake_sha256, self.qtpaths_sha256, self.compiler_sha256):
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("Qt kit executable digest must be SHA-256")
        components = tuple(sorted(set(self.components)))
        if components != ("Core", "Widgets"):
            raise ValueError("Qt kit components do not match frozen fixture")
        object.__setattr__(self, "components", components)

    def canonical(self) -> dict[str, object]:
        return {
            "qt_version": self.qt_version,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "generator": self.generator,
            "cmake_version": self.cmake_version,
            "cmake_sha256": self.cmake_sha256,
            "qtpaths_sha256": self.qtpaths_sha256,
            "compiler_name": self.compiler_name,
            "compiler_id": self.compiler_id,
            "compiler_version": self.compiler_version,
            "compiler_sha256": self.compiler_sha256,
            "components": list(self.components),
            "license_state": self.license_state.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class QtArtifact:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class QtToolchainDiscovery:
    cmake: Path
    qtpaths: Path
    qt_prefix: Path
    cmake_version: str
    qt_version: str
    report_identity: DesktopToolchainIdentity


@dataclass(frozen=True, slots=True)
class QtAcceptanceResult:
    report: DesktopCapabilityReport
    model_sha256: str
    project_manifest: QtProjectManifest
    kit: QtKitIdentity
    dependencies: tuple[QtDependencyDeclaration, ...]
    configure: SandboxResult
    build: SandboxResult
    runtime: SandboxResult
    artifacts: tuple[QtArtifact, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.report.canonical(),
            "model_sha256": self.model_sha256,
            "project_manifest": self.project_manifest.canonical(),
            "project_manifest_sha256": self.project_manifest.digest(),
            "kit": self.kit.canonical(),
            "kit_sha256": self.kit.digest(),
            "dependencies": [item.canonical() for item in self.dependencies],
            "configure": {"returncode": self.configure.returncode},
            "build": {"returncode": self.build.returncode},
            "runtime": {
                "returncode": self.runtime.returncode,
                "stdout": self.runtime.stdout.strip(),
            },
            "artifacts": [
                {"path": item.path, "size": item.size, "sha256": item.sha256}
                for item in self.artifacts
            ],
        }


class Qt6Adapter:
    ADAPTER_ID = "adapter.qt6"
    CMAKE_MINIMUM = (3, 22, 0)
    QT_MINIMUM = (6, 5, 0)
    ACCEPTANCE_QT_VERSION = "6.11.2"
    COMPONENTS = ("Core", "Widgets")
    SENTINEL = "KODEPOIA_QT6_RUNTIME_PASS"
    _WINDOWS_MACHINE_ENV = (
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "PROGRAMDATA",
    )

    def __init__(self, project_root: Path, staging_root: Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.staging_root = Path(staging_root).resolve(strict=False)
        self.last_diagnostic = ""

    @staticmethod
    def current_os() -> DesktopOS | None:
        system = platform.system()
        if system == "Windows":
            return DesktopOS.WINDOWS
        if system == "Linux":
            return DesktopOS.LINUX
        if system == "Darwin":
            return DesktopOS.MACOS
        return None

    @staticmethod
    def current_arch() -> DesktopArchitecture:
        machine = platform.machine().lower()
        if machine in {"arm64", "aarch64"}:
            return DesktopArchitecture.ARM64
        if machine in {"amd64", "x86_64"}:
            return DesktopArchitecture.X64
        return DesktopArchitecture.X86

    @staticmethod
    def _sha(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        match = _VERSION_RE.match(value.strip())
        if match is None:
            return (0, 0, 0)
        return tuple(int(part or 0) for part in match.groups())  # type: ignore[return-value]

    @classmethod
    def _tool_env(cls) -> dict[str, str]:
        if platform.system() != "Windows":
            return {}
        return {
            key: value
            for key in cls._WINDOWS_MACHINE_ENV
            if (value := os.environ.get(key))
        }

    def _failure(
        self,
        identity: DesktopToolchainIdentity | None,
        blocker: str,
        result: SandboxResult | None = None,
        *,
        state: DesktopCapabilityState = DesktopCapabilityState.FAILED,
    ) -> DesktopCapabilityReport:
        if result is not None:
            text = (result.stdout + "\n" + result.stderr).replace("\x00", "").strip()
            self.last_diagnostic = text[-12000:]
        return DesktopCapabilityReport(
            self.ADAPTER_ID,
            state,
            toolchain=identity,
            blockers=(blocker,),
        )

    def discover_toolchain(self) -> QtToolchainDiscovery | DesktopCapabilityReport:
        current = self.current_os()
        if current is None:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("desktop_os_unsupported",),
            )
        cmake_raw = shutil.which("cmake")
        qtpaths_raw = shutil.which("qtpaths6") or shutil.which("qtpaths")
        if not cmake_raw:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNAVAILABLE,
                blockers=("cmake_missing",),
            )
        if not qtpaths_raw:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNAVAILABLE,
                blockers=("qtpaths_missing",),
            )
        cmake = Path(cmake_raw).resolve(strict=True)
        qtpaths = Path(qtpaths_raw).resolve(strict=True)
        roots = (cmake.parent, cmake.parent.parent, qtpaths.parent, qtpaths.parent.parent)
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=roots,
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        cmake = boundary.validate_executable(DesktopToolKind.CMAKE, cmake)
        qtpaths = boundary.validate_executable(DesktopToolKind.QT_PATHS, qtpaths)
        env = self._tool_env()
        cmake_probe = ProcessSandbox(self.project_root, {cmake.name}).run(
            boundary.build_probe_argv(DesktopToolKind.CMAKE, cmake),
            cwd=self.project_root,
            timeout=30,
            env=env,
        )
        if cmake_probe.returncode != 0:
            return self._failure(None, "cmake_probe_failed", cmake_probe)
        cmake_line = next((line.strip() for line in cmake_probe.stdout.splitlines() if "cmake version" in line.lower()), "")
        cmake_version = cmake_line.rsplit(" ", 1)[-1] if cmake_line else ""
        if self._version_tuple(cmake_version) < self.CMAKE_MINIMUM:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("cmake_3_22_required",),
            )
        qt_probe = ProcessSandbox(self.project_root, {qtpaths.name}).run(
            boundary.build_probe_argv(DesktopToolKind.QT_PATHS, qtpaths),
            cwd=self.project_root,
            timeout=30,
            env=env,
        )
        qt_version = qt_probe.stdout.strip()
        if qt_probe.returncode != 0 or not qt_version:
            return self._failure(None, "qt_version_probe_failed", qt_probe)
        if self._version_tuple(qt_version) < self.QT_MINIMUM or self._version_tuple(qt_version)[0] != 6:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("supported_qt6_required",),
            )
        prefix_probe = ProcessSandbox(self.project_root, {qtpaths.name}).run(
            (str(qtpaths), "--query", "QT_INSTALL_PREFIX"),
            cwd=self.project_root,
            timeout=30,
            env=env,
        )
        if prefix_probe.returncode != 0 or not prefix_probe.stdout.strip():
            return self._failure(None, "qt_prefix_probe_failed", prefix_probe)
        try:
            qt_prefix = Path(prefix_probe.stdout.strip()).resolve(strict=True)
        except OSError:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                blockers=("qt_prefix_invalid",),
            )
        if not qt_prefix.is_dir() or (qtpaths != qt_prefix and qt_prefix not in qtpaths.parents):
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                blockers=("qt_prefix_mismatch",),
            )
        report_identity = DesktopToolchainIdentity(
            DesktopToolKind.QT_PATHS,
            qtpaths.name,
            self._sha(qtpaths),
            qt_version,
            current,
            self.current_arch(),
            ("cmake_ready", "qt6_core", "qt6_widgets"),
        )
        return QtToolchainDiscovery(cmake, qtpaths, qt_prefix, cmake_version, qt_version, report_identity)

    def _generator_args(self, current: DesktopOS) -> tuple[str, ...]:
        if current is DesktopOS.WINDOWS:
            if self.current_arch() is not DesktopArchitecture.X64:
                raise DesktopBoundaryError("R12.8 hosted Windows acceptance is x64 only")
            return ("-G", "Visual Studio 17 2022", "-A", "x64")
        return ("-G", "Ninja")

    def fixture_root(self) -> Path:
        return self.project_root / ".kodepoia" / "fixtures" / "qt6"

    def render_fixture(self, model: DesktopAppModel) -> tuple[Path, QtProjectManifest, str]:
        model.validate()
        model_sha = model.conformance_projection(DesktopFramework.QT6).logical_model_sha256
        root = self.fixture_root()
        root.mkdir(parents=True, exist_ok=True)
        cmake = root / "CMakeLists.txt"
        source = root / "main.cpp"
        resource = root / "model.txt"
        cmake.write_text(
            "cmake_minimum_required(VERSION 3.22)\n"
            "project(KodepoiaQtFixture LANGUAGES CXX)\n"
            "set(CMAKE_CXX_STANDARD 17)\n"
            "set(CMAKE_CXX_STANDARD_REQUIRED ON)\n"
            "set(CMAKE_CXX_EXTENSIONS OFF)\n"
            "find_package(Qt6 6.5 REQUIRED COMPONENTS Core Widgets)\n"
            "qt_standard_project_setup(REQUIRES 6.5)\n"
            "qt_add_executable(KodepoiaQtFixture main.cpp)\n"
            "qt_add_resources(KodepoiaQtFixture kodepoia_resources PREFIX / FILES model.txt)\n"
            "target_link_libraries(KodepoiaQtFixture PRIVATE Qt6::Core Qt6::Widgets)\n"
            "file(WRITE \"${CMAKE_BINARY_DIR}/kodepoia-toolchain.txt\" "
            "\"compiler_path=${CMAKE_CXX_COMPILER}\\ncompiler_id=${CMAKE_CXX_COMPILER_ID}\\n"
            "compiler_version=${CMAKE_CXX_COMPILER_VERSION}\\nqt_version=${Qt6_VERSION}\\n\")\n",
            encoding="utf-8",
            newline="\n",
        )
        source.write_text(
            "#include <QCoreApplication>\n"
            "#include <QFile>\n"
            "#include <QWidget>\n"
            "#include <QtCore/qglobal.h>\n"
            "#include <iostream>\n"
            "#include <string>\n"
            "int main(int argc, char **argv) {\n"
            "  QCoreApplication app(argc, argv);\n"
            "  if (std::string(QWidget::staticMetaObject.className()) != \"QWidget\") return 41;\n"
            "  QFile model(\":/model.txt\");\n"
            "  if (!model.open(QIODevice::ReadOnly)) return 42;\n"
            f"  if (model.readAll().trimmed() != QByteArrayLiteral(\"{model_sha}\")) return 43;\n"
            f"  std::cout << \"{self.SENTINEL}:{model_sha}:\" << QT_VERSION_STR << std::endl;\n"
            "  return 0;\n"
            "}\n",
            encoding="utf-8",
            newline="\n",
        )
        resource.write_text(model_sha + "\n", encoding="utf-8", newline="\n")
        files = tuple(
            QtGeneratedFile(path.name, self._sha(path))
            for path in (cmake, source, resource)
        )
        manifest = QtProjectManifest(
            model_sha,
            "3.22",
            17,
            self.COMPONENTS,
            files,
        )
        return cmake, manifest, model_sha

    def _configure_argv(self, discovery: QtToolchainDiscovery, source_root: Path, build_root: Path) -> tuple[str, ...]:
        source = source_root.resolve(strict=True)
        project = self.project_root
        if source != project and project not in source.parents:
            raise DesktopBoundaryError("Qt source root escapes project root")
        build = build_root.resolve(strict=False)
        if build != self.staging_root and self.staging_root not in build.parents:
            raise DesktopBoundaryError("Qt build root escapes staging root")
        prefix = discovery.qt_prefix.resolve(strict=True)
        return (
            str(discovery.cmake),
            "-S",
            str(source),
            "-B",
            str(build),
            *self._generator_args(discovery.report_identity.platform),
            f"-DQt6_ROOT={prefix}",
        )

    @staticmethod
    def _parse_toolchain_file(path: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            if "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            if key in {"compiler_path", "compiler_id", "compiler_version", "qt_version"}:
                values[key] = value.strip()
        required = {"compiler_path", "compiler_id", "compiler_version", "qt_version"}
        if set(values) != required:
            raise ValueError("CMake toolchain metadata is incomplete")
        if any("\x00" in value or len(value) > 4096 for value in values.values()):
            raise ValueError("CMake toolchain metadata is invalid")
        return values

    def _build_kit_identity(
        self,
        discovery: QtToolchainDiscovery,
        build_root: Path,
    ) -> QtKitIdentity:
        metadata_path = build_root / "kodepoia-toolchain.txt"
        if not metadata_path.is_file():
            raise ValueError("CMake did not emit toolchain identity")
        metadata = self._parse_toolchain_file(metadata_path)
        if metadata["qt_version"] != discovery.qt_version:
            raise ValueError("configured Qt version differs from probed Qt version")
        compiler = Path(metadata["compiler_path"]).resolve(strict=True)
        if not compiler.is_file():
            raise ValueError("configured C++ compiler is unavailable")
        if not _STABLE_TOKEN_RE.fullmatch(metadata["compiler_id"]):
            raise ValueError("compiler id is not stable")
        generator = "Visual Studio 17 2022" if discovery.report_identity.platform is DesktopOS.WINDOWS else "Ninja"
        return QtKitIdentity(
            qt_version=discovery.qt_version,
            platform=discovery.report_identity.platform,
            architecture=discovery.report_identity.architecture,
            generator=generator,
            cmake_version=discovery.cmake_version,
            cmake_sha256=self._sha(discovery.cmake),
            qtpaths_sha256=self._sha(discovery.qtpaths),
            compiler_name=compiler.name,
            compiler_id=metadata["compiler_id"],
            compiler_version=metadata["compiler_version"],
            compiler_sha256=self._sha(compiler),
            components=self.COMPONENTS,
        )

    def _runtime_executable(self, build_root: Path, current: DesktopOS) -> Path | None:
        expected = "KodepoiaQtFixture.exe" if current is DesktopOS.WINDOWS else "KodepoiaQtFixture"
        candidates = sorted(path for path in build_root.rglob(expected) if path.is_file())
        return candidates[0] if len(candidates) == 1 else None

    def run_acceptance(self, model: DesktopAppModel) -> QtAcceptanceResult | DesktopCapabilityReport:
        discovered = self.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport):
            return discovered
        cmake_file, manifest, model_sha = self.render_fixture(model)
        build_root = self.staging_root / discovered.report_identity.platform.value / "build"
        build_root.mkdir(parents=True, exist_ok=True)
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(
                discovered.cmake.parent,
                discovered.cmake.parent.parent,
                discovered.qtpaths.parent,
                discovered.qtpaths.parent.parent,
            ),
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        env = self._tool_env()
        sandbox = ProcessSandbox(self.project_root, {discovered.cmake.name})
        configure = sandbox.run(
            self._configure_argv(discovered, cmake_file.parent, build_root),
            cwd=self.project_root,
            timeout=300,
            env=env,
        )
        if configure.returncode != 0:
            return self._failure(discovered.report_identity, "qt_cmake_configure_failed", configure)
        try:
            kit = self._build_kit_identity(discovered, build_root)
        except (OSError, ValueError) as exc:
            self.last_diagnostic = str(exc)
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                toolchain=discovered.report_identity,
                blockers=("qt_kit_identity_failed",),
            )
        build = sandbox.run(
            boundary.build_cmake_build_argv(
                discovered.cmake,
                build_directory=build_root,
                configuration="Release",
            ),
            cwd=self.project_root,
            timeout=300,
            env=env,
        )
        if build.returncode != 0:
            return self._failure(discovered.report_identity, "qt_cmake_build_failed", build)
        executable = self._runtime_executable(build_root, discovered.report_identity.platform)
        if executable is None:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                toolchain=discovered.report_identity,
                blockers=("qt_runtime_artifact_missing",),
            )
        runtime = ProcessSandbox(self.project_root, {executable.name}).run(
            (str(executable),),
            cwd=self.project_root,
            timeout=60,
            env=env,
        )
        expected = f"{self.SENTINEL}:{model_sha}:{discovered.qt_version}"
        if runtime.returncode != 0 or expected not in runtime.stdout:
            return self._failure(discovered.report_identity, "qt_runtime_probe_failed", runtime)
        dependencies = tuple(
            QtDependencyDeclaration(f"Qt6::{component}", discovered.qt_version)
            for component in self.COMPONENTS
        )
        artifacts = tuple(
            QtArtifact(path.relative_to(self.staging_root).as_posix(), path.stat().st_size, self._sha(path))
            for path in sorted(item for item in build_root.rglob("*") if item.is_file())
        )
        report = DesktopCapabilityReport(
            self.ADAPTER_ID,
            DesktopCapabilityState.AVAILABLE,
            toolchain=discovered.report_identity,
            capabilities=(
                "build_ready",
                "cmake_ready",
                "compiler_identity_ready",
                "license_review_required",
                "qt6_core",
                "qt6_widgets",
                "runtime_probe_ready",
            ),
        )
        return QtAcceptanceResult(
            report,
            model_sha,
            manifest,
            kit,
            dependencies,
            configure,
            build,
            runtime,
            artifacts,
        )


def write_qt_acceptance_report(result: QtAcceptanceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
