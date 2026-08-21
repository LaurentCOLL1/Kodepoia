from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import GuardianError, KodeGuardian
from kodepoia.core.permissions import PermissionPolicy
from kodepoia.core.safe_change import SafeChangeManager


class SafeChangeTests(unittest.TestCase):
    def test_write_snapshots_preimage_and_delete_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            project.mkdir()
            target = project / "file.txt"
            target.write_text("old", encoding="utf-8")
            guardian = KodeGuardian(PermissionPolicy.default(), AuditLog(base / "audit.jsonl"))
            manager = SafeChangeManager(guardian, base / "safe-change")
            manager.apply(manager.plan_write(project, target, "new"), actor="test")
            self.assertEqual(target.read_text(encoding="utf-8"), "new")
            snapshots = list((base / "safe-change").rglob("file.txt"))
            self.assertTrue(snapshots)
            self.assertEqual(snapshots[0].read_text(encoding="utf-8"), "old")
            plan = manager.plan_delete(project, [target])
            with self.assertRaises(GuardianError):
                manager.apply(plan, actor="test")
            manager.apply(plan, actor="test", confirmed=True)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
