from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import KodeBackup
from kodepoia.core.guardian import GuardianError, KodeGuardian
from kodepoia.core.permissions import PermissionPolicy


class BackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / "project"
        self.project.mkdir()
        self.guardian = KodeGuardian(PermissionPolicy.default(), AuditLog(self.base / "audit.jsonl"))
        self.backup = KodeBackup(self.guardian, self.base / "backups")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_backup_integrity_and_restore_confirmation(self) -> None:
        (self.project / "a.txt").write_text("alpha", encoding="utf-8")
        record = self.backup.create(self.project)
        self.assertTrue(self.backup.verify(record))
        target = self.base / "restored"
        with self.assertRaises(GuardianError):
            self.backup.restore(record, target)
        self.backup.restore(record, target, confirmed=True)
        self.assertEqual((target / "a.txt").read_text(encoding="utf-8"), "alpha")

    def test_tampering_is_detected(self) -> None:
        (self.project / "a.txt").write_text("alpha", encoding="utf-8")
        record = self.backup.create(self.project)
        (record.path / "a.txt").write_text("tampered", encoding="utf-8")
        self.assertFalse(self.backup.verify(record))


if __name__ == "__main__":
    unittest.main()
