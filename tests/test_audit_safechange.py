from pathlib import Path

from kodepoia.core.audit import AuditLog
from kodepoia.core.safe_change import SafeChangeManager


def test_audit_hash_chain(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append("test", "one", "pytest", "ok")
    log.append("test", "two", "pytest", "ok")
    assert log.verify()


def test_safechange_snapshot(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    file = project / "data.txt"
    file.write_text("before", encoding="utf-8")
    manager = SafeChangeManager(project, tmp_path / "snapshots")
    snapshot = manager.snapshot([file])
    assert (snapshot / "data.txt").read_text(encoding="utf-8") == "before"
    manifest = (snapshot / "MANIFEST.txt").read_bytes()
    assert b"\r\n" not in manifest
    assert manifest.startswith(b"data.txt ")
