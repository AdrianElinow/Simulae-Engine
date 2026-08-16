import unittest

from NGIN.implementation.lib.Claim import Claim


class TestClaim(unittest.TestCase):
    def test_claim_has_isolated_mutable_defaults(self):
        first_claim = Claim("claim-1", "mayor", "is_corrupt", True)
        second_claim = Claim("claim-2", "guard", "knows", "mayor")
        first_claim.provenance.append("event-1")
        first_claim.sources.add("witness-1")

        self.assertEqual(first_claim.status, "unverified")
        self.assertEqual(second_claim.provenance, [])
        self.assertEqual(second_claim.sources, set())
