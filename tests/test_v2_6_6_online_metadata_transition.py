from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v2_6_6_online_metadata_transition.py"
STAGED = ROOT / "docs" / "release" / "evidence" / "V2_6_6_TARGETS_V9.json"
WORKFLOW = ROOT / ".github" / "workflows" / "v2-6-6-online-metadata-transition.yml"

SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tuf_release_ceremony as ceremony  # noqa: E402


def _module():
    spec = importlib.util.spec_from_file_location("v266_online", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v266_operator_targets_v9_is_exact_and_authorized() -> None:
    module = _module()
    blob = subprocess.check_output(
        ["git", "show", "HEAD:docs/release/evidence/V2_6_6_TARGETS_V9.json"],
        cwd=ROOT,
    )
    assert hashlib.sha256(blob).hexdigest() == module.EXPECTED_TARGETS_SHA256
    data = STAGED.read_bytes()
    current = ceremony._load_current_metadata(ROOT / "update-repository" / "metadata")
    report = ceremony.Report()
    root_md, targets_md, _, _ = ceremony._verify_current_state(
        current,
        datetime(2026, 10, 4, 15, 13, 31, tzinfo=UTC),
        report,
    )
    staged = module.validate_staged_targets(
        root=root_md.signed,
        current_targets=targets_md,
        staged_bytes=data,
        report=report,
    )
    assert staged.signed.version == 9
    assert module.TARGET_PATH in staged.signed.targets
    assert staged.signed.targets[module.TARGET_PATH].to_dict() == module.EXPECTED_TARGET


def test_v266_online_transition_workflow_is_post_merge_one_shot() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "automation/v2-6-6-online-signing-trigger" in source
    assert "environment: tuf-production-signing" in source
    assert "pull_request:" not in source
    assert "workflow_dispatch:" not in source
    assert "TUF_SNAPSHOT_ED25519_SEED_B64" in source
    assert "TUF_TIMESTAMP_ED25519_SEED_B64" in source
    assert "contents: write" not in source
    assert "pull-requests: write" not in source
    assert "gh release create" not in source
    assert "git tag" not in source
    assert "--output-dir artifacts/v2_6_6/production-metadata" in source
    assert "path: artifacts/v2_6_6" in source
    assert "Open protected production metadata pull request" not in source
