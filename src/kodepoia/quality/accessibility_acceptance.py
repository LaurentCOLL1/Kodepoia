from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kodepoia.quality.accessibility import AccessibilityReportStatus, AccessibilityStore


@dataclass(frozen=True, slots=True)
class ManualAccessibilityCheck:
    id: str
    category: str
    instruction: str
    expected: str
    blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "instruction": self.instruction,
            "expected": self.expected,
            "blocking": self.blocking,
        }


MANUAL_CHECKS = (
    ManualAccessibilityCheck(
        "keyboard.main_navigation",
        "keyboard",
        "Using only the keyboard, focus Main navigation and move through Chat, Projects, Security, Audit and Settings.",
        "Every navigation item is reachable/selectable without the mouse and focus never becomes trapped.",
    ),
    ManualAccessibilityCheck(
        "keyboard.project_wizard_open",
        "keyboard",
        "Select Projects, Tab to New project, and activate it using Enter or Space without using the mouse.",
        "The New Kodepoia Project dialog opens from keyboard-only operation.",
    ),
    ManualAccessibilityCheck(
        "keyboard.wizard_general",
        "keyboard",
        "On General, Tab through Name, Directory, Browse, Type, Engine, Engine version, Dimension, Genres, Graphics style, inputs, Online and Multiplayer.",
        "All visible enabled controls are reached in a coherent order without a focus trap.",
    ),
    ManualAccessibilityCheck(
        "keyboard.wizard_sections",
        "keyboard",
        "Use the keyboard to move among General, Platforms & budgets, Features & tools and Product tabs, then traverse their controls.",
        "Every section and its visible enabled controls are keyboard reachable.",
    ),
    ManualAccessibilityCheck(
        "keyboard.wizard_actions",
        "keyboard",
        "On Product, reach Add requirement, Remove selected, Create project and Cancel project creation without using the mouse.",
        "All wizard actions can receive keyboard focus and can be activated from the keyboard.",
    ),
    ManualAccessibilityCheck(
        "focus.visible",
        "focus",
        "While performing the keyboard checks, observe the currently focused control throughout KodeStudio and the wizard.",
        "A visible focus indicator is always perceptible on the currently focused interactive control.",
    ),
    ManualAccessibilityCheck(
        "focus.not_obscured",
        "focus",
        "Inspect focused controls near page/tab/table boundaries and after scrolling where applicable.",
        "The focus indicator is not fully hidden, clipped away, or covered by another UI element.",
    ),
    ManualAccessibilityCheck(
        "narrator.enabled",
        "narrator",
        "Press Win+Ctrl+Enter to enable Windows Narrator before the remaining Narrator checks.",
        "Narrator starts and produces speech for focused KodeStudio controls.",
    ),
    ManualAccessibilityCheck(
        "narrator.main_navigation",
        "narrator",
        "With Narrator enabled, traverse Main navigation and the New project control.",
        "Narrator announces meaningful names and appropriate roles for the navigation and New project control.",
    ),
    ManualAccessibilityCheck(
        "narrator.security_actions",
        "narrator",
        "Navigate to Security and focus Stop all protected processes and Reset emergency stop without activating the emergency stop.",
        "Narrator announces both action names, button roles, and enough description to distinguish the dangerous stop action from reset.",
    ),
    ManualAccessibilityCheck(
        "narrator.wizard_fields",
        "narrator",
        "Open the project wizard and traverse the General and Features & tools fields with Narrator.",
        "Narrator announces meaningful field names, roles and current values/states instead of only generic control types.",
    ),
    ManualAccessibilityCheck(
        "narrator.wizard_tables",
        "narrator",
        "Traverse Performance budgets and Product requirements using the keyboard with Narrator enabled.",
        "Narrator identifies the table context and exposes meaningful cell/control information while navigating.",
    ),
    ManualAccessibilityCheck(
        "narrator.wizard_actions",
        "narrator",
        "Focus Browse project directory, Add requirement, Remove selected requirements, Create project and Cancel project creation.",
        "Narrator announces each action with a meaningful name and button role.",
    ),
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _evidence_root(repo_root: Path) -> Path:
    metadata = repo_root / ".kodepoia"
    if not metadata.is_dir():
        raise FileNotFoundError(
            f"Kodepoia metadata not found: {metadata}. Do not create acceptance evidence outside .kodepoia."
        )
    root = metadata / "diagnostics" / "accessibility"
    root.mkdir(parents=True, exist_ok=True)
    return root


def prepare(repo_root: Path, *, source_head: str) -> dict[str, Any]:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError("R6.5 local acceptance requires the UI extra with PySide6") from exc

    from kodepoia.kodestudio.accessibility import (
        MAIN_REQUIRED_CONTROL_IDS,
        WIZARD_REQUIRED_CONTROL_IDS,
        audit_qt_surface,
    )
    from kodepoia.kodestudio.app import build_window
    from kodepoia.kodestudio.project_wizard import create_project_dialog

    app = QApplication.instance() or QApplication([])
    generated_at = _now()
    window = build_window()
    dialog = create_project_dialog(window)
    window.show()
    dialog.show()
    QApplication.processEvents()

    try:
        main_report = audit_qt_surface(
            window,
            surface="kodestudio-main",
            expected_ids=MAIN_REQUIRED_CONTROL_IDS,
            generated_at=generated_at,
        )
        wizard_report = audit_qt_surface(
            dialog,
            surface="kodestudio-project-wizard",
            expected_ids=WIZARD_REQUIRED_CONTROL_IDS,
            generated_at=generated_at,
        )
    finally:
        dialog.close()
        window.close()
        QApplication.processEvents()

    store = AccessibilityStore(repo_root)
    main_latest, _ = store.save(main_report)
    wizard_latest, _ = store.save(wizard_report)
    automated_pass = (
        main_report.status is AccessibilityReportStatus.PASS
        and wizard_report.status is AccessibilityReportStatus.PASS
        and main_report.counts["blocking_failures"] == 0
        and wizard_report.counts["blocking_failures"] == 0
    )

    payload = {
        "schema_version": 1,
        "phase": "R6.5-local-acceptance",
        "generated_at": generated_at,
        "source_head": source_head,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "automated_pass": automated_pass,
        "automated_reports": [
            {
                "surface": main_report.surface,
                "status": main_report.status.value,
                "counts": main_report.counts,
                "evidence_sha256": main_report.evidence_sha256,
                "path": main_latest.relative_to(repo_root).as_posix(),
            },
            {
                "surface": wizard_report.surface,
                "status": wizard_report.status.value,
                "counts": wizard_report.counts,
                "evidence_sha256": wizard_report.evidence_sha256,
                "path": wizard_latest.relative_to(repo_root).as_posix(),
            },
        ],
        "manual_checks": [check.to_dict() for check in MANUAL_CHECKS],
        "narrator_shortcuts": {
            "toggle": "Win+Ctrl+Enter",
            "speech_recap": "Narrator+Alt+X",
        },
    }
    manifest = _evidence_root(repo_root) / "r6-5-manual-manifest.json"
    _write_json(manifest, payload)
    payload["manifest_path"] = manifest.relative_to(repo_root).as_posix()
    return payload


def finalize(repo_root: Path, *, source_head: str, responses_path: Path) -> dict[str, Any]:
    root = _evidence_root(repo_root)
    manifest_path = root / "r6-5-manual-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("R6.5 manual manifest is missing; run --prepare first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest.get("source_head", "")) != source_head:
        raise ValueError("R6.5 manifest source head does not match the current acceptance head")

    response_payload = json.loads(responses_path.read_text(encoding="utf-8"))
    if int(response_payload.get("schema_version", 0)) != 1:
        raise ValueError("Unsupported R6.5 manual response schema version")
    if str(response_payload.get("source_head", "")) != source_head:
        raise ValueError("R6.5 manual responses were recorded for a different source head")
    responses = response_payload.get("responses")
    if not isinstance(responses, dict):
        raise ValueError("R6.5 manual responses must be an object keyed by checklist ID")

    expected_ids = [check.id for check in MANUAL_CHECKS]
    if set(responses) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(responses))
        extra = sorted(set(responses) - set(expected_ids))
        raise ValueError(f"R6.5 manual response IDs mismatch; missing={missing}, extra={extra}")

    manual_results = []
    for check in MANUAL_CHECKS:
        response = responses[check.id]
        if not isinstance(response, dict):
            raise ValueError(f"Manual response for {check.id} must be an object")
        status = str(response.get("status", "")).strip().lower()
        if status not in {"pass", "fail"}:
            raise ValueError(f"Manual response for {check.id} must be pass or fail")
        note = str(response.get("note", "")).strip()
        manual_results.append(
            {
                "id": check.id,
                "category": check.category,
                "status": status,
                "blocking": check.blocking,
                "note": note,
            }
        )

    store = AccessibilityStore(repo_root)
    main_report = store.load_latest("kodestudio-main")
    wizard_report = store.load_latest("kodestudio-project-wizard")
    if manifest["automated_reports"][0]["evidence_sha256"] != main_report.evidence_sha256:
        raise ValueError("KodeStudio main accessibility report changed after manual manifest creation")
    if manifest["automated_reports"][1]["evidence_sha256"] != wizard_report.evidence_sha256:
        raise ValueError("Project wizard accessibility report changed after manual manifest creation")

    automated_pass = (
        bool(manifest.get("automated_pass"))
        and main_report.status is AccessibilityReportStatus.PASS
        and wizard_report.status is AccessibilityReportStatus.PASS
        and main_report.counts["blocking_failures"] == 0
        and wizard_report.counts["blocking_failures"] == 0
    )
    manual_failed = [result for result in manual_results if result["status"] == "fail"]
    blocking_failures = [
        result for result in manual_results if result["status"] == "fail" and result["blocking"]
    ]
    acceptance_completed = automated_pass and not manual_failed and not blocking_failures

    payload = {
        "metadata": {
            "phase": "R6.5-local-acceptance",
            "generated_at": _now(),
            "source_head": source_head,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "acceptance_completed": acceptance_completed,
        },
        "automated": {
            "passed": automated_pass,
            "reports": manifest["automated_reports"],
        },
        "manual": {
            "total": len(manual_results),
            "passed": sum(result["status"] == "pass" for result in manual_results),
            "failed": len(manual_failed),
            "blocking_failures": len(blocking_failures),
            "results": manual_results,
        },
        "summary": {
            "failed": (0 if automated_pass else 1) + len(manual_failed),
            "passed": (2 if automated_pass else 0)
            + sum(result["status"] == "pass" for result in manual_results),
            "total": 2 + len(manual_results),
        },
    }
    output = root / "r6-5-local-acceptance.json"
    _write_json(output, payload)
    payload["output_path"] = output.relative_to(repo_root).as_posix()
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R6.5 KodeAccessibility local acceptance")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--head", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--responses")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve(strict=False)
    try:
        if args.prepare:
            payload = prepare(repo_root, source_head=args.head)
        else:
            if not args.responses:
                raise ValueError("--responses is required with --finalize")
            payload = finalize(
                repo_root,
                source_head=args.head,
                responses_path=Path(args.responses).resolve(strict=True),
            )
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc), "acceptance_completed": False}, indent=2))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.finalize and not payload["metadata"]["acceptance_completed"]:
        return 1
    if args.prepare and not payload["automated_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
