from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from kodepoia.assets.contracts import AssetKind
from kodepoia.assets.search import SearchFilters
from kodepoia.assets.service import AssetCancellationToken, AssetOperationCancelled, AssetService
from kodepoia.cli import build_parser


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    return root


def test_asset_service_is_shared_read_surface_and_unknown_license_is_visible(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "hero.txt").write_text("hero texture notes", encoding="utf-8")

    with AssetService(root) as service:
        detail = service.ingest("hero.txt", kind=AssetKind.DOCUMENT, project_id="fixture")
        assert detail.summary.status == "ready"
        assert detail.summary.license_state == "unknown"
        assert detail.summary.license_token == "NOASSERTION"

        listed = service.list_assets()
        assert len(listed) == 1
        assert listed[0].revision_id == detail.summary.revision_id

        # Governance-blocked/unknown assets are excluded by default, but the UX
        # can explicitly display them without changing their policy state.
        assert service.search("hero") == ()
        hits = service.search("hero", filters=SearchFilters(include_blocked=True))
        assert len(hits) == 1
        assert hits[0].summary.revision_id == detail.summary.revision_id

        plan = service.export_plan("fixture")
        assert plan["allowed"] is False
        assert plan["blockers"]


def test_exact_duplicates_are_candidates_not_destructive_merges(tmp_path: Path) -> None:
    root = _project(tmp_path)
    payload = "same canonical bytes\n"
    (root / "a.txt").write_text(payload, encoding="utf-8")
    (root / "b.txt").write_text(payload, encoding="utf-8")

    with AssetService(root) as service:
        first = service.ingest("a.txt", kind=AssetKind.DOCUMENT)
        second = service.ingest("b.txt", kind=AssetKind.DOCUMENT)
        report = service.duplicate_candidates()
        assert len(report["exact_groups"]) == 1
        assert set(report["exact_groups"][0]) == {
            first.summary.revision_id,
            second.summary.revision_id,
        }
        assert len(service.list_assets()) == 2


def test_rebuild_respects_pre_cancel_without_persisting_search_work(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "asset.txt").write_text("asset", encoding="utf-8")
    with AssetService(root) as service:
        service.ingest("asset.txt", kind=AssetKind.DOCUMENT)
        before = int(service.search_index.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
        token = AssetCancellationToken()
        token.cancel()
        with pytest.raises(AssetOperationCancelled):
            service.rebuild(token=token)
        after = int(service.search_index.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
        assert after == before


def test_materialize_overwrite_requires_explicit_confirmation(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "source.txt").write_text("source", encoding="utf-8")
    target = root / "materialized.txt"
    target.write_text("existing", encoding="utf-8")

    with AssetService(root) as service:
        detail = service.ingest("source.txt", kind=AssetKind.DOCUMENT)
        revision_id = detail.summary.revision_id
        assert revision_id is not None
        with pytest.raises(PermissionError):
            service.materialize(revision_id, "materialized.txt", overwrite=True)
        report = service.materialize(
            revision_id,
            "materialized.txt",
            overwrite=True,
            confirmed=True,
        )
        assert report["overwritten"] is True
        assert target.read_text(encoding="utf-8") == "source"


def test_cli_registers_full_asset_command_surface() -> None:
    parser = build_parser()
    commands = (
        "status", "doctor", "ingest", "list", "show", "search", "duplicates", "lineage",
        "rebuild", "materialize", "delete-plan", "delete", "export-plan", "export",
        "vcs-status", "lfs-doctor", "repository-evidence",
    )
    for command in commands:
        tail = {
            "ingest": ["x.bin"],
            "show": ["rev_" + "0" * 32],
            "search": ["hero"],
            "lineage": ["rev_" + "0" * 32],
            "materialize": ["rev_" + "0" * 32, "out.bin"],
            "delete-plan": ["rev_" + "0" * 32],
            "delete": ["rev_" + "0" * 32, "--confirm"],
            "export-plan": ["fixture"],
            "export": ["fixture", "exported", "--confirm"],
            "repository-evidence": ["rev_" + "0" * 32],
        }.get(command, [])
        args = parser.parse_args(["asset", command, *tail])
        assert callable(args.func)


def test_vault_panel_has_no_direct_git_process_socket_or_secret_adapter_imports() -> None:
    import kodepoia.kodestudio.vault_panel as vault_panel

    source = inspect.getsource(vault_panel)
    forbidden = (
        "from kodepoia.assets.vcs import",
        "from kodepoia.assets.lfs import",
        "ProcessSandbox",
        "import subprocess",
        "import socket",
        "KodeSecrets",
    )
    assert not any(item in source for item in forbidden)
    assert "AssetService" in source
