from __future__ import annotations

from pathlib import Path

from kodepoia.kodestudio.preferences import ApplicationPreferences

PROJECT_MARKER = Path(".kodepoia") / "project.yaml"
PRODUCT_MARKER = Path("product") / "product.yaml"
ACTIVE_PROJECT_KEY = "active_project_root"
RECENT_PROJECTS_KEY = "recent_projects"
MAX_RECENT_PROJECTS = 12


def canonical_project_root(value: Path | str) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def is_kodepoia_project(value: Path | str) -> bool:
    root = canonical_project_root(value)
    return root.is_dir() and (root / PROJECT_MARKER).is_file()


def validate_project_root(value: Path | str) -> Path:
    root = canonical_project_root(value)
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    if not (root / PROJECT_MARKER).is_file():
        raise ValueError(
            "This folder is not a Kodepoia project: missing .kodepoia/project.yaml"
        )
    return root


def recent_project_roots(
    preferences: ApplicationPreferences,
    *,
    include_missing: bool = False,
    limit: int = MAX_RECENT_PROJECTS,
) -> list[Path]:
    raw = preferences.get(RECENT_PROJECTS_KEY, [])
    if not isinstance(raw, list):
        return []
    result: list[Path] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str) or not value.strip():
            continue
        root = canonical_project_root(value)
        key = str(root).casefold()
        if key in seen:
            continue
        if include_missing or is_kodepoia_project(root):
            result.append(root)
            seen.add(key)
        if len(result) >= max(0, limit):
            break
    return result


def active_project_root(preferences: ApplicationPreferences) -> Path | None:
    raw = preferences.get(ACTIVE_PROJECT_KEY)
    if not isinstance(raw, str) or not raw.strip():
        return None
    root = canonical_project_root(raw)
    return root if is_kodepoia_project(root) else None


def remember_project(
    preferences: ApplicationPreferences,
    value: Path | str,
    *,
    make_active: bool = True,
    limit: int = MAX_RECENT_PROJECTS,
) -> Path:
    root = validate_project_root(value)
    existing = recent_project_roots(preferences, include_missing=True, limit=max(limit, 1) * 2)
    canonical_key = str(root).casefold()
    recent = [root]
    recent.extend(item for item in existing if str(item).casefold() != canonical_key)
    payload: dict[str, object] = {
        RECENT_PROJECTS_KEY: [str(item) for item in recent[: max(1, limit)]],
    }
    if make_active:
        payload[ACTIVE_PROJECT_KEY] = str(root)
    preferences.update(payload)
    return root


def forget_recent_project(preferences: ApplicationPreferences, value: Path | str) -> None:
    root = canonical_project_root(value)
    target = str(root).casefold()
    recent = [
        item
        for item in recent_project_roots(preferences, include_missing=True)
        if str(item).casefold() != target
    ]
    payload: dict[str, object] = {RECENT_PROJECTS_KEY: [str(item) for item in recent]}
    active = preferences.get(ACTIVE_PROJECT_KEY)
    if isinstance(active, str) and str(canonical_project_root(active)).casefold() == target:
        payload[ACTIVE_PROJECT_KEY] = None
    preferences.update(payload)


def clear_active_project(preferences: ApplicationPreferences) -> None:
    preferences.update({ACTIVE_PROJECT_KEY: None})


__all__ = [
    "ACTIVE_PROJECT_KEY",
    "MAX_RECENT_PROJECTS",
    "PRODUCT_MARKER",
    "PROJECT_MARKER",
    "RECENT_PROJECTS_KEY",
    "active_project_root",
    "canonical_project_root",
    "clear_active_project",
    "forget_recent_project",
    "is_kodepoia_project",
    "recent_project_roots",
    "remember_project",
    "validate_project_root",
]
