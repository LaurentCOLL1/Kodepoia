from pathlib import Path

import pytest

from kodepoia.kodestudio.preferences import ApplicationPreferences
from kodepoia.kodestudio.project_sessions import (
    active_project_root,
    forget_recent_project,
    is_kodepoia_project,
    recent_project_roots,
    remember_project,
    validate_project_root,
)


def make_project(root: Path) -> Path:
    (root / ".kodepoia").mkdir(parents=True)
    (root / ".kodepoia" / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    return root


def test_project_marker_validation(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project")
    assert is_kodepoia_project(project)
    assert validate_project_root(project) == project.resolve(strict=False)
    with pytest.raises(ValueError, match="missing .kodepoia/project.yaml"):
        validate_project_root(tmp_path)


def test_remember_project_sets_active_and_deduplicates(tmp_path: Path) -> None:
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    first = make_project(tmp_path / "first")
    second = make_project(tmp_path / "second")

    remember_project(preferences, first)
    remember_project(preferences, second)
    remember_project(preferences, first)

    assert active_project_root(preferences) == first.resolve(strict=False)
    assert recent_project_roots(preferences) == [
        first.resolve(strict=False),
        second.resolve(strict=False),
    ]


def test_missing_project_is_not_restored_as_active(tmp_path: Path) -> None:
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    project = make_project(tmp_path / "project")
    remember_project(preferences, project)
    (project / ".kodepoia" / "project.yaml").unlink()

    assert active_project_root(preferences) is None
    assert recent_project_roots(preferences) == []
    assert recent_project_roots(preferences, include_missing=True) == [project.resolve(strict=False)]


def test_forget_recent_project_clears_matching_active(tmp_path: Path) -> None:
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    project = make_project(tmp_path / "project")
    remember_project(preferences, project)

    forget_recent_project(preferences, project)

    assert active_project_root(preferences) is None
    assert recent_project_roots(preferences, include_missing=True) == []
