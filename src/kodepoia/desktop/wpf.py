from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from .app_model import DesktopAppModel
from .boundary import DesktopToolchainBoundary
from .contracts import DesktopArchitecture, DesktopCapabilityReport, DesktopCapabilityState, DesktopFramework, DesktopOS, DesktopToolKind, DesktopToolchainIdentity


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
        return {"adapter": self.report.canonical(), "model_sha256": self.model_sha256, "build": {"returncode": self.build.returncode}, "test": {"returncode": self.test.returncode, "stdout": self.test.stdout.strip()}, "artifacts": [{"path": a.path, "size": a.size, "sha256": a.sha256} for a in self.artifacts]}


class WpfAdapter:
    ADAPTER_ID = "adapter.wpf"
    TARGET = "net10.0-windows"
    SENTINEL = "KODEPOIA_WPF_TEST_PASS"
    _WINDOWS_MACHINE_ENV = ("PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "PROGRAMDATA")

    def __init__(self, project_root: Path, staging_root: Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.staging_root = Path(staging_root).resolve(strict=False)
        self.fixture_root = self.project_root / ".kodepoia" / "fixtures" / "wpf"
        self.last_diagnostic = ""

    @classmethod
    def _dotnet_env(cls) -> dict[str, str]:
        return {key: value for key in cls._WINDOWS_MACHINE_ENV if (value := os.environ.get(key))}

    def _failure(self, identity: DesktopToolchainIdentity, blocker: str, result: SandboxResult | None = None) -> DesktopCapabilityReport:
        if result is not None:
            text = (result.stdout + "\n" + result.stderr).strip().replace("\x00", "")
            self.last_diagnostic = text[-8000:]
        return DesktopCapabilityReport(self.ADAPTER_ID, DesktopCapabilityState.FAILED, toolchain=identity, blockers=(blocker,))

    @staticmethod
    def _sha(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _arch() -> DesktopArchitecture:
        m = platform.machine().lower()
        return DesktopArchitecture.ARM64 if m in {"arm64", "aarch64"} else DesktopArchitecture.X64 if m in {"amd64", "x86_64"} else DesktopArchitecture.X86

    def discover_toolchain(self) -> tuple[Path, DesktopToolchainIdentity] | DesktopCapabilityReport:
        if platform.system() != "Windows":
            return DesktopCapabilityReport(self.ADAPTER_ID, DesktopCapabilityState.UNSUPPORTED, blockers=("windows_required",))
        found = shutil.which("dotnet")
        if not found:
            return DesktopCapabilityReport(self.ADAPTER_ID, DesktopCapabilityState.UNAVAILABLE, blockers=("dotnet_missing",))
        dotnet = Path(found).resolve(strict=True)
        boundary = DesktopToolchainBoundary(allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent), project_root=self.project_root, staging_root=self.staging_root)
        probe = ProcessSandbox(self.project_root, {dotnet.name}).run(boundary.build_probe_argv(DesktopToolKind.DOTNET, dotnet), cwd=self.project_root, timeout=30, env=self._dotnet_env())
        version = probe.stdout.strip()
        if probe.returncode != 0 or not version:
            self.last_diagnostic = (probe.stdout + "\n" + probe.stderr).strip()[-8000:]
            return DesktopCapabilityReport(self.ADAPTER_ID, DesktopCapabilityState.FAILED, blockers=("dotnet_probe_failed",))
        try:
            major = int(version.split(".", 1)[0])
        except ValueError:
            major = 0
        if major < 10:
            return DesktopCapabilityReport(self.ADAPTER_ID, DesktopCapabilityState.UNSUPPORTED, blockers=("dotnet_10_required",))
        identity = DesktopToolchainIdentity(DesktopToolKind.DOTNET, dotnet.name, self._sha(dotnet), version, DesktopOS.WINDOWS, self._arch(), ("dotnet_sdk", "windows_desktop_probe"))
        return dotnet, identity

    def render_fixture(self, model: DesktopAppModel) -> tuple[Path, Path, str]:
        model.validate()
        digest = model.conformance_projection(DesktopFramework.WPF).logical_model_sha256
        app, harness = self.fixture_root / "App", self.fixture_root / "Harness"
        app.mkdir(parents=True, exist_ok=True); harness.mkdir(parents=True, exist_ok=True)
        out = str(self.staging_root)
        def project(output: str, kind: str) -> str:
            return f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>{kind}</OutputType><TargetFramework>{self.TARGET}</TargetFramework><UseWPF>true</UseWPF><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings><Deterministic>true</Deterministic><ContinuousIntegrationBuild>true</ContinuousIntegrationBuild><BaseOutputPath>{out}\\{output}\\</BaseOutputPath><BaseIntermediateOutputPath>{out}\\obj-{output}\\</BaseIntermediateOutputPath></PropertyGroup></Project>\n'
        (app / "KodepoiaWpfFixture.csproj").write_text(project("app", "WinExe"), encoding="utf-8", newline="\n")
        (app / "App.xaml").write_text('<Application x:Class="KodepoiaWpfFixture.App" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" StartupUri="MainWindow.xaml"/>\n', encoding="utf-8", newline="\n")
        (app / "App.xaml.cs").write_text('using System.Windows; namespace KodepoiaWpfFixture; public partial class App : Application { }\n', encoding="utf-8", newline="\n")
        (app / "MainWindow.xaml").write_text('<Window x:Class="KodepoiaWpfFixture.MainWindow" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Title="Kodepoia"><TextBlock Text="Kodepoia WPF fixture"/></Window>\n', encoding="utf-8", newline="\n")
        (app / "MainWindow.xaml.cs").write_text(f'using System.Windows; namespace KodepoiaWpfFixture; public partial class MainWindow : Window {{ public const string ModelSha="{digest}"; public MainWindow() {{ InitializeComponent(); DataContext=ModelSha; }} }}\n', encoding="utf-8", newline="\n")
        (harness / "KodepoiaWpfHarness.csproj").write_text(project("harness", "Exe"), encoding="utf-8", newline="\n")
        (harness / "Program.cs").write_text(f'using System; using System.Threading; using System.Windows; using System.Windows.Threading; internal static class Program {{ [STAThread] public static int Main() {{ if(Thread.CurrentThread.GetApartmentState()!=ApartmentState.STA)return 11; if(typeof(Window).Assembly.GetName().Name!="PresentationFramework")return 12; var app=new Application(); var d=Dispatcher.CurrentDispatcher; var w=new Window{{DataContext="{digest}"}}; if((string?)w.DataContext!="{digest}")return 13; w.Close(); app.Shutdown(); Console.WriteLine("{self.SENTINEL}:{digest}"); return 0; }} }}\n', encoding="utf-8", newline="\n")
        return app / "KodepoiaWpfFixture.csproj", harness / "KodepoiaWpfHarness.csproj", digest

    def run_acceptance(self, model: DesktopAppModel) -> WpfAcceptanceResult | DesktopCapabilityReport:
        discovered = self.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport): return discovered
        dotnet, identity = discovered
        app, harness, digest = self.render_fixture(model)
        boundary = DesktopToolchainBoundary(allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent), project_root=self.project_root, staging_root=self.staging_root)
        sandbox = ProcessSandbox(self.project_root, {dotnet.name})
        env = self._dotnet_env()
        for project in (app, harness):
            p = boundary.validate_project_file(project, suffixes=frozenset({".csproj"}))
            r = sandbox.run((str(dotnet), "restore", str(p), "--nologo"), cwd=self.project_root, timeout=120, env=env)
            if r.returncode != 0: return self._failure(identity, "restore_failed", r)
        build = sandbox.run(boundary.build_dotnet_argv(dotnet, operation="build", project_file=app, configuration="Release"), cwd=self.project_root, timeout=180, env=env)
        if build.returncode != 0: return self._failure(identity, "wpf_build_failed", build)
        hb = sandbox.run(boundary.build_dotnet_argv(dotnet, operation="build", project_file=harness, configuration="Release"), cwd=self.project_root, timeout=180, env=env)
        if hb.returncode != 0: return self._failure(identity, "wpf_test_build_failed", hb)
        dll = boundary.validate_staging_path(self.staging_root / "harness" / "Release" / self.TARGET / "KodepoiaWpfHarness.dll")
        if not dll.is_file(): return self._failure(identity, "test_artifact_missing")
        test = sandbox.run((str(dotnet), str(dll)), cwd=self.project_root, timeout=60, env=env)
        if test.returncode != 0 or f"{self.SENTINEL}:{digest}" not in test.stdout: return self._failure(identity, "wpf_runtime_test_failed", test)
        artifacts = tuple(WpfArtifact(p.relative_to(self.staging_root).as_posix(), p.stat().st_size, self._sha(p)) for p in sorted(x for x in self.staging_root.rglob("*") if x.is_file()))
        report = DesktopCapabilityReport(self.ADAPTER_ID, DesktopCapabilityState.AVAILABLE, toolchain=identity, capabilities=("build_ready", "restore_ready", "runtime_smoke_ready", "test_ready", "windows_only"))
        return WpfAcceptanceResult(report, digest, build, test, artifacts)


def write_wpf_acceptance_report(result: WpfAcceptanceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
