from __future__ import annotations

import json

import pytest

from kodepoia.cli import build_parser


def test_r15_cli_help_surface_and_argument_validation() -> None:
    parser = build_parser()
    args = parser.parse_args(["r15", "catalog"])
    assert args.func is not None

    with pytest.raises(SystemExit):
        parser.parse_args(["r15", "training", "run"])


def test_r15_cli_mutation_is_dry_run_without_apply(tmp_path, capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "r15",
            "training",
            "run",
            "--project-root",
            str(tmp_path),
            "--id",
            "train.plan.1",
        ]
    )
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run"
    assert payload["workflow"] == "training.run"
    assert payload["would_mutate"] is True


def test_r15_cli_apply_requires_backend_even_after_confirmation(tmp_path, capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "r15",
            "registry",
            "promote",
            "--project-root",
            str(tmp_path),
            "--id",
            "candidate.1",
            "--apply",
            "--confirm",
        ]
    )
    assert args.func(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert "backend is not configured" in payload["detail"]


def test_r15_cli_evidence_export_is_project_relative(tmp_path, capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "r15",
            "evidence",
            "--project-root",
            str(tmp_path),
            "--output",
            ".kodepoia/tuning/r15-ui.json",
        ]
    )
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["output"] == ".kodepoia/tuning/r15-ui.json"
    assert (tmp_path / payload["output"]).is_file()
