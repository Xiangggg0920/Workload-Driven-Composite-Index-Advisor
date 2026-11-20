import unittest
from unittest.mock import patch

from dataset.verify_sf1 import accept_checks, verify


class Sf1AcceptanceTests(unittest.TestCase):
    def test_every_check_must_be_explicitly_successful(self):
        self.assertTrue(accept_checks({"count": True, "integrity": True, "smoke": True}))
        for checks in ({}, {"count": False}, {"count": True, "integrity": False},
                       {"count": 1}, {"smoke": None}):
            with self.subTest(checks=checks):
                self.assertFalse(accept_checks(checks))

    def test_incomplete_or_wrong_database_load_never_connects(self):
        for report in ({}, {"verified": False},
                       {"verified": True, "data_loaded": True, "database_created": True,
                        "target_database": "advisor_smoke"}):
            with self.subTest(report=report), patch("dataset.verify_sf1.psycopg.connect") as connect:
                with self.assertRaises(ValueError):
                    verify(report, {}, {})
                connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
