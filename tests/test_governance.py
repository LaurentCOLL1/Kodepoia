from __future__ import annotations

import unittest

from kodepoia.core.governance import DataClass, DataPolicy, KodeDataGovernance


class GovernanceTests(unittest.TestCase):
    def test_sensitive_data_cannot_escape_by_flags_alone(self) -> None:
        governance = KodeDataGovernance()
        secret = DataPolicy(DataClass.SECRET, global_memory=True, training_dataset=True, external_research=True)
        self.assertFalse(governance.can_store_globally(secret))
        self.assertFalse(governance.can_train(secret))
        self.assertFalse(governance.can_send_to_research(secret))

    def test_public_data_can_follow_explicit_policy(self) -> None:
        governance = KodeDataGovernance()
        public = DataPolicy(DataClass.PUBLIC, global_memory=True, training_dataset=True, external_research=True)
        self.assertTrue(governance.can_store_globally(public))
        self.assertTrue(governance.can_train(public))
        self.assertTrue(governance.can_send_to_research(public))


if __name__ == "__main__":
    unittest.main()
