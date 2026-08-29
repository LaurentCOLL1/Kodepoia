from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.backend import r14_cli
from kodepoia.backend.liveops_ux import BackendLiveOpsUXService
from kodepoia.cli import build_parser


def invoke(argv: list[str]) -> tuple[int, dict[str, object]]:
    args = build_parser().parse_args(argv)
    code = int(args.func(args))
    return code, args


def test_backend_liveops_catalog_is_machine_readable_and_stable(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        ["backend-liveops", "catalog", "--project-root", str(tmp_path)]
    )
    assert args.func(args) == 0
    text = capsys.readouterr().out
    payload = json.loads(text)
    assert payload["schema"] == "kodepoia.r14.liveops-ux.v1"
    assert payload["status"] == "ok"
    assert "backend_profile" in payload["operations"]
    assert "campaign" in payload["operations"]
    assert text == r14_cli.stable_liveops_json(payload) + "\n"


def test_cli_profile_keeps_environment_explicit(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        [
            "backend-liveops",
            "profile",
            "--project-root",
            str(tmp_path),
            "--environment",
            "staging",
        ]
    )
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["environment"] == "staging"
    assert payload["mode"] == "inspect"
    assert payload["result"]["authority_source"] == "project_local_read_only"


def test_cli_mutation_confirmation_cannot_self_grant_permission(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        [
            "backend-liveops",
            "change",
            "config",
            "rollout",
            "--resource-id",
            "flag.release",
            "--confirm",
            "--project-root",
            str(tmp_path),
        ]
    )
    assert args.func(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "domain_permission_denied"


def test_cli_has_no_user_supplied_permission_grant_escape_hatch() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "backend-liveops",
                "change",
                "content",
                "rollout",
                "--resource-id",
                "content.release",
                "--confirm",
                "--permission-granted",
            ]
        )


def test_cli_rejects_raw_endpoint_resource_as_policy_block(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        [
            "backend-liveops",
            "inspect",
            "save",
            "--resource-id",
            "https://example.invalid/save/1",
            "--project-root",
            str(tmp_path),
        ]
    )
    assert args.func(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "policy_error"
    assert "endpoint" in payload["detail"]


def test_cli_provider_missing_is_unavailable_not_pass(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        [
            "backend-liveops",
            "provider-status",
            "--project-root",
            str(tmp_path),
        ]
    )
    assert args.func(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "unavailable"
    assert payload["result"]["provider_live_claim"] is False


def test_cli_stack_start_is_blocked_outside_local_test_before_domain_call(tmp_path: Path, capsys) -> None:
    args = build_parser().parse_args(
        [
            "backend-liveops",
            "stack",
            "start",
            "--project-root",
            str(tmp_path),
            "--environment",
            "production",
            "--confirm",
        ]
    )
    assert args.func(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "local_stack_mutation_forbidden_outside_local_test"
