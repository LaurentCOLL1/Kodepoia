from __future__ import annotations

import json
from pathlib import Path

from kodepoia.cli import build_parser


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    return root


def test_research_cli_commands_are_registered_with_typed_fetch_kinds() -> None:
    parser = build_parser()
    for argv in (
        ["research-query", "--query", "rendering"],
        ["research-show", "a" * 64],
        ["research-cache", "b" * 64],
        ["research-status"],
        ["research-media-capability"],
        ["research-fetch", "--kind", "local", "--locator", "notes.md"],
        ["research-fetch", "--kind", "official_docs", "--locator", "docs/page.md"],
        ["research-fetch", "--kind", "web", "--locator", "https://example.com"],
    ):
        args = parser.parse_args(argv)
        assert callable(args.func)


def test_research_status_cli_is_json_and_web_is_blocked_by_default(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    monkeypatch.chdir(root)
    args = build_parser().parse_args(["research-status"])
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "status"
    assert payload["status"] == "ready"
    assert payload["metadata"]["capabilities"]["web"]["status"] == "blocked"


def test_research_fetch_web_without_explicit_network_grant_is_blocked(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    monkeypatch.chdir(root)
    args = build_parser().parse_args(
        ["research-fetch", "--kind", "web", "--locator", "https://example.com/docs"]
    )
    assert args.func(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "network_permission_not_granted"


def test_research_fetch_local_cli_roundtrip(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    (root / "notes.md").write_text("# Notes\nFixture evidence.\n", encoding="utf-8")
    monkeypatch.chdir(root)
    args = build_parser().parse_args(
        [
            "research-fetch",
            "--kind",
            "local",
            "--locator",
            "notes.md",
            "--retrieved-at",
            "2026-08-22T20:00:00Z",
        ]
    )
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["items"][0]["source_kind"] == "local"
    artifact_id = payload["items"][0]["artifact_id"]

    show = build_parser().parse_args(["research-show", artifact_id])
    assert show.func(show) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["metadata"]["record_type"] == "artifact"
    assert shown["items"][0]["artifact_id"] == artifact_id
