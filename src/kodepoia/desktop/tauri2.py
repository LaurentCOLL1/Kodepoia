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

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")
_HOST_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{2,127}$")
_WINDOW_ICON_BYTES = bytes.fromhex(
    "00000100010001010000010020003000000016000000280000000100000002000000"
    "0100200000000000040000000000000000000000000000000000000000000066ccff"
    "00000000"
)


class TauriLicenseState(StrEnum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class TauriDependencyDeclaration:
    package: str
    version: str
    license_state: TauriLicenseState = TauriLicenseState.REVIEW_REQUIRED
    redistribution_rights_inferred: bool = False

    def __post_init__(self) -> None:
        if self.package not in {"tauri", "tauri-build"}:
            raise ValueError("Tauri dependency package is not allowlisted")
        if _VERSION_RE.match(self.version) is None:
            raise ValueError("Tauri dependency version is invalid")
        if self.redistribution_rights_inferred:
            raise ValueError("Kodepoia must not infer Tauri redistribution rights")

    def canonical(self) -> dict[str, object]:
        return {
            "package": self.package,
            "version": self.version,
            "license_state": self.license_state.value,
            "redistribution_rights_inferred": self.redistribution_rights_inferred,
        }


@dataclass(frozen=True, slots=True)
class TauriGeneratedFile:
    path: str
    sha256: str

    def __post_init__(self) -> None:
        parts = Path(self.path).parts
        if not self.path or self.path.startswith(("/", "\\")) or ".." in parts:
            raise ValueError("Tauri generated file path must be relative and bounded")
        if _SHA256_RE.fullmatch(self.sha256) is None:
            raise ValueError("Tauri generated file hash must be SHA-256")

    def canonical(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class TauriProjectManifest:
    model_sha256: str
    tauri_version: str
    tauri_build_version: str
    permissions: tuple[str, ...]
    bundle_targets: tuple[str, ...]
    files: tuple[TauriGeneratedFile, ...]

    def __post_init__(self) -> None:
        if _SHA256_RE.fullmatch(self.model_sha256) is None:
            raise ValueError("model_sha256 must be SHA-256")
        if self.tauri_version != Tauri2Adapter.TAURI_VERSION:
            raise ValueError("R12.9 Tauri runtime version is frozen")
        if self.tauri_build_version != Tauri2Adapter.TAURI_BUILD_VERSION:
            raise ValueError("R12.9 tauri-build version is frozen")
        if self.permissions:
            raise ValueError("R12.9 acceptance fixture exposes no frontend IPC permissions")
        if self.bundle_targets:
            raise ValueError("R12.9 acceptance fixture does not build installers")
        ordered = tuple(sorted(self.files, key=lambda item: item.path))
        if len({item.path for item in ordered}) != len(ordered):
            raise ValueError("Tauri generated file manifest contains duplicate paths")
        object.__setattr__(self, "files", ordered)

    def canonical(self) -> dict[str, object]:
        return {
            "model_sha256": self.model_sha256,
            "tauri_version": self.tauri_version,
            "tauri_build_version": self.tauri_build_version,
            "permissions": list(self.permissions),
            "bundle_targets": list(self.bundle_targets),
            "files": [item.canonical() for item in self.files],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class TauriToolchainDiscovery:
    cargo: Path
    rustc: Path
    cargo_version: str
    rustc_version: str
    host_triple: str
    report_identity: DesktopToolchainIdentity


@dataclass(frozen=True, slots=True)
class TauriKitIdentity:
    platform: DesktopOS
    architecture: DesktopArchitecture
    cargo_version: str
    cargo_sha256: str
    rustc_version: str
    rustc_sha256: str
    host_triple: str
    tauri_version: str
    webview_version: str
    cargo_lock_sha256: str
    capability_policy_sha256: str

    def __post_init__(self) -> None:
        if self.platform is not DesktopOS.WINDOWS:
            raise ValueError("R12.9 WebView2 acceptance is Windows-only")
        if self.architecture is not DesktopArchitecture.X64:
            raise ValueError("R12.9 hosted WebView2 acceptance is x64 only")
        if _HOST_RE.fullmatch(self.host_triple) is None or not self.host_triple.endswith("pc-windows-msvc"):
            raise ValueError("R12.9 requires the Rust MSVC Windows host")
        if self.tauri_version != Tauri2Adapter.TAURI_VERSION:
            raise ValueError("unexpected Tauri runtime version")
        if not self.webview_version or len(self.webview_version) > 128 or "\x00" in self.webview_version:
            raise ValueError("WebView2 version evidence is invalid")
        for value in (
            self.cargo_sha256,
            self.rustc_sha256,
            self.cargo_lock_sha256,
            self.capability_policy_sha256,
        ):
            if _SHA256_RE.fullmatch(value) is None:
                raise ValueError("Tauri kit digest must be SHA-256")

    def canonical(self) -> dict[str, object]:
        return {
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "cargo_version": self.cargo_version,
            "cargo_sha256": self.cargo_sha256,
            "rustc_version": self.rustc_version,
            "rustc_sha256": self.rustc_sha256,
            "host_triple": self.host_triple,
            "tauri_version": self.tauri_version,
            "webview_version": self.webview_version,
            "cargo_lock_sha256": self.cargo_lock_sha256,
            "capability_policy_sha256": self.capability_policy_sha256,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class TauriArtifact:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class TauriAcceptanceResult:
    report: DesktopCapabilityReport
    model_sha256: str
    project_manifest: TauriProjectManifest
    kit: TauriKitIdentity
    dependencies: tuple[TauriDependencyDeclaration, ...]
    build: SandboxResult
    runtime: SandboxResult
    artifacts: tuple[TauriArtifact, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.report.canonical(),
            "model_sha256": self.model_sha256,
            "project_manifest": self.project_manifest.canonical(),
            "project_manifest_sha256": self.project_manifest.digest(),
            "kit": self.kit.canonical(),
            "kit_sha256": self.kit.digest(),
            "dependencies": [item.canonical() for item in self.dependencies],
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


class Tauri2Adapter:
    ADAPTER_ID = "adapter.tauri2"
    TAURI_VERSION = "2.11.5"
    TAURI_BUILD_VERSION = "2.6.3"
    RUST_MINIMUM = (1, 77, 2)
    SENTINEL = "KODEPOIA_TAURI2_RUNTIME_PASS"

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
        if machine in {"amd64", "x86_64"}:
            return DesktopArchitecture.X64
        if machine in {"arm64", "aarch64"}:
            return DesktopArchitecture.ARM64
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
        match = _VERSION_RE.search(value)
        if match is None:
            return (0, 0, 0)
        return tuple(int(part or 0) for part in match.groups())  # type: ignore[return-value]

    @staticmethod
    def _msvc_env() -> dict[str, str]:
        if platform.system() != "Windows":
            return {}
        return {
            key: value
            for key in ("INCLUDE", "LIB", "LIBPATH")
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

    def discover_toolchain(self) -> TauriToolchainDiscovery | DesktopCapabilityReport:
        current = self.current_os()
        if current is not DesktopOS.WINDOWS:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("windows_webview2_acceptance_required",),
            )
        if self.current_arch() is not DesktopArchitecture.X64:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("windows_x64_acceptance_required",),
            )
        cargo_raw = shutil.which("cargo")
        rustc_raw = shutil.which("rustc")
        if not cargo_raw:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNAVAILABLE,
                blockers=("cargo_missing",),
            )
        if not rustc_raw:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNAVAILABLE,
                blockers=("rustc_missing",),
            )
        cargo = Path(cargo_raw).resolve(strict=True)
        rustc = Path(rustc_raw).resolve(strict=True)
        roots = (cargo.parent, cargo.parent.parent, rustc.parent, rustc.parent.parent)
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=roots,
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        cargo = boundary.validate_executable(DesktopToolKind.CARGO, cargo)
        rustc = boundary.validate_executable(DesktopToolKind.RUSTC, rustc)
        sandbox = ProcessSandbox(self.project_root, {cargo.name, rustc.name})
        cargo_probe = sandbox.run(
            boundary.build_probe_argv(DesktopToolKind.CARGO, cargo),
            cwd=self.project_root,
            timeout=30,
        )
        if cargo_probe.returncode != 0:
            return self._failure(None, "cargo_probe_failed", cargo_probe)
        rustc_probe = sandbox.run(
            boundary.build_probe_argv(DesktopToolKind.RUSTC, rustc),
            cwd=self.project_root,
            timeout=30,
        )
        if rustc_probe.returncode != 0:
            return self._failure(None, "rustc_probe_failed", rustc_probe)
        cargo_version = cargo_probe.stdout.strip()
        rustc_version = rustc_probe.stdout.strip()
        if self._version_tuple(rustc_version) < self.RUST_MINIMUM:
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("rust_1_77_2_required",),
            )
        verbose = sandbox.run((str(rustc), "-vV"), cwd=self.project_root, timeout=30)
        if verbose.returncode != 0:
            return self._failure(None, "rustc_verbose_probe_failed", verbose)
        host = ""
        for line in verbose.stdout.splitlines():
            if line.startswith("host:"):
                host = line.split(":", 1)[1].strip()
                break
        if _HOST_RE.fullmatch(host) is None or not host.endswith("pc-windows-msvc"):
            return DesktopCapabilityReport(
                self.ADAPTER_ID,
                DesktopCapabilityState.UNSUPPORTED,
                blockers=("rust_msvc_host_required",),
            )
        identity = DesktopToolchainIdentity(
            DesktopToolKind.CARGO,
            cargo.name,
            self._sha(cargo),
            cargo_version,
            current,
            self.current_arch(),
            ("offline_locked_build", "rustc_ready", "tauri2", "webview2_runtime_probe"),
        )
        return TauriToolchainDiscovery(cargo, rustc, cargo_version, rustc_version, host, identity)

    def fixture_root(self) -> Path:
        return self.project_root / ".kodepoia" / "fixtures" / "tauri2"

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def render_fixture(self, model: DesktopAppModel) -> tuple[Path, TauriProjectManifest, str]:
        model.validate()
        model_sha = model.conformance_projection(DesktopFramework.TAURI2).logical_model_sha256
        root = self.fixture_root()
        root.mkdir(parents=True, exist_ok=True)
        cargo = root / "Cargo.toml"
        build_rs = root / "build.rs"
        main_rs = root / "src" / "main.rs"
        config = root / "tauri.conf.json"
        html = root / "dist" / "index.html"
        model_file = root / "dist" / "model.txt"
        icon = root / "icons" / "icon.ico"

        self._write(
            cargo,
            "[package]\n"
            "name = \"kodepoia_tauri_fixture\"\n"
            "version = \"0.1.0\"\n"
            "edition = \"2021\"\n"
            "rust-version = \"1.77.2\"\n"
            "build = \"build.rs\"\n\n"
            "[build-dependencies]\n"
            f"tauri-build = \"={self.TAURI_BUILD_VERSION}\"\n\n"
            "[dependencies]\n"
            f"tauri = \"={self.TAURI_VERSION}\"\n",
        )
        self._write(build_rs, "fn main() { tauri_build::build(); }\n")
        self._write(
            main_rs,
            "use std::time::Duration;\n"
            "use tauri::Manager;\n\n"
            f"const MODEL_SHA: &str = \"{model_sha}\";\n"
            f"const SENTINEL: &str = \"{self.SENTINEL}\";\n\n"
            "fn main() {\n"
            "    let app = tauri::Builder::default()\n"
            "        .setup(|app| {\n"
            "            if app.get_webview_window(\"main\").is_none() {\n"
            "                return Err(std::io::Error::other(\"main webview missing\").into());\n"
            "            }\n"
            "            let webview = tauri::webview_version()?;\n"
            "            println!(\"{}:{}:{}:{}\", SENTINEL, MODEL_SHA, tauri::VERSION, webview);\n"
            "            let handle = app.handle().clone();\n"
            "            std::thread::spawn(move || {\n"
            "                std::thread::sleep(Duration::from_millis(250));\n"
            "                handle.exit(0);\n"
            "            });\n"
            "            Ok(())\n"
            "        })\n"
            "        .build(tauri::generate_context!())\n"
            "        .expect(\"Kodepoia Tauri fixture failed to initialize\");\n"
            "    app.run(|_, _| {});\n"
            "}\n",
        )
        config_payload = {
            "$schema": "https://schema.tauri.app/config/2",
            "productName": "KodepoiaTauriFixture",
            "version": "0.1.0",
            "identifier": "io.kodepoia.r12_9.fixture",
            "mainBinaryName": "kodepoia_tauri_fixture",
            "build": {"frontendDist": "dist"},
            "app": {
                "withGlobalTauri": False,
                "security": {
                    "capabilities": [],
                    "csp": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'none'; img-src 'self' data:; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'",
                    "freezePrototype": True,
                },
                "windows": [
                    {
                        "label": "main",
                        "title": "Kodepoia R12.9 Tauri Fixture",
                        "width": 640,
                        "height": 480,
                        "resizable": False,
                        "visible": False,
                    }
                ],
            },
            "bundle": {"active": False},
            "plugins": {},
        }
        self._write(config, json.dumps(config_payload, indent=2, sort_keys=True) + "\n")
        self._write(
            html,
            "<!doctype html><html><head><meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; connect-src 'none'; object-src 'none'; frame-src 'none'\"><title>Kodepoia</title></head><body><main id=\"app\">Kodepoia Tauri R12.9</main></body></html>\n",
        )
        self._write(model_file, model_sha + "\n")
        icon.parent.mkdir(parents=True, exist_ok=True)
        icon.write_bytes(_WINDOW_ICON_BYTES)
        paths = (cargo, build_rs, main_rs, config, html, model_file, icon)
        files = tuple(
            TauriGeneratedFile(path.relative_to(root).as_posix(), self._sha(path))
            for path in paths
        )
        manifest = TauriProjectManifest(
            model_sha,
            self.TAURI_VERSION,
            self.TAURI_BUILD_VERSION,
            (),
            (),
            files,
        )
        return cargo, manifest, model_sha

    def _validate_lockfile(self, root: Path) -> tuple[Path, str]:
        lock = root / "Cargo.lock"
        if not lock.is_file():
            raise FileNotFoundError("Cargo.lock is required before governed offline acceptance")
        text = lock.read_text(encoding="utf-8")
        for package, version in (
            ("tauri", self.TAURI_VERSION),
            ("tauri-build", self.TAURI_BUILD_VERSION),
        ):
            pattern = rf'name = "{re.escape(package)}"\nversion = "{re.escape(version)}"'
            if re.search(pattern, text) is None:
                raise ValueError(f"Cargo.lock does not pin {package} {version}")
        return lock, self._sha(lock)

    def run_acceptance(
        self,
        model: DesktopAppModel,
    ) -> TauriAcceptanceResult | DesktopCapabilityReport:
        discovered = self.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport):
            return discovered
        cargo_manifest, manifest, model_sha = self.render_fixture(model)
        root = cargo_manifest.parent
        try:
            lock, lock_sha = self._validate_lockfile(root)
        except (FileNotFoundError, ValueError) as exc:
            self.last_diagnostic = str(exc)
            return self._failure(discovered.report_identity, "cargo_lock_invalid")
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(
                discovered.cargo.parent,
                discovered.cargo.parent.parent,
                discovered.rustc.parent,
                discovered.rustc.parent.parent,
            ),
            project_root=self.project_root,
            staging_root=self.staging_root,
        )
        target_dir = boundary.validate_staging_path(self.staging_root / "cargo-target")
        target_dir.mkdir(parents=True, exist_ok=True)
        build = ProcessSandbox(self.project_root, {discovered.cargo.name}).run(
            boundary.build_cargo_argv(
                discovered.cargo,
                operation="build",
                manifest_path=cargo_manifest,
                target_directory=target_dir,
            ),
            cwd=self.project_root,
            timeout=900,
            env=self._msvc_env(),
        )
        if build.returncode != 0:
            return self._failure(discovered.report_identity, "tauri_offline_build_failed", build)
        executable = boundary.validate_staging_path(
            target_dir / "debug" / "kodepoia_tauri_fixture.exe"
        )
        if not executable.is_file():
            return self._failure(discovered.report_identity, "tauri_runtime_artifact_missing")
        runtime = ProcessSandbox(self.project_root, {executable.name}).run(
            (str(executable),),
            cwd=self.project_root,
            timeout=30,
        )
        prefix = f"{self.SENTINEL}:{model_sha}:{self.TAURI_VERSION}:"
        line = next((item.strip() for item in runtime.stdout.splitlines() if item.startswith(prefix)), "")
        if runtime.returncode != 0 or not line:
            return self._failure(discovered.report_identity, "tauri_webview2_runtime_probe_failed", runtime)
        webview_version = line[len(prefix) :].strip()
        if not webview_version:
            return self._failure(discovered.report_identity, "webview2_version_missing", runtime)
        config = root / "tauri.conf.json"
        config_payload = json.loads(config.read_text(encoding="utf-8"))
        capability_policy_sha = canonical_sha256(
            {
                "capabilities": config_payload["app"]["security"]["capabilities"],
                "withGlobalTauri": config_payload["app"]["withGlobalTauri"],
                "csp": config_payload["app"]["security"]["csp"],
                "bundle": config_payload["bundle"],
            }
        )
        kit = TauriKitIdentity(
            DesktopOS.WINDOWS,
            DesktopArchitecture.X64,
            discovered.cargo_version,
            self._sha(discovered.cargo),
            discovered.rustc_version,
            self._sha(discovered.rustc),
            discovered.host_triple,
            self.TAURI_VERSION,
            webview_version,
            lock_sha,
            capability_policy_sha,
        )
        dependencies = (
            TauriDependencyDeclaration("tauri", self.TAURI_VERSION),
            TauriDependencyDeclaration("tauri-build", self.TAURI_BUILD_VERSION),
        )
        artifacts = tuple(
            TauriArtifact(path.relative_to(self.staging_root).as_posix(), path.stat().st_size, self._sha(path))
            for path in sorted(item for item in self.staging_root.rglob("*") if item.is_file())
        )
        report = DesktopCapabilityReport(
            self.ADAPTER_ID,
            DesktopCapabilityState.AVAILABLE,
            toolchain=discovered.report_identity,
            capabilities=(
                "cargo_locked_offline_build",
                "ipc_default_deny",
                "tauri2_runtime_ready",
                "webview2_runtime_ready",
                "windows_x64",
            ),
        )
        _ = lock
        return TauriAcceptanceResult(
            report,
            model_sha,
            manifest,
            kit,
            dependencies,
            build,
            runtime,
            artifacts,
        )


def write_tauri_acceptance_report(result: TauriAcceptanceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
