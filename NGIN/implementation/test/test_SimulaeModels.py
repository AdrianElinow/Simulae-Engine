import unittest

from NGIN.implementation.lib.Claim import Claim
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition, ConditionRule
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNodeStatus import SimulaeNodeStatus
from NGIN.utilities.lib.SimulaeConstants import OBS, SRC, TGT


class TestClaim(unittest.TestCase):
    def test_claim_has_isolated_mutable_defaults(self):
        first_claim = Claim("claim-1", "mayor", "is_corrupt", True)
        second_claim = Claim("claim-2", "guard", "knows", "mayor")
        first_claim.provenance.append("event-1")
        first_claim.sources.add("witness-1")

        self.assertEqual(first_claim.status, "unverified")
        self.assertEqual(second_claim.provenance, [])
        self.assertEqual(second_claim.sources, set())


class TestSimulaeEvent(unittest.TestCase):
    def test_event_normalizes_and_tracks_participants(self):
        event = SimulaeEvent(
            "event-1", "social", "conversation", "gossip", None, None,
            [" actor-1 ", "actor-1"], ["target-1"], ["observer-1"], ["rumor"],
        )

        self.assertEqual(event.source_ids, ["actor-1"])
        self.assertEqual(event.Relations[SRC], {"actor-1": {}})
        self.assertEqual(event.Relations[TGT], {"target-1": {}})
        self.assertEqual(event.Relations[OBS], {"observer-1": {}})
        self.assertTrue(event.add_observer("observer-2"))
        self.assertTrue(event.was_observed_by("observer-2"))
        self.assertTrue(event.remove_observer("observer-2"))
        self.assertFalse(event.remove_observer("observer-2"))


class TestSimulaeCondition(unittest.TestCase):
    def setUp(self):
        self.condition = SimulaeCondition("condition-1")

    def test_evaluates_nested_numeric_and_string_properties(self):
        subject = {"status": {"hunger": 4}, "name": "Ada"}
        self.condition.property = ["status", "hunger"]
        self.condition.rule = ConditionRule.GREATER_THAN
        self.condition.value = 3
        self.assertTrue(self.condition.evaluate(subject))

        self.condition.property = ["name"]
        self.condition.rule = ConditionRule.REGEX_MATCHES
        self.condition.value = "ada"
        self.assertTrue(self.condition.evaluate(subject))

    def test_evaluates_list_membership(self):
        self.condition.property = ["roles"]
        self.condition.rule = ConditionRule.LIST_CONTAINS
        self.condition.value = "medic"

        self.assertTrue(self.condition.evaluate({"roles": ["scout", "medic"]}))


class TestSimulaeNodeStatus(unittest.TestCase):
    def test_status_serializes_to_its_name(self):
        self.assertEqual(SimulaeNodeStatus.ALIVE.toJSON(), "ALIVE")
        self.assertEqual(SimulaeNodeStatus.DEAD.toJSON(), "DEAD")
