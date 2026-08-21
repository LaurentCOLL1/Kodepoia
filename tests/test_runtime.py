from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodepoia.core.paths import AppPaths
from kodepoia.runtime import KodeRuntime


class RuntimeTests(unittest.TestCase):
    def test_runtime_builds_without_ui_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = KodeRuntime.build(AppPaths(base / "data", base / "config", base / "cache"), sandbox_roots=(base,))
            self.assertFalse(runtime.guardian.stopped)
            self.assertTrue(runtime.audit.path.parent.exists())
            self.assertEqual(runtime.recovery.pending(), [])


if __name__ == "__main__":
    unittest.main()
