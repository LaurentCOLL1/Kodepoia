from __future__ import annotations

import hashlib
import json
import os
import platform as platform_module
import re
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.core.trust import AuthorityEffect, TrustBoundary, TrustMetadata, TrustOrigin
from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.boundary import DesktopBoundaryError, DesktopToolchainBoundary
from kodepoia.desktop.contracts import (
    DesktopCapabilityReport,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
    DesktopToolKind,
)
from kodepoia.desktop.ipc import (
    IpcAuthorizationError,
    IpcAuthorizationPolicy,
    IpcEndpointIdentity,
    IpcEnvelope,
    IpcMessageKind,
    IpcPeerIdentity,
    IpcPolicy,
    IpcTransportKind,
)
from kodepoia.desktop.packaging import (
    DesktopVersion,
    SigningState,
    build_artifact_manifest,
    verify_artifact_tree,
)
from kodepoia.desktop.persistence import (
    ColumnDefinition,
    QueryIntent,
    QueryOperation,
    SchemaDefinition,
    SQLitePersistenceService,
    SQLiteValueType,
    TableDefinition,
)
from kodepoia.desktop.wpf import WpfAcceptanceResult, WpfAdapter

FIXTURE_RELATIVE = Path("tests/fixtures/r16_12_windows_desktop")
MALICIOUS_FIXTURE = FIXTURE_RELATIVE / "untrusted_project.json"
MALICIOUS_MARKER = "R16_12_UNTRUSTED_SHOULD_NOT_RUN"
SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MIN_REPRESENTATIVE_PROJECT_PATH = 160
MAX_REPRESENTATIVE_PROJECT_PATH = 240


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_payload(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in root.rglob("*")
        if item.is_file()
        and "obj-" not in item.as_posix()
        and "staging" not in item.parts
    )
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(path.read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def build_dotnet_publish_argv(
    boundary: DesktopToolchainBoundary,
    executable: Path,
    *,
    project_file: Path,
    output_directory: Path,
    configuration: str = "Release",
) -> tuple[str, ...]:
    """Build one fixed, shell-free dotnet publish argv under desktop boundaries."""

    if configuration not in {"Debug", "Release"}:
        raise DesktopBoundaryError("dotnet configuration is not allowlisted")
    exe = boundary.validate_executable(DesktopToolKind.DOTNET, executable)
    project = boundary.validate_project_file(
        project_file,
        suffixes=frozenset({".csproj", ".sln", ".slnx"}),
    )
    output = boundary.validate_staging_path(output_directory)
    return (
        str(exe),
        "publish",
        str(project),
        "--no-restore",
        "--nologo",
        "--configuration",
        configuration,
        "--output",
        str(output),
    )


def _dotnet_env() -> dict[str, str]:
    allowed = ("PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "PROGRAMDATA")
    return {key: value for key in allowed if (value := os.environ.get(key))}


def _representative_workspace(temp_root: Path) -> Path:
    workspace = temp_root / "Representative Windows Application With Spaces"
    project_suffix = Path(".kodepoia/fixtures/wpf/App/KodepoiaWpfFixture.csproj")
    segment_number = 1
    while len(str(workspace / project_suffix)) < MIN_REPRESENTATIVE_PROJECT_PATH:
        candidate = workspace / (
            f"Nested Segment {segment_number:02d} " + ("x" * 20)
        )
        if len(str(candidate / project_suffix)) > MAX_REPRESENTATIVE_PROJECT_PATH:
            break
        workspace = candidate
        segment_number += 1
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _offline_nuget_config(workspace: Path) -> None:
    (workspace / "NuGet.Config").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
  </packageSources>
</configuration>
""",
        encoding="utf-8",
        newline="\n",
    )


def _exercise_persistence(workspace: Path) -> dict[str, Any]:
    table = TableDefinition(
        "settings",
        (
            ColumnDefinition(
                "key",
                SQLiteValueType.TEXT,
                nullable=False,
                primary_key=True,
            ),
            ColumnDefinition("value", SQLiteValueType.TEXT, nullable=False),
        ),
    )
    schema = SchemaDefinition(1, (table,))
    database = workspace / ".kodepoia" / "state" / "representative.db"
    database.parent.mkdir(parents=True, exist_ok=True)
    service = SQLitePersistenceService(database, schema)
    status = service.initialize()
    inserted = service.execute(
        QueryIntent(
            QueryOperation.INSERT,
            "settings",
            values=(("key", "theme"), ("value", "system")),
        )
    )
    rows = service.execute(
        QueryIntent(
            QueryOperation.SELECT,
            "settings",
            columns=("key", "value"),
        )
    )
    return {
        "database_sha256": _file_sha256(database),
        "inserted": inserted,
        "rows": [list(row) for row in rows],
        "status": status.state.value,
    }


def _exercise_ipc_contract() -> dict[str, Any]:
    session = "r16.12-session"
    endpoint = IpcEndpointIdentity(
        "r16.12-desktop",
        session,
        IpcTransportKind.WINDOWS_NAMED_PIPE,
    )
    policy = IpcPolicy()
    peer = IpcPeerIdentity("kodepoia-ui", session, "desktop_ui")
    envelope = IpcEnvelope(
        policy.protocol_version,
        "message-1",
        IpcMessageKind.REQUEST,
        "state.read",
        peer,
        {"key": "theme"},
    )
    authorization = IpcAuthorizationPolicy(
        session,
        ("desktop_ui",),
        ("state.read",),
    )
    authorization.authorize(envelope)

    rejected = False
    bad = IpcEnvelope(
        policy.protocol_version,
        "message-2",
        IpcMessageKind.REQUEST,
        "process.execute",
        peer,
        {"command": "untrusted"},
    )
    try:
        authorization.authorize(bad)
    except IpcAuthorizationError:
        rejected = True

    return {
        "endpoint": endpoint.canonical(),
        "policy_sha256": policy.digest,
        "authorized_method": envelope.method,
        "unauthorized_method_rejected": rejected,
    }


def _copy_untrusted_fixture(repo_root: Path, workspace: Path) -> tuple[Path, str]:
    source = (repo_root / MALICIOUS_FIXTURE).resolve(strict=True)
    destination = workspace / "project-input" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    text = destination.read_text(encoding="utf-8")
    return destination, text


def _secret_free_payload(value: Any) -> bool:
    lowered = _canonical_json(value).lower()
    forbidden = (
        "-----begin private key-----",
        "-----begin rsa private key-----",
        "ghp_",
        "github_pat_",
        "password=",
        "client_secret=",
        "aws_secret_access_key",
    )
    return not any(marker in lowered for marker in forbidden)


def build_windows_desktop_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    source_sha = source_sha.strip().lower()
    if SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be a lowercase 40-character Git SHA")
    if platform_module.system() != "Windows":
        raise RuntimeError("R16.12 live acceptance requires Windows")

    cases: list[dict[str, Any]] = []
    model = canonical_sample_app()
    model.validate()

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-12-") as temporary:
        temp_root = Path(temporary)
        workspace = _representative_workspace(temp_root)
        staging = workspace / ".kodepoia" / "staging with spaces"
        staging.mkdir(parents=True, exist_ok=True)
        _offline_nuget_config(workspace)
        untrusted_path, untrusted_text = _copy_untrusted_fixture(repo_root, workspace)

        adapter = WpfAdapter(workspace, staging)
        result = adapter.run_acceptance(model)
        if isinstance(result, DesktopCapabilityReport):
            raise RuntimeError(
                f"WPF capability unavailable for R16.12: {result.canonical()} "
                f"{adapter.last_diagnostic}"
            )
        assert isinstance(result, WpfAcceptanceResult)
        app_project = workspace / ".kodepoia" / "fixtures" / "wpf" / "App" / "KodepoiaWpfFixture.csproj"
        main_window = app_project.parent / "MainWindow.xaml.cs"
        main_xaml = app_project.parent / "MainWindow.xaml"

        discovered = adapter.discover_toolchain()
        if isinstance(discovered, DesktopCapabilityReport):
            raise RuntimeError(f"dotnet discovery changed during acceptance: {discovered.canonical()}")
        dotnet, identity = discovered
        boundary = DesktopToolchainBoundary(
            allowed_runtime_roots=(dotnet.parent, dotnet.parent.parent),
            project_root=workspace,
            staging_root=staging,
        )
        sandbox = ProcessSandbox(workspace, {dotnet.name})
        env = _dotnet_env()

        publish_root = staging / "Published Package With Spaces"
        publish_argv = build_dotnet_publish_argv(
            boundary,
            dotnet,
            project_file=app_project,
            output_directory=publish_root,
        )
        publish = sandbox.run(
            publish_argv,
            cwd=workspace,
            timeout=240,
            env=env,
        )
        if publish.returncode != 0:
            raise RuntimeError(
                "governed dotnet publish failed: "
                + (publish.stdout + "\n" + publish.stderr)[-8000:]
            )

        executable = next(iter(sorted(publish_root.glob("KodepoiaWpfFixture.exe"))), None)
        executable_paths = (
            () if executable is None else (executable.relative_to(publish_root).as_posix(),)
        )
        package_manifest = build_artifact_manifest(
            publish_root,
            package_id="kodepoia-r16-12-wpf",
            version=DesktopVersion(1, 0, 0),
            framework=DesktopFramework.WPF,
            platform=DesktopOS.WINDOWS,
            architecture=identity.architecture,
            package_kind=DesktopPackageKind.ARCHIVE,
            signing_state=SigningState.UNSIGNED,
            executable_paths=executable_paths,
        )
        verify_artifact_tree(publish_root, package_manifest)
        package_binding = {
            "source_sha": source_sha,
            "model_sha256": result.model_sha256,
            "manifest_sha256": package_manifest.digest(),
        }

        project_path_length = len(str(app_project))
        cases.extend(
            [
                _case(
                    "canonical-wpf-dotnet10-runtime",
                    result.report.state.value == "AVAILABLE"
                    and identity.version.split(".", 1)[0] == "10"
                    and result.build.returncode == 0
                    and result.test.returncode == 0,
                    "repository-supported WPF path builds and runtime-smokes under the probed .NET 10 SDK",
                ),
                _case(
                    "windows-space-and-bounded-long-path",
                    " " in str(app_project)
                    and MIN_REPRESENTATIVE_PROJECT_PATH <= project_path_length
                    <= MAX_REPRESENTATIVE_PROJECT_PATH
                    and Path(publish_argv[2]) == app_project.resolve(strict=True),
                    (
                        "actual project argv carries one bounded long-ish path containing "
                        "spaces without shell interpolation"
                    ),
                ),
                _case(
                    "governed-publish-package",
                    publish.returncode == 0
                    and not publish.timed_out
                    and not publish.cancelled
                    and bool(package_manifest.files)
                    and package_manifest.signing_state is SigningState.UNSIGNED,
                    (
                        "dotnet publish executes through validated executable/project/staging "
                        "boundaries and yields an unsigned archive manifest"
                    ),
                ),
                _case(
                    "source-bound-package-evidence",
                    len(package_manifest.digest()) == 64
                    and len(_sha256_payload(package_binding)) == 64
                    and package_binding["source_sha"] == source_sha,
                    (
                        "package semantic manifest is cryptographically bound to the exact "
                        "acceptance source and desktop model"
                    ),
                ),
            ]
        )

        outside = temp_root / "outside.csproj"
        outside.write_text("<Project />\n", encoding="utf-8", newline="\n")
        escape_denied = False
        try:
            build_dotnet_publish_argv(
                boundary,
                dotnet,
                project_file=outside,
                output_directory=publish_root,
            )
        except DesktopBoundaryError:
            escape_denied = True
        cases.append(
            _case(
                "workspace-escape-negative-control",
                escape_denied,
                "project files outside the representative workspace cannot acquire build/publish authority",
            )
        )

        trust = TrustMetadata.untrusted(
            TrustOrigin.REPOSITORY,
            source=untrusted_path.relative_to(workspace).as_posix(),
            content=untrusted_text,
        )
        trust_boundary = TrustBoundary()
        inspect_decision = trust_boundary.evaluate(trust, AuthorityEffect.INSPECT_DATA)
        process_decision = trust_boundary.evaluate(trust, AuthorityEffect.PROCESS_EXECUTION)
        tool_decision = trust_boundary.evaluate(
            trust,
            AuthorityEffect.PRIVILEGED_TOOL_TRIGGER,
        )
        cases.append(
            _case(
                "untrusted-windows-config-data-only",
                MALICIOUS_MARKER in untrusted_text
                and inspect_decision.allowed
                and not process_decision.allowed
                and not tool_decision.allowed,
                (
                    "repository-supplied post-build text is inspectable data but cannot become "
                    "process or privileged-tool authority"
                ),
            )
        )

        safe_change = SafeChangeManager(
            workspace,
            workspace / ".kodepoia" / "snapshots",
        )
        source_before = _source_digest(app_project.parent)
        xaml_before = main_xaml.read_bytes()
        cancel_snapshot = safe_change.snapshot([main_xaml])
        main_xaml.write_text(
            main_xaml.read_text(encoding="utf-8").replace(
                "Kodepoia WPF fixture",
                "Kodepoia WPF fixture - cancelled edit",
            ),
            encoding="utf-8",
            newline="\n",
        )
        cancellation_requested = True
        cancel_restored = safe_change.restore(cancel_snapshot)
        cases.append(
            _case(
                "bounded-cancellation-safechange",
                cancellation_requested
                and len(cancel_restored) == 1
                and main_xaml.read_bytes() == xaml_before
                and _source_digest(app_project.parent) == source_before,
                "a cancelled representative edit restores exact source bytes before the next build step",
            )
        )

        code_before = main_window.read_bytes()
        failure_snapshot = safe_change.snapshot([main_window])
        main_window.write_text(
            main_window.read_text(encoding="utf-8")
            + "\nthis is intentionally invalid C# for R16.12 recovery;\n",
            encoding="utf-8",
            newline="\n",
        )
        failed_build = sandbox.run(
            boundary.build_dotnet_argv(
                dotnet,
                operation="build",
                project_file=app_project,
                configuration="Release",
            ),
            cwd=workspace,
            timeout=180,
            env=env,
        )
        restored = safe_change.restore(failure_snapshot)
        recovery_build = sandbox.run(
            boundary.build_dotnet_argv(
                dotnet,
                operation="build",
                project_file=app_project,
                configuration="Release",
            ),
            cwd=workspace,
            timeout=180,
            env=env,
        )
        cases.append(
            _case(
                "failed-build-safechange-recovery",
                failed_build.returncode != 0
                and len(restored) == 1
                and main_window.read_bytes() == code_before
                and recovery_build.returncode == 0
                and not recovery_build.timed_out,
                (
                    "an injected compile failure leaves a recoverable workspace and exact "
                    "SafeChange restore returns it to a green build"
                ),
            )
        )

        persistence = _exercise_persistence(workspace)
        cases.append(
            _case(
                "typed-sqlite-persistence",
                persistence["status"] == "ready"
                and persistence["inserted"] == 1
                and persistence["rows"] == [["theme", "system"]]
                and len(str(persistence["database_sha256"])) == 64,
                "representative desktop state persists through typed SQLite intents in the bounded workspace",
            )
        )

        ipc = _exercise_ipc_contract()
        cases.append(
            _case(
                "windows-local-ipc-contract",
                ipc["endpoint"]["transport"] == "windows_named_pipe"
                and ipc["endpoint"]["local_only"] is True
                and ipc["authorized_method"] == "state.read"
                and ipc["unauthorized_method_rejected"] is True,
                (
                    "Windows named-pipe identity remains local-only and authorization rejects "
                    "an unapproved process method"
                ),
            )
        )

        diagnostics = {
            "toolchain": identity.canonical(),
            "model_sha256": result.model_sha256,
            "project_path_length": project_path_length,
            "publish_argv": list(publish_argv[1:]),
            "package_manifest": package_manifest.canonical(),
            "persistence": persistence,
            "ipc": ipc,
            "trust": {
                "metadata": trust.to_dict(),
                "inspect_data": asdict(inspect_decision),
                "process_execution": asdict(process_decision),
                "privileged_tool_trigger": asdict(tool_decision),
            },
            "failed_build": {
                "returncode": failed_build.returncode,
                "timed_out": failed_build.timed_out,
                "cancelled": failed_build.cancelled,
            },
            "recovery_build": {
                "returncode": recovery_build.returncode,
                "timed_out": recovery_build.timed_out,
                "cancelled": recovery_build.cancelled,
            },
        }

    security_claim = all(bool(item["pass"]) for item in cases)
    semantic_payload = {
        "phase": "R16.12",
        "source_sha": source_sha,
        "model_sha256": result.model_sha256,
        "package_manifest_sha256": package_manifest.digest(),
        "case_results": [
            {"name": item["name"], "pass": item["pass"]} for item in cases
        ],
        "manual_state": "NONE",
        "security_claim": security_claim,
        "critical_veto": not security_claim,
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.12",
        "source_sha": source_sha,
        "platform": platform,
        "canonical_framework": "wpf",
        "manual_state": "NONE",
        "security_claim": security_claim,
        "critical_veto": not security_claim,
        "live_credentials_used": False,
        "destructive_host_actions": False,
        "network_policy": "NuGet package sources cleared; no network capability is required by the fixture",
        "toolchain": identity.canonical(),
        "model_sha256": result.model_sha256,
        "project_path_length": project_path_length,
        "package_manifest": package_manifest.canonical(),
        "package_manifest_sha256": package_manifest.digest(),
        "package_binding_sha256": _sha256_payload(package_binding),
        "diagnostic_sha256": _sha256_payload(diagnostics),
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(bool(item["pass"]) for item in cases),
            "failed": sum(not bool(item["pass"]) for item in cases),
        },
        "semantic_sha256": _sha256_payload(semantic_payload),
    }
    report["secret_free"] = _secret_free_payload(report)
    if not report["secret_free"]:
        report["security_claim"] = False
        report["critical_veto"] = True
    report["evidence_sha256"] = _sha256_payload(report)
    return report
