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
from .boundary import DesktopToolchainBoundary
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

_PACKAGE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{2,49}$")
_PUBLISHER = re.compile(r"^CN=[A-Za-z0-9 ._-]{1,64}$")
_VERSION = re.compile(r"^(?:0|[1-9][0-9]{0,4})(?:\.(?:0|[1-9][0-9]{0,4})){3}$")


class WinUiDeploymentMode(StrEnum):
    PACKAGED_MSIX = "packaged_msix"
    UNPACKAGED_FRAMEWORK_DEPENDENT = "unpackaged_framework_dependent"
    UNPACKAGED_SELF_CONTAINED = "unpackaged_self_contained"


@dataclass(frozen=True, slots=True)
class WinUiDeploymentContract:
    package_name: str
    publisher: str
    version: str
    mode: WinUiDeploymentMode
    min_windows_build: int = 17763

    def __post_init__(self) -> None:
        if _PACKAGE_NAME.fullmatch(self.package_name) is None:
            raise ValueError("invalid WinUI package name")
        if _PUBLISHER.fullmatch(self.publisher) is None:
            raise ValueError("invalid WinUI publisher")
        if _VERSION.fullmatch(self.version) is None:
            raise ValueError("invalid four-part WinUI package version")
        if self.min_windows_build < 17763:
            raise ValueError("WinUI 3 requires Windows 10 build 17763 or later")

    def canonical(self) -> dict[str, object]:
        return {
            "package_name": self.package_name,
            "publisher": self.publisher,
            "version": self.version,
            "mode": self.mode.value,
            "min_windows_build": self.min_windows_build,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class WinUiArtifact:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class WinUiAcceptanceResult:
    report: DesktopCapabilityReport
    model_sha256: str
    deployment_sha256: str
    windows_app_sdk_version: str
    template_probe: SandboxResult
    build: SandboxResult
    runtime: SandboxResult
    artifacts: tuple[WinUiArtifact, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.report.canonical(),
            "model_sha256": self.model_sha256,
            "deployment_sha256": self.deployment_sha256,
            "windows_app_sdk_version": self.windows_app_sdk_version,
            "template_probe": {"returncode": self.template_probe.returncode},
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


class WinUi3Adapter:
    ADAPTER_ID = "adapter.winui3"
    TARGET = "net10.0-windows10.0.26100.0"
    WINDOWS_APP_SDK_VERSION = "1.8.260804001"
    SENTINEL = "KODEPOIA_WINUI3_RUNTIME_PASS"
    _WINDOWS_MACHINE_ENV = (
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "PROGRAMDATA",
    )

    def __init__(self, project_root: Path, staging_root: Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.staging_root = Path(staging_root).resolve(strict=False)
        self.fixture_root = self.project_root / ".kodepoia" / "fixtures" / "winui3"
        self.last_diagnostic = ""

    @classmethod
    def _dotnet_env(cls) -> dict[str, str]:
        return {
            key: value
            for key in cls._WINDOWS_MACHINE_ENV
            if (value := os.environ.get(key))
        }

    @staticmethod
    def _sha(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _arch() -> DesktopArchitecture:
        machine = platform.machine().lower()
        if machine in {"arm64", "aarch64"}:
            return DesktopArchitecture.ARM64
        if machine in {"amd64", "x86_64"}:
            return DesktopArchitecture.X64
        return DesktopArchitecture.X86

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
            self.last_diagnostic = text[-8000:]
        return DesktopCapabilityReport(
            self.ADAPTER_ID,
            state,
            toolchain=identity,
            blockers=(blocker,),
        )

    def discover_toolchain(
        self,
    ) -> tuple[Path, DesktopToolchainIdentity, SandboxResult] | DesktopCapabilityReport:
        if platform.system() != "Windows":
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("windows_required",),
            )
        found = shutil.which("dotnet")
        if not found:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNAVAILABLE,
                blockers=("dotnet_missing",),
            )
        dotnet = Path(found).resolve(strict=True)
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent),
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        sandbox = ProcessSandbox(self.project_root, {dotnet.name})
        env = self._dotnet_env()
        probe = sandbox.run(
            boundary.build_probe_argv(DesktopToolKind.DOTNET, dotnet),
            cwd=self.project_root,
            timeout=30,
            env=env,
        )
        version = probe.stdout.strip()
        if probe.returncode != 0 or not version:
            return self._failure(None, "dotnet_probe_failed", probe)
        try:
            major = int(version.split(".", 1)[0])
        except ValueError:
            major = 0
        if major < 10:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("dotnet_10_required",),
            )
        identity = DesktopToolchainIdentity(
            DesktopToolKind.DOTNET,
            dotnet.name,
            self._sha(dotnet),
            version,
            DesktopOS.WINDOWS,
            self._arch(),
            ("dotnet_sdk", "winui_template_probe", "windows_app_sdk_restore"),
        )
        template_probe = sandbox.run(
            (str(dotnet), "new", "list", "winui", "--columns-all"),
            cwd=self.project_root,
            timeout=60,
            env=env,
        )
        text = (template_probe.stdout + "\n" + template_probe.stderr).lower()
        if template_probe.returncode != 0 or "winui" not in text:
            return self._failure(
                identity,
                "winui_template_missing",
                template_probe,
                state=DesktopCapabilityState.UNAVAILABLE,
            )
        return dotnet, identity, template_probe

    def render_fixture(
        self,
        model: DesktopAppModel,
        deployment: WinUiDeploymentContract,
    ) -> tuple[Path, Path, Path, str]:
        model.validate()
        if deployment.mode is not WinUiDeploymentMode.UNPACKAGED_SELF_CONTAINED:
            raise ValueError("R12.6 runtime fixture requires unpackaged self-contained mode")
        model_sha = model.conformance_projection(DesktopFramework.WINUI3).logical_model_sha256
        app_dir = self.fixture_root / "App"
        probe_dir = self.fixture_root / "RuntimeProbe"
        app_dir.mkdir(parents=True, exist_ok=True)
        probe_dir.mkdir(parents=True, exist_ok=True)
        output = str(self.staging_root)
        common = (
            f"<TargetFramework>{self.TARGET}</TargetFramework>"
            "<Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>"
            "<Deterministic>true</Deterministic><ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>"
            "<RuntimeIdentifier>win-x64</RuntimeIdentifier>"
            "<WindowsPackageType>None</WindowsPackageType>"
            "<WindowsAppSDKSelfContained>true</WindowsAppSDKSelfContained>"
        )
        package = (
            f'<PackageReference Include="Microsoft.WindowsAppSDK" Version="{self.WINDOWS_APP_SDK_VERSION}" />'
        )
        app_project = app_dir / "KodepoiaWinUiFixture.csproj"
        app_project.write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
            '<OutputType>WinExe</OutputType>' + common + '<UseWinUI>true</UseWinUI>'
            f'<BaseOutputPath>{output}\\app\\</BaseOutputPath>'
            f'<BaseIntermediateOutputPath>{output}\\obj-app\\</BaseIntermediateOutputPath>'
            '</PropertyGroup><ItemGroup>' + package + '</ItemGroup></Project>\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "App.xaml").write_text(
            '<Application x:Class="KodepoiaWinUiFixture.App" '
            'xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" '
            'xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"/>\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "App.xaml.cs").write_text(
            'using Microsoft.UI.Xaml; namespace KodepoiaWinUiFixture; '
            'public partial class App : Application { protected override void OnLaunched(LaunchActivatedEventArgs args) '
            '{ var window = new MainWindow(); window.Activate(); } }\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "MainWindow.xaml").write_text(
            '<Window x:Class="KodepoiaWinUiFixture.MainWindow" '
            'xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" '
            'xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">'
            f'<TextBlock Text="{model_sha}"/></Window>\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "MainWindow.xaml.cs").write_text(
            f'using Microsoft.UI.Xaml; namespace KodepoiaWinUiFixture; public sealed partial class MainWindow : Window '
            f'{{ public const string ModelSha = "{model_sha}"; public MainWindow() {{ InitializeComponent(); Title = "Kodepoia"; }} }}\n',
            encoding="utf-8",
            newline="\n",
        )
        manifest = app_dir / "Package.appxmanifest"
        manifest.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10">'
            f'<Identity Name="{deployment.package_name}" Publisher="{deployment.publisher}" Version="{deployment.version}"/>'
            '<Properties><DisplayName>Kodepoia WinUI Fixture</DisplayName><PublisherDisplayName>Kodepoia</PublisherDisplayName>'
            '<Logo>Assets\\StoreLogo.png</Logo></Properties>'
            '<Dependencies><TargetDeviceFamily Name="Windows.Desktop" '
            f'MinVersion="10.0.{deployment.min_windows_build}.0" MaxVersionTested="10.0.26100.0"/></Dependencies>'
            '</Package>\n',
            encoding="utf-8",
            newline="\n",
        )
        probe_project = probe_dir / "KodepoiaWinUiRuntimeProbe.csproj"
        probe_project.write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
            + common
            + f'<BaseOutputPath>{output}\\probe\\</BaseOutputPath>'
            + f'<BaseIntermediateOutputPath>{output}\\obj-probe\\</BaseIntermediateOutputPath>'
            + '</PropertyGroup><ItemGroup>' + package + '</ItemGroup></Project>\n',
            encoding="utf-8",
            newline="\n",
        )
        (probe_dir / "Program.cs").write_text(
            'using System; using System.Reflection; internal static class Program { public static int Main() {'
            'var asm = Assembly.Load("Microsoft.WinUI"); '
            'if (asm.GetType("Microsoft.UI.Xaml.Application") is null) return 21; '
            'if (asm.GetType("Microsoft.UI.Xaml.Window") is null) return 22; '
            f'Console.WriteLine("{self.SENTINEL}:{model_sha}"); return 0; }} }}\n',
            encoding="utf-8",
            newline="\n",
        )
        return app_project, probe_project, manifest, model_sha

    def run_acceptance(
        self,
        model: DesktopAppModel,
        deployment: WinUiDeploymentContract,
    ) -> WinUiAcceptanceResult | DesktopCapabilityReport:
        discovered = self.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport):
            return discovered
        dotnet, identity, template_probe = discovered
        app, probe, manifest, model_sha = self.render_fixture(model, deployment)
        if not manifest.is_file() or deployment.package_name not in manifest.read_text(encoding="utf-8"):
            return self._failure(identity, "manifest_validation_failed")
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent),
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        sandbox = ProcessSandbox(self.project_root, {dotnet.name})
        env = self._dotnet_env()
        for project in (app, probe):
            project = boundary.validate_project_file(project, suffixes=frozenset({".csproj"}))
            restore = sandbox.run(
                (str(dotnet), "restore", str(project), "--nologo"),
                cwd=self.project_root,
                timeout=240,
                env=env,
            )
            if restore.returncode != 0:
                return self._failure(identity, "windows_app_sdk_restore_failed", restore)
        build = sandbox.run(
            boundary.build_dotnet_argv(
                dotnet,
                operation="build",
                project_file=app,
                configuration="Release",
            ),
            cwd=self.project_root,
            timeout=300,
            env=env,
        )
        if build.returncode != 0:
            return self._failure(identity, "winui_build_failed", build)
        probe_build = sandbox.run(
            boundary.build_dotnet_argv(
                dotnet,
                operation="build",
                project_file=probe,
                configuration="Release",
            ),
            cwd=self.project_root,
            timeout=300,
            env=env,
        )
        if probe_build.returncode != 0:
            return self._failure(identity, "runtime_probe_build_failed", probe_build)
        dll = boundary.validate_staging_path(
            self.staging_root / "probe" / "Release" / self.TARGET / "win-x64" / "KodepoiaWinUiRuntimeProbe.dll"
        )
        if not dll.is_file():
            return self._failure(identity, "runtime_probe_artifact_missing")
        runtime = sandbox.run(
            (str(dotnet), str(dll)),
            cwd=self.project_root,
            timeout=60,
            env=env,
        )
        if runtime.returncode != 0 or f"{self.SENTINEL}:{model_sha}" not in runtime.stdout:
            return self._failure(identity, "winui_runtime_probe_failed", runtime)
        artifacts = tuple(
            WinUiArtifact(path.relative_to(self.staging_root).as_posix(), path.stat().st_size, self._sha(path))
            for path in sorted(item for item in self.staging_root.rglob("*") if item.is_file())
        )
        report = DesktopCapabilityReport(
            self.ADAPTER_ID,
            DesktopCapabilityState.AVAILABLE,
            toolchain=identity,
            capabilities=(
                "build_ready",
                "deployment_metadata_ready",
                "runtime_smoke_ready",
                "template_ready",
                "windows_app_sdk_1_8",
                "windows_only",
            ),
        )
        return WinUiAcceptanceResult(
            report,
            model_sha,
            deployment.digest(),
            self.WINDOWS_APP_SDK_VERSION,
            template_probe,
            build,
            runtime,
            artifacts,
        )


def canonical_winui_deployment() -> WinUiDeploymentContract:
    return WinUiDeploymentContract(
        package_name="Kodepoia.WinUI3.Fixture",
        publisher="CN=Kodepoia",
        version="1.0.0.0",
        mode=WinUiDeploymentMode.UNPACKAGED_SELF_CONTAINED,
        min_windows_build=17763,
    )


def write_winui_acceptance_report(result: WinUiAcceptanceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
