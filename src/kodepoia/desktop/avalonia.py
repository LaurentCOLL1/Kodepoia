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


@dataclass(frozen=True, slots=True)
class AvaloniaTargetMatrix:
    targets: tuple[DesktopOS, ...]

    def __post_init__(self) -> None:
        allowed = {DesktopOS.WINDOWS, DesktopOS.LINUX, DesktopOS.MACOS}
        normalized = tuple(sorted(set(self.targets), key=lambda item: item.value))
        if not normalized or any(item not in allowed for item in normalized):
            raise ValueError("Avalonia R12.7 matrix supports desktop Windows/Linux/macOS only")
        object.__setattr__(self, "targets", normalized)

    def canonical(self) -> dict[str, object]:
        return {"targets": [item.value for item in self.targets]}

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AvaloniaArtifact:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class AvaloniaAcceptanceResult:
    report: DesktopCapabilityReport
    model_sha256: str
    target_matrix_sha256: str
    avalonia_version: str
    platform: DesktopOS
    architecture: DesktopArchitecture
    build: SandboxResult
    runtime: SandboxResult
    artifacts: tuple[AvaloniaArtifact, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.report.canonical(),
            "model_sha256": self.model_sha256,
            "target_matrix_sha256": self.target_matrix_sha256,
            "avalonia_version": self.avalonia_version,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
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


class AvaloniaAdapter:
    ADAPTER_ID = "adapter.avalonia"
    TARGET = "net10.0"
    AVALONIA_VERSION = "12.1.1"
    SENTINEL = "KODEPOIA_AVALONIA_RUNTIME_PASS"
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

    @classmethod
    def _dotnet_env(cls) -> dict[str, str]:
        if platform.system() != "Windows":
            return {}
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
    ) -> tuple[Path, DesktopToolchainIdentity] | DesktopCapabilityReport:
        current = self.current_os()
        if current is None:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("desktop_os_unsupported",),
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
        probe = ProcessSandbox(self.project_root, {dotnet.name}).run(
            boundary.build_probe_argv(DesktopToolKind.DOTNET, dotnet),
            cwd=self.project_root,
            timeout=30,
            env=self._dotnet_env(),
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
                blockers=("dotnet_10_acceptance_target_required",),
            )
        identity = DesktopToolchainIdentity(
            DesktopToolKind.DOTNET,
            dotnet.name,
            self._sha(dotnet),
            version,
            current,
            self.current_arch(),
            ("avalonia_restore", "cross_platform_dotnet", "dotnet_sdk"),
        )
        return dotnet, identity

    def fixture_root(self, current: DesktopOS) -> Path:
        return self.project_root / ".kodepoia" / "fixtures" / "avalonia" / current.value

    def render_fixture(
        self,
        model: DesktopAppModel,
        matrix: AvaloniaTargetMatrix,
    ) -> tuple[Path, Path, str]:
        model.validate()
        current = self.current_os()
        if current is None or current not in matrix.targets:
            raise ValueError("current platform is not selected by Avalonia target matrix")
        model_sha = model.conformance_projection(DesktopFramework.AVALONIA).logical_model_sha256
        root = self.fixture_root(current)
        app_dir = root / "App"
        probe_dir = root / "RuntimeProbe"
        app_dir.mkdir(parents=True, exist_ok=True)
        probe_dir.mkdir(parents=True, exist_ok=True)
        output = str(self.staging_root)
        packages = (
            f'<PackageReference Include="Avalonia" Version="{self.AVALONIA_VERSION}" />'
            f'<PackageReference Include="Avalonia.Desktop" Version="{self.AVALONIA_VERSION}" />'
            f'<PackageReference Include="Avalonia.Themes.Fluent" Version="{self.AVALONIA_VERSION}" />'
        )
        app_project = app_dir / "KodepoiaAvaloniaFixture.csproj"
        app_project.write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
            '<OutputType>Exe</OutputType>'
            f'<TargetFramework>{self.TARGET}</TargetFramework>'
            '<Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>'
            '<Deterministic>true</Deterministic><ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>'
            '<AvaloniaUseCompiledBindingsByDefault>false</AvaloniaUseCompiledBindingsByDefault>'
            f'<BaseOutputPath>{output}/{current.value}/app/</BaseOutputPath>'
            f'<BaseIntermediateOutputPath>{output}/{current.value}/obj-app/</BaseIntermediateOutputPath>'
            '</PropertyGroup><ItemGroup>' + packages + '</ItemGroup></Project>\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "Program.cs").write_text(
            'using Avalonia; namespace KodepoiaAvaloniaFixture; internal static class Program {'
            '[STAThread] public static void Main(string[] args) => BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);'
            'public static AppBuilder BuildAvaloniaApp() => AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace();}\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "App.axaml").write_text(
            '<Application xmlns="https://github.com/avaloniaui" '
            'xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" '
            'x:Class="KodepoiaAvaloniaFixture.App">'
            '<Application.Styles><FluentTheme /></Application.Styles></Application>\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "App.axaml.cs").write_text(
            'using Avalonia; using Avalonia.Controls.ApplicationLifetimes; '
            'namespace KodepoiaAvaloniaFixture; public partial class App : Application {'
            'public override void Initialize() => Avalonia.Markup.Xaml.AvaloniaXamlLoader.Load(this);'
            'public override void OnFrameworkInitializationCompleted() {'
            'if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop) desktop.MainWindow = new MainWindow();'
            'base.OnFrameworkInitializationCompleted(); }}\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "MainWindow.axaml").write_text(
            '<Window xmlns="https://github.com/avaloniaui" '
            'xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" '
            'x:Class="KodepoiaAvaloniaFixture.MainWindow" Title="Kodepoia">'
            f'<TextBlock Text="{model_sha}"/></Window>\n',
            encoding="utf-8",
            newline="\n",
        )
        (app_dir / "MainWindow.axaml.cs").write_text(
            f'using Avalonia.Controls; namespace KodepoiaAvaloniaFixture; public partial class MainWindow : Window '
            f'{{ public const string ModelSha = "{model_sha}"; public MainWindow() {{ InitializeComponent(); }} }}\n',
            encoding="utf-8",
            newline="\n",
        )
        probe_project = probe_dir / "KodepoiaAvaloniaRuntimeProbe.csproj"
        probe_project.write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
            f'<TargetFramework>{self.TARGET}</TargetFramework>'
            '<Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>'
            '<Deterministic>true</Deterministic><ContinuousIntegrationBuild>true</ContinuousIntegrationBuild>'
            f'<BaseOutputPath>{output}/{current.value}/probe/</BaseOutputPath>'
            f'<BaseIntermediateOutputPath>{output}/{current.value}/obj-probe/</BaseIntermediateOutputPath>'
            '</PropertyGroup><ItemGroup>' + packages + '</ItemGroup></Project>\n',
            encoding="utf-8",
            newline="\n",
        )
        (probe_dir / "Program.cs").write_text(
            'using System; using Avalonia; using Avalonia.Controls; internal static class Program {'
            'public static int Main() {'
            'if (typeof(Application).Assembly.GetName().Name != "Avalonia.Base") return 31;'
            'if (typeof(Window).FullName != "Avalonia.Controls.Window") return 32;'
            'if (typeof(AppBuilder).FullName != "Avalonia.AppBuilder") return 33;'
            f'Console.WriteLine("{self.SENTINEL}:{current.value}:{model_sha}"); return 0; }} }}\n',
            encoding="utf-8",
            newline="\n",
        )
        return app_project, probe_project, model_sha

    def run_acceptance(
        self,
        model: DesktopAppModel,
        matrix: AvaloniaTargetMatrix,
    ) -> AvaloniaAcceptanceResult | DesktopCapabilityReport:
        discovered = self.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport):
            return discovered
        dotnet, identity = discovered
        current = identity.platform
        app, probe, model_sha = self.render_fixture(model, matrix)
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent),
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        sandbox = ProcessSandbox(self.project_root, {dotnet.name})
        env = self._dotnet_env()
        for project in (app, probe):
            validated = boundary.validate_project_file(project, suffixes=frozenset({".csproj"}))
            restore = sandbox.run(
                (str(dotnet), "restore", str(validated), "--nologo"),
                cwd=self.project_root,
                timeout=240,
                env=env,
            )
            if restore.returncode != 0:
                return self._failure(identity, "avalonia_restore_failed", restore)
        build = sandbox.run(
            boundary.build_dotnet_argv(dotnet, operation="build", project_file=app, configuration="Release"),
            cwd=self.project_root,
            timeout=300,
            env=env,
        )
        if build.returncode != 0:
            return self._failure(identity, "avalonia_build_failed", build)
        probe_build = sandbox.run(
            boundary.build_dotnet_argv(dotnet, operation="build", project_file=probe, configuration="Release"),
            cwd=self.project_root,
            timeout=300,
            env=env,
        )
        if probe_build.returncode != 0:
            return self._failure(identity, "avalonia_probe_build_failed", probe_build)
        dll = boundary.validate_staging_path(
            self.staging_root / current.value / "probe" / "Release" / self.TARGET / "KodepoiaAvaloniaRuntimeProbe.dll"
        )
        if not dll.is_file():
            return self._failure(identity, "avalonia_probe_artifact_missing")
        runtime = sandbox.run((str(dotnet), str(dll)), cwd=self.project_root, timeout=60, env=env)
        expected = f"{self.SENTINEL}:{current.value}:{model_sha}"
        if runtime.returncode != 0 or expected not in runtime.stdout:
            return self._failure(identity, "avalonia_runtime_probe_failed", runtime)
        platform_root = self.staging_root / current.value
        artifacts = tuple(
            AvaloniaArtifact(path.relative_to(self.staging_root).as_posix(), path.stat().st_size, self._sha(path))
            for path in sorted(item for item in platform_root.rglob("*") if item.is_file())
        )
        report = DesktopCapabilityReport(
            self.ADAPTER_ID,
            DesktopCapabilityState.AVAILABLE,
            toolchain=identity,
            capabilities=(
                "assembly_runtime_ready",
                "build_ready",
                f"platform_{current.value}",
                "restore_ready",
            ),
        )
        return AvaloniaAcceptanceResult(
            report,
            model_sha,
            matrix.digest(),
            self.AVALONIA_VERSION,
            current,
            identity.architecture,
            build,
            runtime,
            artifacts,
        )


def canonical_avalonia_matrix() -> AvaloniaTargetMatrix:
    return AvaloniaTargetMatrix((DesktopOS.WINDOWS, DesktopOS.LINUX, DesktopOS.MACOS))


def write_avalonia_acceptance_report(result: AvaloniaAcceptanceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
