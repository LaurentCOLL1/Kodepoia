from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.cli import build_parser
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.kodestudio.r13_localization import PSEUDO_LOCALE, R13Translator
from kodepoia.mobile.contracts import MobilePackageKind, MobileSourceKind
from kodepoia.mobile.workspace import (
    MobileExecutionReceipt,
    MobileWorkspaceOperation,
    MobileWorkspaceService,
    MobileWorkspaceState,
)
from kodepoia.project.dna import (
    MobileNetworkIntent,
    MobileProjectProfile,
    MobileReleaseChannel,
    MobileSigningIntent,
    Platform,
    ProjectDNA,
    ProjectType,
)


def _write_mobile_project(root: Path) -> ProjectDNA:
    dna = ProjectDNA(
        schema_version=1,
        name="R13MobileFixture",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID],
        inputs=["touch"],
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.NATIVE,
            android_application_id="com.kodepoia.r13fixture",
            android_min_api=26,
            android_target_api=36,
            package_kinds=(MobilePackageKind.AAB,),
            network_intent=MobileNetworkIntent.OPTIONAL,
            release_channel=MobileReleaseChannel.BETA,
            signing_intent=MobileSigningIntent.TEST,
        ),
    )
    dna.save(root / ".kodepoia" / "project.yaml")
    return dna


def test_passive_status_never_calls_executor_and_does_not_upgrade_evidence_to_pass(
    tmp_path: Path,
) -> None:
    _write_mobile_project(tmp_path)
    evidence_dir = tmp_path / ".kodepoia" / "mobile" / "evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "compliance.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "evidence_id": "untrusted-reported-pass",
                "source_digest": "sha256:fixture",
            }
        ),
        encoding="utf-8",
    )
    calls: list[MobileWorkspaceOperation] = []

    def executor(operation, context, kill_switch):
        calls.append(operation)
        raise AssertionError("passive status must not call the execution backend")

    result = MobileWorkspaceService(tmp_path, executor=executor).status()

    assert calls == []
    assert result.state is MobileWorkspaceState.READY
    assert result.state is not MobileWorkspaceState.PASS
    payload = result.to_dict()
    assert payload["capability_matrix"]["passive_refresh"] == {
        "state": "AVAILABLE",
        "external_process_launch": False,
        "network_access": False,
        "read_only": True,
    }
    assert payload["evidence"]["compliance"] == {
        "available": True,
        "read_only": True,
        "reported_status": "pass",
        "evidence_id": "untrusted-reported-pass",
        "source_digest": "sha256:fixture",
    }


def test_execution_without_governed_backend_is_explicitly_blocked(tmp_path: Path) -> None:
    _write_mobile_project(tmp_path)

    result = MobileWorkspaceService(tmp_path).execute(MobileWorkspaceOperation.BUILD)

    assert result.state is MobileWorkspaceState.BLOCKED
    assert result.blockers == ("EXECUTION_BACKEND_UNAVAILABLE",)
    assert result.ok is False
    assert result.to_dict()["capability_matrix"]["build"]["state"] == "BLOCKED"


def test_global_kill_switch_cancels_before_executor_is_called(tmp_path: Path) -> None:
    _write_mobile_project(tmp_path)
    switch = KillSwitch()
    switch.trigger()
    calls: list[MobileWorkspaceOperation] = []

    def executor(operation, context, kill_switch):
        calls.append(operation)
        return MobileExecutionReceipt(MobileWorkspaceState.PASS, "unexpected")

    result = MobileWorkspaceService(
        tmp_path,
        executor=executor,
        kill_switch=switch,
    ).execute(MobileWorkspaceOperation.TEST)

    assert calls == []
    assert result.state is MobileWorkspaceState.CANCELLED
    assert result.blockers == ("KILL_SWITCH_ACTIVE",)


def test_structured_executor_receives_bounded_project_intent(tmp_path: Path) -> None:
    _write_mobile_project(tmp_path)
    received: dict[str, object] = {}

    def executor(operation, context, kill_switch):
        received.update(
            {
                "operation": operation,
                "project_root": context.project_root,
                "project_name": context.project_name,
                "platforms": context.platforms,
                "source_kind": context.source_kind,
                "package_kinds": context.package_kinds,
                "release_channel": context.release_channel,
                "signing_intent": context.signing_intent,
                "network_intent": context.network_intent,
                "kill_switch": kill_switch,
            }
        )
        return MobileExecutionReceipt(
            MobileWorkspaceState.PASS,
            "governed execution passed",
            evidence=(("run_id", "fixture-run"),),
        )

    switch = KillSwitch()
    result = MobileWorkspaceService(
        tmp_path,
        executor=executor,
        kill_switch=switch,
    ).execute(MobileWorkspaceOperation.PACKAGE)

    assert result.state is MobileWorkspaceState.PASS
    assert result.blockers == ()
    assert result.to_dict()["evidence"] == {"run_id": "fixture-run"}
    assert received == {
        "operation": MobileWorkspaceOperation.PACKAGE,
        "project_root": tmp_path.resolve(strict=False),
        "project_name": "R13MobileFixture",
        "platforms": ("android",),
        "source_kind": "native",
        "package_kinds": ("aab",),
        "release_channel": "beta",
        "signing_intent": "test",
        "network_intent": "optional",
        "kill_switch": switch,
    }


def test_invalid_or_non_mobile_project_is_blocked(tmp_path: Path) -> None:
    result = MobileWorkspaceService(tmp_path).status()
    assert result.state is MobileWorkspaceState.BLOCKED
    assert result.blockers == ("PROJECT_DNA_MISSING",)

    ProjectDNA(
        schema_version=1,
        name="DesktopFixture",
        project_type=ProjectType.TOOL,
        platforms=[Platform.WINDOWS],
    ).save(tmp_path / ".kodepoia" / "project.yaml")
    result = MobileWorkspaceService(tmp_path).status()
    assert result.state is MobileWorkspaceState.BLOCKED
    assert result.blockers == ("MOBILE_PROFILE_MISSING",)


def test_r13_cli_has_only_structured_project_input() -> None:
    parser = build_parser()
    args = parser.parse_args(["r13", "status", "--project", "."])
    assert args.command == "r13"
    assert args.r13_operation == "status"

    with pytest.raises(SystemExit):
        parser.parse_args(["r13", "build", "--executable", "gradle", "--project", "."])
    with pytest.raises(SystemExit):
        parser.parse_args(["r13", "release", "--store-token", "secret", "--project", "."])
    with pytest.raises(SystemExit):
        parser.parse_args(["r13", "test", "--argv", "adb shell", "--project", "."])


def test_r13_pseudo_localization_expands_workspace_labels() -> None:
    source = R13Translator().text("r13.title")
    pseudo = R13Translator(PSEUDO_LOCALE).text("r13.title")
    assert pseudo != source
    assert len(pseudo) > len(source)
    assert R13Translator("fr").text("r13.refresh") == "Refresh status"
