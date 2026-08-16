import unittest

from NGIN.implementation.lib.ConditionRule import ConditionRuleType
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import (
    ATTRIBUTES,
    CND,
    CONTENTS,
    NAME,
    NODETYPE,
    OBJ,
    POI,
    REFERENCES,
    RELATIONS,
    SCALES,
)


class TestSimulaeCondition(unittest.TestCase):
    def test_initializes_as_condition_meta_node(self):
        condition = SimulaeCondition(
            "condition-1",
            property_path=[ATTRIBUTES, "health"],
            rule=ConditionRuleType.GREATER_THAN,
            value=0,
        )

        self.assertEqual(condition.ID, "condition-1")
        self.assertEqual(condition.Nodetype, CND)
        self.assertEqual(condition.property_path, [ATTRIBUTES, "health"])
        self.assertEqual(condition.rule, ConditionRuleType.GREATER_THAN)
        self.assertEqual(condition.value, 0)

    def test_rejects_invalid_constructor_inputs(self):
        blank = SimulaeCondition("condition-1")
        self.assertEqual(blank.property_path, [])
        self.assertEqual(blank.rule, ConditionRuleType.EXISTS)

        with self.assertRaises(ValueError):
            SimulaeCondition("condition-1", property_path=[])

        with self.assertRaises(ValueError):
            SimulaeCondition("condition-1", rule=ConditionRuleType.GREATER_THAN, value=0)

        with self.assertRaises(ValueError):
            SimulaeCondition("condition-1", property_path=["status"], rule="exists")

        with self.assertRaises(ValueError):
            SimulaeCondition(
                "condition-1",
                property_path=["status"],
                rule=ConditionRuleType.GREATER_THAN,
            )

        with self.assertRaises(ValueError):
            SimulaeCondition(
                "condition-1",
                property_path=["status"],
                rule=ConditionRuleType.STRING_CONTAINS,
                value=3,
            )

    def test_evaluates_basic_existence_rules(self):
        subject = {"status": {"alive": True}}

        exists = SimulaeCondition(
            "condition-1",
            property_path=["status", "alive"],
            rule=ConditionRuleType.EXISTS,
        )
        missing = SimulaeCondition(
            "condition-2",
            property_path=["status", "missing"],
            rule=ConditionRuleType.NOT_EXISTS,
        )

        self.assertTrue(exists.evaluate(subject))
        self.assertTrue(missing.evaluate(subject))

    def test_evaluates_numeric_rules_against_nested_properties(self):
        subject = {ATTRIBUTES: {"health": 10, "hunger": 0}}

        cases = [
            (ConditionRuleType.EQUALS, "health", 10, True),
            (ConditionRuleType.NOT_EQUALS, "health", 4, True),
            (ConditionRuleType.LESS_THAN, "health", 12, True),
            (ConditionRuleType.LESS_THAN_OR_EQUAL, "health", 10, True),
            (ConditionRuleType.GREATER_THAN, "health", 5, True),
            (ConditionRuleType.GREATER_THAN_OR_EQUAL, "hunger", 0, True),
        ]

        for rule, key, value, expected in cases:
            with self.subTest(rule=rule):
                condition = SimulaeCondition(
                    f"condition-{rule.name}",
                    property_path=[ATTRIBUTES, key],
                    rule=rule,
                    value=value,
                )
                self.assertEqual(condition.evaluate(subject), expected)

    def test_evaluates_numeric_range_rules(self):
        within = SimulaeCondition(
            "condition-1",
            property_path=[ATTRIBUTES, "health"],
            rule=ConditionRuleType.WITHIN_RANGE,
            value=(5, 15),
        )
        beyond = SimulaeCondition(
            "condition-2",
            property_path=[ATTRIBUTES, "health"],
            rule=ConditionRuleType.BEYOND_RANGE,
            value=(5, 15),
        )

        self.assertTrue(within.evaluate({ATTRIBUTES: {"health": 10}}))
        self.assertFalse(within.evaluate({ATTRIBUTES: {"health": 16}}))
        self.assertTrue(beyond.evaluate({ATTRIBUTES: {"health": 16}}))
        self.assertFalse(beyond.evaluate({ATTRIBUTES: {"health": 10}}))

    def test_evaluates_string_rules(self):
        subject = {"profile": {"name": "Ada Voss"}}

        contains = SimulaeCondition(
            "condition-1",
            property_path=["profile", "name"],
            rule=ConditionRuleType.STRING_CONTAINS,
            value="Voss",
        )
        matches_regex = SimulaeCondition(
            "condition-2",
            property_path=["profile", "name"],
            rule=ConditionRuleType.REGEX_MATCHES,
            value="ada",
        )
        equals = SimulaeCondition(
            "condition-3",
            property_path=["profile", "name"],
            rule=ConditionRuleType.EQUALS,
            value="Ada Voss",
        )

        self.assertTrue(contains.evaluate(subject))
        self.assertTrue(matches_regex.evaluate(subject))
        self.assertTrue(equals.evaluate(subject))

    def test_evaluates_list_rules(self):
        subject = {"roles": ["scout", "medic"]}

        contains = SimulaeCondition(
            "condition-1",
            property_path=["roles"],
            rule=ConditionRuleType.LIST_CONTAINS,
            value="medic",
        )
        excludes = SimulaeCondition(
            "condition-2",
            property_path=["roles"],
            rule=ConditionRuleType.NOT_LIST_CONTAINS,
            value="driver",
        )

        self.assertTrue(contains.evaluate(subject))
        self.assertTrue(excludes.evaluate(subject))

    def test_extracts_from_simulae_node_state(self):
        target = SimulaeNode(
            given_id="target-1",
            nodetype=POI,
            references={NAME: "Ada"},
            attributes={"health": 6},
            scales={"Trust": {"Team": 4}},
        )
        condition = SimulaeCondition(
            "condition-1",
            property_path=[ATTRIBUTES, "health"],
            rule=ConditionRuleType.GREATER_THAN,
            value=0,
        )
        name_condition = SimulaeCondition(
            "condition-2",
            property_path=[REFERENCES, NAME],
            rule=ConditionRuleType.EQUALS,
            value="Ada",
        )
        scale_condition = SimulaeCondition(
            "condition-3",
            property_path=[SCALES, "Trust", "Team"],
            rule=ConditionRuleType.EQUALS,
            value=4,
        )

        self.assertTrue(condition.evaluate(target))
        self.assertTrue(name_condition.evaluate(target))
        self.assertTrue(scale_condition.evaluate(target))
        self.assertEqual(condition.extract_property(target, [NODETYPE]), POI)

    def test_extracts_from_nested_simulae_nodes_in_relations(self):
        container = SimulaeNode(given_id="container-1", nodetype=OBJ)
        child = SimulaeNode(
            given_id="child-1",
            nodetype=OBJ,
            references={NAME: "Battery"},
            attributes={"charge": 7},
        )
        container.Relations[CONTENTS][OBJ][child.ID] = child

        charge_condition = SimulaeCondition(
            "condition-1",
            property_path=[RELATIONS, CONTENTS, OBJ, child.ID, ATTRIBUTES, "charge"],
            rule=ConditionRuleType.GREATER_THAN_OR_EQUAL,
            value=5,
        )
        name_condition = SimulaeCondition(
            "condition-2",
            property_path=[RELATIONS, CONTENTS, OBJ, child.ID, REFERENCES, NAME],
            rule=ConditionRuleType.EQUALS,
            value="Battery",
        )
        missing_nested_condition = SimulaeCondition(
            "condition-3",
            property_path=[RELATIONS, CONTENTS, OBJ, "missing-child", ATTRIBUTES, "charge"],
            rule=ConditionRuleType.NOT_EXISTS,
        )

        self.assertTrue(charge_condition.evaluate(container))
        self.assertTrue(name_condition.evaluate(container))
        self.assertTrue(missing_nested_condition.evaluate(container))

    def test_extracts_from_generic_json_objects(self):
        target = {
            NODETYPE: POI,
            REFERENCES: {NAME: "Bea"},
            ATTRIBUTES: {
                "health": 9,
                "inventory": [
                    {"name": "bandage", "quantity": 2},
                    {"name": "radio", "quantity": 1},
                ],
            },
        }

        name_condition = SimulaeCondition(
            "condition-1",
            property_path=[REFERENCES, NAME],
            rule=ConditionRuleType.EQUALS,
            value="Bea",
        )
        list_item_condition = SimulaeCondition(
            "condition-2",
            property_path=[ATTRIBUTES, "inventory", "1", "name"],
            rule=ConditionRuleType.EQUALS,
            value="radio",
        )
        missing_list_item = SimulaeCondition(
            "condition-3",
            property_path=[ATTRIBUTES, "inventory", "4", "name"],
            rule=ConditionRuleType.NOT_EXISTS,
        )

        self.assertTrue(name_condition.evaluate(target))
        self.assertTrue(list_item_condition.evaluate(target))
        self.assertTrue(missing_list_item.evaluate(target))

    def test_extracts_from_nested_json_relations(self):
        target = {
            RELATIONS: {
                CONTENTS: {
                    OBJ: {
                        "child-1": {
                            NODETYPE: OBJ,
                            REFERENCES: {NAME: "Battery"},
                            ATTRIBUTES: {"charge": 7},
                        },
                    },
                },
            },
        }
        condition = SimulaeCondition(
            "condition-1",
            property_path=[RELATIONS, CONTENTS, OBJ, "child-1", ATTRIBUTES, "charge"],
            rule=ConditionRuleType.EQUALS,
            value=7,
        )

        self.assertTrue(condition.evaluate(target))

    def test_missing_non_basic_property_evaluates_false(self):
        condition = SimulaeCondition(
            "condition-1",
            property_path=[ATTRIBUTES, "health"],
            rule=ConditionRuleType.GREATER_THAN,
            value=0,
        )

        self.assertFalse(condition.evaluate({ATTRIBUTES: {}}))

    def test_wrong_target_value_type_raises_for_rule_family(self):
        numeric = SimulaeCondition(
            "condition-1",
            property_path=["name"],
            rule=ConditionRuleType.GREATER_THAN,
            value=0,
        )
        string = SimulaeCondition(
            "condition-2",
            property_path=["age"],
            rule=ConditionRuleType.STRING_CONTAINS,
            value="Ada",
        )
        list_condition = SimulaeCondition(
            "condition-3",
            property_path=["role"],
            rule=ConditionRuleType.LIST_CONTAINS,
            value="medic",
        )

        with self.assertRaises(ValueError):
            numeric.evaluate({"name": "Ada"})

        with self.assertRaises(ValueError):
            string.evaluate({"age": 4})

        with self.assertRaises(ValueError):
            list_condition.evaluate({"role": "medic"})
