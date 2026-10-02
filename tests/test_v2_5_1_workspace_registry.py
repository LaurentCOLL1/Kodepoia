from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.orchestrator.workspaces import (
    WorkspaceIdentity,
    WorkspaceRegistry,
    WorkspaceRelationshipKind,
)


def _project(root: Path, name: str) -> Path:
    (root / ".kodepoia").mkdir(parents=True)
    (root / ".kodepoia" / "project.yaml").write_text(
        f"schema_version: 1\nname: {name}\nproject_type: tool\nplatforms:\n  - windows\n",
        encoding="utf-8",
    )
    return root


def test_workspace_identity_is_stable_and_project_scoped(tmp_path: Path) -> None:
    root = _project(tmp_path / "alpha", "Alpha")
    first = WorkspaceIdentity.from_project_root(root)
    second = WorkspaceIdentity.from_project_root(root / ".")

    assert first == second
    assert first.project_scope == f"project:{first.workspace_id}"
    assert first.project_name == "Alpha"
    assert first.canonical_root == str(root.resolve())
    assert len(first.project_marker_sha256) == 64
    assert len(first.digest_sha256) == 64


def test_registry_rejects_duplicate_alias_and_is_bounded(tmp_path: Path) -> None:
    first = _project(tmp_path / "alpha", "Alpha")
    second = _project(tmp_path / "beta", "Beta")
    registry = WorkspaceRegistry(max_workspaces=2)

    registry.register(first)
    with pytest.raises(ValueError, match="alias or duplicate"):
        registry.register(first / ".")
    registry.register(second)

    third = _project(tmp_path / "gamma", "Gamma")
    with pytest.raises(ValueError, match="capacity"):
        registry.register(third)


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlinks unavailable")
def test_registry_rejects_symlink_alias_when_supported(tmp_path: Path) -> None:
    root = _project(tmp_path / "alpha", "Alpha")
    alias = tmp_path / "alpha-link"
    try:
        alias.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted")

    registry = WorkspaceRegistry()
    registry.register(root)
    with pytest.raises(ValueError, match="alias or duplicate"):
        registry.register(alias)


def test_relationships_require_registered_distinct_workspaces(tmp_path: Path) -> None:
    first = _project(tmp_path / "alpha", "Alpha")
    second = _project(tmp_path / "beta", "Beta")
    registry = WorkspaceRegistry()
    alpha = registry.register(first)
    beta = registry.register(second)

    relation = registry.add_relationship(
        alpha.workspace_id,
        beta.workspace_id,
        WorkspaceRelationshipKind.DEPENDS_ON,
        label="shared schema",
    )
    assert relation.source_workspace_id == alpha.workspace_id
    assert relation.destination_workspace_id == beta.workspace_id
    assert registry.relationships() == (relation,)

    with pytest.raises(ValueError, match="distinct"):
        registry.add_relationship(
            alpha.workspace_id,
            alpha.workspace_id,
            WorkspaceRelationshipKind.COMPANION,
        )
    with pytest.raises(KeyError, match="Unknown workspace"):
        registry.add_relationship(
            alpha.workspace_id,
            "missing",
            WorkspaceRelationshipKind.COMPANION,
        )


def test_registry_serialization_is_deterministic(tmp_path: Path) -> None:
    first = _project(tmp_path / "alpha", "Alpha")
    second = _project(tmp_path / "beta", "Beta")
    registry = WorkspaceRegistry()
    alpha = registry.register(first)
    beta = registry.register(second)
    registry.add_relationship(
        beta.workspace_id,
        alpha.workspace_id,
        WorkspaceRelationshipKind.PRODUCES_FOR,
    )

    payload = registry.to_dict()
    assert payload["schema_version"] == 1
    assert len(payload["digest_sha256"]) == 64
    assert {item["project_name"] for item in payload["workspaces"]} == {"Alpha", "Beta"}
    assert payload["relationships"][0]["kind"] == "produces_for"
