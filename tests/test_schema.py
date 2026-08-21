from __future__ import annotations

import unittest

from kodepoia.core.schema import KodeSchema, SchemaError, SchemaSpec


class SchemaTests(unittest.TestCase):
    def test_versioned_migration_and_validation(self) -> None:
        registry = KodeSchema()
        def validate_v2(payload):
            if payload.get("version") != 2 or "name" not in payload:
                raise SchemaError("invalid payload")
        registry.register(SchemaSpec("demo", 2, validate_v2))
        registry.register_migration("demo", 1, 2, lambda value: {**value, "version": 2})
        migrated = registry.migrate("demo", {"name": "x", "version": 1}, 1, 2)
        self.assertEqual(migrated["version"], 2)

    def test_missing_migration_fails_closed(self) -> None:
        registry = KodeSchema()
        registry.register(SchemaSpec("demo", 2, lambda payload: None))
        with self.assertRaises(SchemaError):
            registry.migrate("demo", {}, 1, 2)


if __name__ == "__main__":
    unittest.main()
