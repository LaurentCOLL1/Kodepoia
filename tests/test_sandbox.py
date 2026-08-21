from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import GuardianError, KodeGuardian
from kodepoia.core.permissions import PermissionPolicy
from kodepoia.core.sandbox import KodeSandbox, SandboxProfile, SandboxViolation


class SandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.guardian = KodeGuardian(PermissionPolicy.default(), AuditLog(self.root / "audit.jsonl"))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_allowlist_scope_and_confirmation(self) -> None:
        profile = SandboxProfile(frozenset({Path(sys.executable).name}), (self.root,), timeout_seconds=5)
        sandbox = KodeSandbox(self.guardian, profile)
        with self.assertRaises(GuardianError):
            sandbox.run([sys.executable, "-c", "print('ok')"], cwd=self.root, actor="test")
        result = sandbox.run([sys.executable, "-c", "print('ok')"], cwd=self.root, actor="test", confirmed=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "ok")
        with self.assertRaises(SandboxViolation):
            sandbox.run(["definitely-not-allowed", "--version"], cwd=self.root, actor="test", confirmed=True)
        with self.assertRaises(SandboxViolation):
            sandbox.run([sys.executable, "-V"], cwd=self.root.parent, actor="test", confirmed=True)


if __name__ == "__main__":
    unittest.main()
