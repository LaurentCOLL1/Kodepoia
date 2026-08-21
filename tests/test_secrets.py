from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import GuardianError, KodeGuardian
from kodepoia.core.permissions import PermissionPolicy
from kodepoia.core.secrets import MemorySecretStore, SecretBroker


class SecretTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.guardian = KodeGuardian(PermissionPolicy.default(), AuditLog(self.root / "audit.jsonl"))
        self.broker = SecretBroker(self.guardian, MemorySecretStore())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_broker_requires_confirmation_for_write(self) -> None:
        with self.assertRaises(GuardianError):
            self.broker.set("TOKEN", "abc123")
        self.broker.set("TOKEN", "abc123", confirmed=True)
        self.assertEqual(self.broker.get("TOKEN"), "abc123")

    def test_redaction_removes_secret_value(self) -> None:
        self.assertEqual(self.broker.redact("token=abc123", ["abc123"]), "token=[REDACTED]")


if __name__ == "__main__":
    unittest.main()
