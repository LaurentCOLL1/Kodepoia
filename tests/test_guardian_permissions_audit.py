from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import GuardianError, KodeGuardian
from kodepoia.core.permissions import PermissionPolicy
from kodepoia.core.types import ActionKind, ActionRequest, DecisionStatus


class GuardianTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.audit = AuditLog(self.root / "audit.jsonl")
        self.guardian = KodeGuardian(PermissionPolicy.default(), self.audit)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_project_read_allowed_and_outside_denied(self) -> None:
        inside = self.root / "project.godot"
        decision = self.guardian.evaluate(ActionRequest(ActionKind.FILE_READ, "test", self.root, str(inside)))
        self.assertEqual(decision.status, DecisionStatus.ALLOW)
        outside = self.root.parent / "outside.txt"
        decision = self.guardian.evaluate(ActionRequest(ActionKind.FILE_READ, "test", self.root, str(outside)))
        self.assertEqual(decision.status, DecisionStatus.DENY)

    def test_process_requires_confirmation(self) -> None:
        request = ActionRequest(ActionKind.PROCESS_RUN, "test", self.root, "python")
        with self.assertRaises(GuardianError):
            self.guardian.require_allowed(request)
        self.guardian.require_allowed(request, confirmed=True)

    def test_brain_cannot_read_secret(self) -> None:
        decision = self.guardian.evaluate(ActionRequest(ActionKind.SECRET_READ, "kodebrain", target="TOKEN"))
        self.assertEqual(decision.status, DecisionStatus.DENY)

    def test_kill_switch_default_denies(self) -> None:
        self.guardian.kill_switch()
        decision = self.guardian.evaluate(ActionRequest(ActionKind.FILE_READ, "test", self.root, str(self.root / "a")))
        self.assertEqual(decision.status, DecisionStatus.DENY)

    def test_audit_is_written(self) -> None:
        self.guardian.evaluate(ActionRequest(ActionKind.FILE_READ, "test", self.root, str(self.root / "a")))
        events = self.audit.tail()
        self.assertTrue(events)
        self.assertEqual(events[-1]["event_type"], "guardian.decision")


if __name__ == "__main__":
    unittest.main()
