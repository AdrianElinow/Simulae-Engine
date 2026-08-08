import unittest

from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition, ConditionRuleType


class TestSimulaeCondition(unittest.TestCase):
    def setUp(self):
        self.condition = SimulaeCondition("condition-1")

    def test_evaluates_nested_numeric_and_string_properties(self):
        subject = {"status": {"hunger": 4}, "name": "Ada"}
        self.condition.property = ["status", "hunger"]
        self.condition.rule = ConditionRuleType.GREATER_THAN
        self.condition.value = 3
        self.assertTrue(self.condition.evaluate(subject))

        self.condition.property = ["name"]
        self.condition.rule = ConditionRuleType.REGEX_MATCHES
        self.condition.value = "ada"
        self.assertTrue(self.condition.evaluate(subject))

    def test_evaluates_list_membership(self):
        self.condition.property = ["roles"]
        self.condition.rule = ConditionRuleType.LIST_CONTAINS
        self.condition.value = "medic"

        self.assertTrue(self.condition.evaluate({"roles": ["scout", "medic"]}))
