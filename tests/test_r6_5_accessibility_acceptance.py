from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.quality.accessibility import (
    AccessibilityResult,
    AccessibilityStatus,
    AccessibilityStore,
    KodeAccessibility,
)
from kodepoia.quality.accessibility_acceptance import MANUAL_CHECKS, finalize


HEAD = "a" * 40


def _pass_report(surface: str):
    return KodeAccessibility.evaluate(
        [
            AccessibilityResult(
                rule_id="qt.name.explicit",
                target_id="fixture",
                status=AccessibilityStatus.PASS,
                summary="fixture pass",
                evidence={"source": "test"},
            )
        ],
        surface=surface,
        generated_at="2026-08-22T10:20:00Z",
    )


def _seed(repo: Path) -> tuple[Path, dict[str, object]]:
    root = repo / ".kodepoia" / "diagnostics" / "accessibility"
    root.mkdir(parents=True)
    store = AccessibilityStore(repo)
    main = _pass_report("kodestudio-main")
    wizard = _pass_report("kodestudio-project-wizard")
    main_path, _ = store.save(main, snapshot=False)
    wizard_path, _ = store.save(wizard, snapshot=False)
    manifest = {
        "schema_version": 1,
        "phase": "R6.5-local-acceptance",
        "generated_at": "2026-08-22T10:20:00Z",
        "source_head": HEAD,
        "platform": "fixture",
        "python": "3.12.4",
        "automated_pass": True,
        "automated_reports": [
            {
                "surface": main.surface,
                "status": main.status.value,
                "counts": main.counts,
                "evidence_sha256": main.evidence_sha256,
                "path": main_path.relative_to(repo).as_posix(),
            },
            {
                "surface": wizard.surface,
                "status": wizard.status.value,
                "counts": wizard.counts,
                "evidence_sha256": wizard.evidence_sha256,
                "path": wizard_path.relative_to(repo).as_posix(),
            },
        ],
        "manual_checks": [check.to_dict() for check in MANUAL_CHECKS],
        "narrator_shortcuts": {
            "toggle": "Win+Ctrl+Enter",
            "speech_recap": "Narrator+Alt+X",
        },
    }
    (root / "r6-5-manual-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return root, manifest


def _responses(*, failed_id: str | None = None, source_head: str = HEAD) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_head": source_head,
        "responses": {
            check.id: {
                "status": "fail" if check.id == failed_id else "pass",
                "note": "fixture failure" if check.id == failed_id else "",
            }
            for check in MANUAL_CHECKS
        },
    }


def _write_responses(root: Path, payload: dict[str, object]) -> Path:
    path = root / "r6-5-manual-responses.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_finalize_accepts_exact_head_complete_all_pass_evidence(tmp_path: Path) -> None:
    root, _ = _seed(tmp_path)
    response_path = _write_responses(root, _responses())
    result = finalize(tmp_path, source_head=HEAD, responses_path=response_path)

    assert result["metadata"]["acceptance_completed"] is True
    assert result["metadata"]["source_head"] == HEAD
    assert result["automated"]["passed"] is True
    assert result["manual"]["total"] == len(MANUAL_CHECKS) == 13
    assert result["manual"]["passed"] == 13
    assert result["manual"]["failed"] == 0
    assert result["manual"]["blocking_failures"] == 0
    assert result["summary"] == {"failed": 0, "passed": 15, "total": 15}
    assert result["output_path"] == ".kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json"


def test_one_manual_failure_blocks_acceptance(tmp_path: Path) -> None:
    root, _ = _seed(tmp_path)
    response_path = _write_responses(
        root,
        _responses(failed_id="focus.visible"),
    )
    result = finalize(tmp_path, source_head=HEAD, responses_path=response_path)

    assert result["metadata"]["acceptance_completed"] is False
    assert result["manual"]["passed"] == 12
    assert result["manual"]["failed"] == 1
    assert result["manual"]["blocking_failures"] == 1
    assert result["summary"] == {"failed": 1, "passed": 14, "total": 15}


def test_missing_manual_check_is_rejected(tmp_path: Path) -> None:
    root, _ = _seed(tmp_path)
    payload = _responses()
    payload["responses"].pop("narrator.wizard_actions")
    response_path = _write_responses(root, payload)

    with pytest.raises(ValueError, match="manual response IDs mismatch"):
        finalize(tmp_path, source_head=HEAD, responses_path=response_path)


def test_wrong_source_head_is_rejected(tmp_path: Path) -> None:
    root, _ = _seed(tmp_path)
    response_path = _write_responses(root, _responses(source_head="b" * 40))

    with pytest.raises(ValueError, match="different source head"):
        finalize(tmp_path, source_head=HEAD, responses_path=response_path)


def test_manifest_source_head_mismatch_is_rejected(tmp_path: Path) -> None:
    root, manifest = _seed(tmp_path)
    manifest["source_head"] = "c" * 40
    (root / "r6-5-manual-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    response_path = _write_responses(root, _responses())

    with pytest.raises(ValueError, match="manifest source head"):
        finalize(tmp_path, source_head=HEAD, responses_path=response_path)


def test_outside_workspace_responses_are_rejected(tmp_path: Path) -> None:
    _seed(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-responses.json"
    outside.write_text(json.dumps(_responses()), encoding="utf-8")

    with pytest.raises(WorkspaceViolation, match="escapes workspace"):
        finalize(tmp_path, source_head=HEAD, responses_path=outside)


def test_responses_inside_workspace_but_outside_evidence_directory_are_rejected(tmp_path: Path) -> None:
    _seed(tmp_path)
    response_path = tmp_path / ".kodepoia" / "wrong-responses.json"
    response_path.write_text(json.dumps(_responses()), encoding="utf-8")

    with pytest.raises(ValueError, match="accessibility evidence directory"):
        finalize(tmp_path, source_head=HEAD, responses_path=response_path)


def test_changed_automated_report_hash_is_rejected(tmp_path: Path) -> None:
    root, _ = _seed(tmp_path)
    store = AccessibilityStore(tmp_path)
    changed = KodeAccessibility.evaluate(
        [
            AccessibilityResult(
                rule_id="qt.name.explicit",
                target_id="fixture",
                status=AccessibilityStatus.PASS,
                summary="changed after manifest",
                evidence={"source": "tampered"},
            )
        ],
        surface="kodestudio-main",
        generated_at="2026-08-22T10:21:00Z",
    )
    store.save(changed, snapshot=False)
    response_path = _write_responses(root, _responses())

    with pytest.raises(ValueError, match="changed after manual manifest"):
        finalize(tmp_path, source_head=HEAD, responses_path=response_path)
