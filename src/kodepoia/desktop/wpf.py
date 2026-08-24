from __future__ import annotations

import hashlib
import json
import platform
import shutil
from dataclasses import dataclass
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
)


@dataclass(frozen=True, slots=True)
class WpfArtifact:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class WpfAcceptanceResult:
    report: DesktopCapabilityReport
    model_sha256: str
    build: SandboxResult
    test: SandboxResult
    artifacts: tuple[WpfArtifact, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.report.canonical(),
            "model_sha256": self.model_sha256,
            "build": {
                "returncode": self.build.returncode,
                "timed_out": self.build.timed_out,
                "cancelled": self.build.cancelled,
            },
            "test": {
                "returncode": self.test.returncode,
                "timed_out": self.test.timed_out,
                "cancelled": self.test.cancelled,
                "stdout": self.test.stdout.strip(),
            },
            "artifacts": [
                {"path": item.path, "size": item.size, "sha256": item.sha256}
                for item in self.artifacts
            ],
        }


class WpfAdapter:
    ADAPTER_ID = "adapter.wpf"
    TARGET_FRAMEWORK = "net10.0-windows"
    TEST_SENTINEL = "KODEPOIA_WPF_TEST_PASS"

    def __init__(self, project_root: Path, staging_root: Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.staging_root = Path(staging_root).resolve(strict=False)
        self.fixture_root = self.project_root / ".kodepoia" / "fixtures" / "wpf"

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
        if machine in {"amd64", "x86_64"}:
            return DesktopArchitecture.X64
        if machine in {"arm64", "aarch64"}:
            return DesktopArchitecture.ARM64
        return DesktopArchitecture.X86

    def discover_toolchain(self) -> tuple[Path, DesktopToolchainIdentity] | DesktopCapabilityReport:
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
        argv = boundary.build_probe_argv(DesktopToolKind.DOTNET, dotnet)
        result = ProcessSandbox(
            self.project_root, allowed_executables={dotnet.name}
        ).run(argv, cwd=self.project_root, timeout=30)
        version = result.stdout.strip()
        if result.returncode != 0 or not version:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                blockers=("dotnet_probe_failed",),
            )
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
            ("dotnet_sdk", "windows_desktop_probe"),
        )
        return dotnet, identity

    def render_fixture(self, model: DesktopAppModel) -> tuple[Path, Path, str]:
        model.validate()
        projection = model.adapter_projection(DesktopFramework.WPF)
        model_sha = projection.logical_model_sha256
        root = self.fixture_root
        app = root / "App"
        harness = root / "Harness"
        app.mkdir(parents=True, exist_ok=True)
        harness.mkdir(parents=True, exist_ok=True)
        staging = self.staging_root.as_posix().replace("/", "\\")

        app_csproj = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>{self.TARGET_FRAMEWORK}</TargetFramework>
    <UseWPF>true</UseWPF>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <Deterministic>true</Deterministic>
    <ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>
    <BaseOutputPath>{staging}\\app\\</BaseOutputPath>
    <BaseIntermediateOutputPath>{staging}\\obj-app\\</BaseIntermediateOutputPath>
  </PropertyGroup>
