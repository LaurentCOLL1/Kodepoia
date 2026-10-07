from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v1_1_1_online_metadata_transition.py"
STAGED = ROOT / "docs" / "release" / "evidence" / "V1_1_1_TARGETS_V10.json"
WORKFLOW = ROOT / ".github" / "workflows" / "v1-1-1-online-metadata-transition.yml"

SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tuf_release_ceremony as ceremony  # noqa: E402


def _module():
    spec = importlib.util.spec_from_file_location("v111_online", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v111_operator_targets_v10_is_exact_and_authorized() -> None:
    module = _module()
    blob = subprocess.check_output(
        ["git", "show", "HEAD:docs/release/evidence/V1_1_1_TARGETS_V10.json"],
        cwd=ROOT,
    )
    assert hashlib.sha256(blob).hexdigest() == module.EXPECTED_TARGETS_SHA256

    current = ceremony._load_current_metadata(ROOT / "update-repository" / "metadata")
    report = ceremony.Report()
    root_md, targets_md, _, _ = ceremony._verify_current_state(
        current,
        datetime(2026, 10, 7, 14, 1, 2, tzinfo=UTC),
        report,
    )
    staged = module.validate_staged_targets(
        root=root_md.signed,
        current_targets=targets_md,
        current_bytes=current["targets.json"],
        staged_bytes=blob,
        report=report,
    )
    assert staged.signed.version == 10
    assert module.TARGET_PATH in staged.signed.targets
    assert staged.signed.targets[module.TARGET_PATH].to_dict() == module.EXPECTED_TARGET


def test_v111_online_transition_constants_are_monotonic() -> None:
    module = _module()
    assert module.CURRENT_TARGETS_VERSION == 9
    assert module.EXPECTED_TARGETS_VERSION == 10
    assert module.CURRENT_SNAPSHOT_VERSION == 11
    assert module.EXPECTED_SNAPSHOT_VERSION == 12
    assert module.CURRENT_TIMESTAMP_VERSION == 11
    assert module.EXPECTED_TIMESTAMP_VERSION == 12
    assert module.RELEASE_SOURCE_SHA == "aa1c80389b10f5ef44737241bf192c04f847e4ec"


def test_v111_online_transition_workflow_is_protected_one_shot() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "github.ref == 'refs/heads/main'" in source
    assert "environment: tuf-production-signing" in source
    assert "TUF_SNAPSHOT_ED25519_SEED_B64" in source
    assert "TUF_TIMESTAMP_ED25519_SEED_B64" in source
    assert "Require stable 1.1.0 baseline and absent 1.1.1 namespace" in source
    assert "--staged-targets docs/release/evidence/V1_1_1_TARGETS_V10.json" in source
    assert "targets_version\"] == 10" in source
    assert "snapshot_version\"] == 12" in source
    assert "timestamp_version\"] == 12" in source
    assert "contents: write" not in source
    assert "pull-requests: write" not in source
    assert "gh release create" not in source
    assert "gh release upload" not in source
    assert "git tag" not in source
