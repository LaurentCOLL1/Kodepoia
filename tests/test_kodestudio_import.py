from __future__ import annotations

import unittest


class KodeStudioImportTests(unittest.TestCase):
    def test_ui_module_import_does_not_require_qt_until_main(self) -> None:
        from kodepoia.kodestudio import app
        self.assertTrue(callable(app.main))


if __name__ == "__main__":
    unittest.main()
