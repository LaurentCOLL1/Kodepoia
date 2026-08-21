from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodepoia.core.recovery import KodeRecovery


class RecoveryTests(unittest.TestCase):
    def test_checkpoint_roundtrip_and_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recovery = KodeRecovery(Path(tmp))
            recovery.checkpoint("task-1", "patch", "running", {"file": "x"})
            loaded = recovery.load("task-1")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.payload["file"], "x")
            self.assertEqual(len(recovery.pending()), 1)
            recovery.complete("task-1")
            self.assertEqual(recovery.pending(), [])

    def test_unknown_task_can_be_completed_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recovery = KodeRecovery(Path(tmp))
            state = recovery.complete("missing", {"reason": "reconciled"})
            self.assertEqual(state.status, "complete")
            self.assertEqual(state.phase, "unknown")


if __name__ == "__main__":
    unittest.main()
