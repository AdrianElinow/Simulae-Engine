import unittest

from NGIN.implementation.lib.ConditionRule import ConditionRuleType
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.implementation.lib.SimulaeSelector import SimulaeSelector
from NGIN.utilities.lib.SimulaeConstants import (
    ABILITIES,
    ADJACENT,
    ATTRIBUTES,
    CHECKS,
    COMPONENTS,
    CONTENTS,
    LOC,
    NAME,
    NODETYPE,
    OBJ,
    POI,
    REFERENCES,
    RELATIONS,
)


class TestSimulaeSelector(unittest.TestCase):
    def test_empty_selector_matches_all_candidates(self):
        candidates = [{"id": "a"}, {"id": "b"}]
        selector = SimulaeSelector()

        self.assertTrue(selector.matches(candidates[0]))
        self.assertEqual(selector.select(candidates), candidates)

    def test_rejects_invalid_conditions(self):
        with self.assertRaises(ValueError):
            SimulaeSelector([object()])

        selector = SimulaeSelector()
        with self.assertRaises(ValueError):
            selector.add_condition(object())

    def test_rejects_invalid_match_modes(self):
        with self.assertRaises(ValueError):
            SimulaeSelector(match_mode="middle")

        selector = SimulaeSelector()
        with self.assertRaises(ValueError):
            selector.select([], match_mode="middle")

    def test_supports_result_match_modes(self):
        candidates = [
            {REFERENCES: {NAME: "Ada"}, ATTRIBUTES: {"health": 8}},
            {REFERENCES: {NAME: "Bea"}, ATTRIBUTES: {"health": 0}},
            {REFERENCES: {NAME: "Cal"}, ATTRIBUTES: {"health": 5}},
        ]
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
            ]
        )

        self.assertEqual(
            [candidate[REFERENCES][NAME] for candidate in selector.select(candidates, match_mode="all")],
            ["Ada", "Cal"],
        )
        self.assertEqual(selector.select(candidates, match_mode="first")[REFERENCES][NAME], "Ada")
        self.assertEqual(selector.select(candidates, match_mode="last")[REFERENCES][NAME], "Cal")
        self.assertTrue(selector.select(candidates, match_mode="any"))
        self.assertFalse(selector.select(candidates, match_mode="none"))

    def test_uses_configured_match_mode_by_default(self):
        candidates = [
            {REFERENCES: {NAME: "Ada"}, ATTRIBUTES: {"health": 8}},
            {REFERENCES: {NAME: "Cal"}, ATTRIBUTES: {"health": 5}},
        ]
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
            ],
            match_mode="last",
        )

        self.assertEqual(selector.select(candidates)[REFERENCES][NAME], "Cal")

    def test_match_modes_handle_no_matches(self):
        candidates = [{ATTRIBUTES: {"health": 0}}]
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
            ]
        )

        self.assertEqual(selector.select(candidates, match_mode="all"), [])
        self.assertIsNone(selector.select(candidates, match_mode="first"))
        self.assertIsNone(selector.select(candidates, match_mode="last"))
        self.assertFalse(selector.select(candidates, match_mode="any"))
        self.assertTrue(selector.select(candidates, match_mode="none"))

    def test_selects_json_candidates_matching_all_conditions(self):
        candidates = [
            {REFERENCES: {NAME: "Ada"}, ATTRIBUTES: {"health": 8, "roles": ["scout"]}},
            {REFERENCES: {NAME: "Bea"}, ATTRIBUTES: {"health": 0, "roles": ["medic"]}},
            {REFERENCES: {NAME: "Cal"}, ATTRIBUTES: {"health": 5, "roles": ["scout"]}},
        ]
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[ATTRIBUTES, "roles"],
                    rule=ConditionRuleType.LIST_CONTAINS,
                    value="scout",
                ),
            ]
        )

        selected = selector.select(candidates)

        self.assertEqual([candidate[REFERENCES][NAME] for candidate in selected], ["Ada", "Cal"])

    def test_matches_any_condition_when_configured(self):
        candidates = [
            {REFERENCES: {NAME: "Ada"}, ATTRIBUTES: {"health": 0, "roles": ["scout"]}},
            {REFERENCES: {NAME: "Bea"}, ATTRIBUTES: {"health": 4, "roles": ["medic"]}},
            {REFERENCES: {NAME: "Cal"}, ATTRIBUTES: {"health": 0, "roles": ["runner"]}},
        ]
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[ATTRIBUTES, "roles"],
                    rule=ConditionRuleType.LIST_CONTAINS,
                    value="scout",
                ),
            ],
            match_all=False,
        )

        selected = selector.select(candidates)

        self.assertEqual([candidate[REFERENCES][NAME] for candidate in selected], ["Ada", "Bea"])

    def test_selects_simulae_node_candidates(self):
        matching = SimulaeNode(
            given_id="node-1",
            nodetype=POI,
            references={NAME: "Ada"},
            attributes={"health": 5},
        )
        exhausted = SimulaeNode(
            given_id="node-2",
            nodetype=POI,
            references={NAME: "Bea"},
            attributes={"health": 0},
        )
        object_node = SimulaeNode(
            given_id="node-3",
            nodetype=OBJ,
            references={NAME: "Crate"},
            attributes={"health": 5},
        )
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=["Nodetype"],
                    rule=ConditionRuleType.EQUALS,
                    value=POI,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
            ]
        )

        selected = selector.select([matching, exhausted, object_node])

        self.assertEqual(selected, [matching])
        self.assertIs(selector.first([exhausted, matching]), matching)
        self.assertIsNone(selector.first([exhausted]))

    def test_selects_from_set_of_simulae_nodes(self):
        matching = SimulaeNode(
            given_id="node-1",
            nodetype=POI,
            references={NAME: "Ada"},
            attributes={"health": 5},
        )
        exhausted = SimulaeNode(
            given_id="node-2",
            nodetype=POI,
            references={NAME: "Bea"},
            attributes={"health": 0},
        )
        object_node = SimulaeNode(
            given_id="node-3",
            nodetype=OBJ,
            references={NAME: "Crate"},
            attributes={"health": 5},
        )
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=["Nodetype"],
                    rule=ConditionRuleType.EQUALS,
                    value=POI,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
            ]
        )

        selected = selector.select({matching, exhausted, object_node})

        self.assertEqual({node.ID for node in selected}, {"node-1"})

    def test_selects_from_set_using_nested_simulae_node_relations(self):
        charged_container = SimulaeNode(given_id="container-1", nodetype=OBJ)
        charged_container.Relations[CONTENTS][OBJ]["battery"] = SimulaeNode(
            given_id="battery",
            nodetype=OBJ,
            references={NAME: "Battery"},
            attributes={"charge": 9},
        )
        drained_container = SimulaeNode(given_id="container-2", nodetype=OBJ)
        drained_container.Relations[CONTENTS][OBJ]["battery"] = SimulaeNode(
            given_id="battery",
            nodetype=OBJ,
            references={NAME: "Battery"},
            attributes={"charge": 0},
        )
        empty_container = SimulaeNode(given_id="container-3", nodetype=OBJ)
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[RELATIONS, CONTENTS, OBJ, "battery", ATTRIBUTES, "charge"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=0,
                ),
            ]
        )

        selected = selector.select({charged_container, drained_container, empty_container})

        self.assertEqual({node.ID for node in selected}, {"container-1"})

    def test_selects_poi_nodes_with_health_above_100(self):
        healthy = SimulaeNode(given_id="poi-1", nodetype=POI, attributes={"health": 101})
        threshold = SimulaeNode(given_id="poi-2", nodetype=POI, attributes={"health": 100})
        object_node = SimulaeNode(given_id="obj-1", nodetype=OBJ, attributes={"health": 150})
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[NODETYPE],
                    rule=ConditionRuleType.EQUALS,
                    value=POI,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[ATTRIBUTES, "health"],
                    rule=ConditionRuleType.GREATER_THAN,
                    value=100,
                ),
            ]
        )

        selected = selector.select({healthy, threshold, object_node})

        self.assertEqual({node.ID for node in selected}, {"poi-1"})

    def test_selects_obj_nodes_with_true_check_values_only(self):
        active = SimulaeNode(given_id="obj-1", nodetype=OBJ, checks={"powered": True})
        inactive = SimulaeNode(given_id="obj-2", nodetype=OBJ, checks={"powered": False})
        missing_check = SimulaeNode(given_id="obj-3", nodetype=OBJ)
        person = SimulaeNode(given_id="poi-1", nodetype=POI, checks={"powered": True})
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[NODETYPE],
                    rule=ConditionRuleType.EQUALS,
                    value=OBJ,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[CHECKS, "powered"],
                    rule=ConditionRuleType.EQUALS,
                    value=True,
                ),
            ]
        )

        selected = selector.select({active, inactive, missing_check, person})

        self.assertEqual({node.ID for node in selected}, {"obj-1"})

    def test_selects_loc_nodes_with_at_least_three_sub_locations(self):
        hub = SimulaeNode(given_id="loc-1", nodetype=LOC)
        two_room_area = SimulaeNode(given_id="loc-2", nodetype=LOC)
        object_with_locations = SimulaeNode(given_id="obj-1", nodetype=OBJ)

        for index in range(3):
            hub.set_relation(SimulaeNode(given_id=f"hub-sub-{index}", nodetype=LOC), ADJACENT)
            object_with_locations.set_relation(
                SimulaeNode(given_id=f"obj-sub-{index}", nodetype=LOC),
                ADJACENT,
            )

        for index in range(2):
            two_room_area.set_relation(SimulaeNode(given_id=f"two-sub-{index}", nodetype=LOC), ADJACENT)

        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[NODETYPE],
                    rule=ConditionRuleType.EQUALS,
                    value=LOC,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[RELATIONS, ADJACENT, LOC],
                    rule=ConditionRuleType.GREATER_THAN_OR_EQUAL,
                    value=3,
                ),
            ]
        )

        selected = selector.select({hub, two_room_area, object_with_locations})

        self.assertEqual({node.ID for node in selected}, {"loc-1"})

    def test_selects_poi_nodes_with_heart_nested_in_human_body_composition(self):
        human_with_heart = SimulaeNode(given_id="poi-1", nodetype=POI)
        human_body = SimulaeNode(given_id="human_body", nodetype=OBJ, references={NAME: "Human Body"})
        human_body.Relations[COMPONENTS][OBJ]["heart"] = SimulaeNode(
            given_id="heart",
            nodetype=OBJ,
            references={NAME: "Heart"},
        )
        human_with_heart.Relations[COMPONENTS][OBJ][human_body.ID] = human_body

        human_without_heart = SimulaeNode(given_id="poi-2", nodetype=POI)
        human_without_heart.Relations[COMPONENTS][OBJ]["human_body"] = SimulaeNode(
            given_id="human_body",
            nodetype=OBJ,
            references={NAME: "Human Body"},
        )

        direct_heart_only = SimulaeNode(given_id="poi-3", nodetype=POI)
        direct_heart_only.Relations[COMPONENTS][OBJ]["heart"] = SimulaeNode(
            given_id="heart",
            nodetype=OBJ,
            references={NAME: "Heart"},
        )

        object_with_body = SimulaeNode(given_id="obj-1", nodetype=OBJ)
        object_with_body.Relations[COMPONENTS][OBJ][human_body.ID] = human_body

        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[NODETYPE],
                    rule=ConditionRuleType.EQUALS,
                    value=POI,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[RELATIONS, COMPONENTS, OBJ, "human_body", RELATIONS, COMPONENTS, OBJ, "heart"],
                    rule=ConditionRuleType.EXISTS,
                ),
            ]
        )

        selected = selector.select({human_with_heart, human_without_heart, direct_heart_only, object_with_body})

        self.assertEqual({node.ID for node in selected}, {"poi-1"})

    def test_selects_poi_nodes_with_specific_ability_property(self):
        healer = SimulaeNode(
            given_id="poi-1",
            nodetype=POI,
            abilities={"triage": {"enabled": True, "rank": 2}},
        )
        disabled_healer = SimulaeNode(
            given_id="poi-2",
            nodetype=POI,
            abilities={"triage": {"enabled": False, "rank": 2}},
        )
        untrained = SimulaeNode(given_id="poi-3", nodetype=POI)
        object_with_ability = SimulaeNode(
            given_id="obj-1",
            nodetype=OBJ,
            abilities={"triage": {"enabled": True, "rank": 2}},
        )
        selector = SimulaeSelector(
            [
                SimulaeCondition(
                    "condition-1",
                    property_path=[NODETYPE],
                    rule=ConditionRuleType.EQUALS,
                    value=POI,
                ),
                SimulaeCondition(
                    "condition-2",
                    property_path=[ABILITIES, "triage", "enabled"],
                    rule=ConditionRuleType.EQUALS,
                    value=True,
                ),
            ]
        )

        selected = selector.select({healer, disabled_healer, untrained, object_with_ability})

        self.assertEqual({node.ID for node in selected}, {"poi-1"})