</Project>
'''
        (app / "KodepoiaWpfFixture.csproj").write_text(app_csproj, encoding="utf-8", newline="\n")
        (app / "App.xaml").write_text(
            '<Application x:Class="KodepoiaWpfFixture.App" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" StartupUri="MainWindow.xaml"/>\n',
            encoding="utf-8", newline="\n",
        )
        (app / "App.xaml.cs").write_text(
            'using System.Windows; namespace KodepoiaWpfFixture; public partial class App : Application { }\n',
            encoding="utf-8", newline="\n",
        )
        (app / "MainWindow.xaml").write_text(
            '<Window x:Class="KodepoiaWpfFixture.MainWindow" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Title="Kodepoia WPF" Width="640" Height="360"><Grid><TextBlock Text="Kodepoia WPF fixture"/></Grid></Window>\n',
            encoding="utf-8", newline="\n",
        )
        (app / "MainWindow.xaml.cs").write_text(
            f'using System.Windows; namespace KodepoiaWpfFixture; public partial class MainWindow : Window {{ public const string ModelSha = "{model_sha}"; public MainWindow() {{ InitializeComponent(); DataContext = ModelSha; }} }}\n',
            encoding="utf-8", newline="\n",
        )

        harness_csproj = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>{self.TARGET_FRAMEWORK}</TargetFramework>
    <UseWPF>true</UseWPF>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <Deterministic>true</Deterministic>
    <ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>
    <BaseOutputPath>{staging}\\harness\\</BaseOutputPath>
    <BaseIntermediateOutputPath>{staging}\\obj-harness\\</BaseIntermediateOutputPath>
  </PropertyGroup>
</Project>
'''
        (harness / "KodepoiaWpfHarness.csproj").write_text(harness_csproj, encoding="utf-8", newline="\n")
        (harness / "Program.cs").write_text(
            f'''using System;\nusing System.Threading;\nusing System.Windows;\nusing System.Windows.Threading;\ninternal static class Program {{\n  [STAThread]\n  public static int Main() {{\n    if (Thread.CurrentThread.GetApartmentState() != ApartmentState.STA) return 11;\n    if (typeof(Window).Assembly.GetName().Name != "PresentationFramework") return 12;\n    var app = new Application();\n    var dispatcher = Dispatcher.CurrentDispatcher;\n    var window = new Window {{ Title = "Kodepoia", DataContext = "{model_sha}" }};\n    if ((string?)window.DataContext != "{model_sha}") return 13;\n    window.Close();\n    app.Shutdown();\n    Console.WriteLine("{self.TEST_SENTINEL}:{model_sha}");\n    return 0;\n  }}\n}}\n''',
            encoding="utf-8", newline="\n",
        )
        return app / "KodepoiaWpfFixture.csproj", harness / "KodepoiaWpfHarness.csproj", model_sha

    def run_acceptance(self, model: DesktopAppModel) -> WpfAcceptanceResult | DesktopCapabilityReport:
        discovered = self.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport):
            return discovered
        dotnet, identity = discovered
        app_project, harness_project, model_sha = self.render_fixture(model)
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent),
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        sandbox = ProcessSandbox(self.project_root, allowed_executables={dotnet.name})

        for project in (app_project, harness_project):
            validated = boundary.validate_project_file(project, suffixes=frozenset({".csproj"}))
            restore = (str(dotnet), "restore", str(validated), "--nologo")
            restore_result = sandbox.run(restore, cwd=self.project_root, timeout=120)
            if restore_result.returncode != 0:
                return DesktopCapabilityReport(
                    self.ADAPTER_ID,
                    DesktopCapabilityState.FAILED,
                    toolchain=identity,
                    blockers=("restore_failed",),
                )

        build_argv = boundary.build_dotnet_argv(
            dotnet,
            operation="build",
            project_file=app_project,
            configuration="Release",
        )
        build = sandbox.run(build_argv, cwd=self.project_root, timeout=180)
        if build.returncode != 0:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                toolchain=identity,
                blockers=("wpf_build_failed",),
            )
        harness_build_argv = boundary.build_dotnet_argv(
            dotnet,
            operation="build",
            project_file=harness_project,
            configuration="Release",
        )
        harness_build = sandbox.run(harness_build_argv, cwd=self.project_root, timeout=180)
        if harness_build.returncode != 0:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                toolchain=identity,
                blockers=("wpf_test_build_failed",),
            )
        harness_dll = self.staging_root / "harness" / "Release" / self.TARGET_FRAMEWORK / "KodepoiaWpfHarness.dll"
        validated_dll = boundary.validate_staging_path(harness_dll)
        if not validated_dll.is_file():
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                toolchain=identity,
                blockers=("test_artifact_missing",),
            )
        test = sandbox.run((str(dotnet), str(validated_dll)), cwd=self.project_root, timeout=60)
        if test.returncode != 0 or f"{self.TEST_SENTINEL}:{model_sha}" not in test.stdout:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.FAILED,
                toolchain=identity,
                blockers=("wpf_runtime_test_failed",),
            )

        artifacts: list[WpfArtifact] = []
        for path in sorted(item for item in self.staging_root.rglob("*") if item.is_file()):
            artifacts.append(WpfArtifact(path.relative_to(self.staging_root).as_posix(), path.stat().st_size, self._sha(path)))
        report = DesktopCapabilityReport(
            self.ADAPTER_ID,
            DesktopCapabilityState.AVAILABLE,
            toolchain=identity,
            capabilities=("build_ready", "restore_ready", "runtime_smoke_ready", "test_ready", "windows_only"),
        )
        return WpfAcceptanceResult(report, model_sha, build, test, tuple(artifacts))


def write_wpf_acceptance_report(result: WpfAcceptanceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
