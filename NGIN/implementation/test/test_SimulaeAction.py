import json
import unittest

from NGIN.implementation.lib.SimulaeAction import SimulaeAction, SimulaeEffectActionType
from NGIN.implementation.lib.SimulaeEffect import SimulaeEffect
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import (
    ACT,
    ATTRIBUTES,
    COMPONENTS,
    EVENTS,
    META_NODE_TYPES,
    MEMORY,
    NAME,
    OBJ,
    RELATIONS,
)


class TestSimulaeAction(unittest.TestCase):
    def test_action_uses_simulae_node_meta_structure(self):
        action = SimulaeAction(
            {"action": "increment", "bucket": "attributes", "key": "health", "value": 4},
            given_id="action-1",
            name="Heal",
        )

        self.assertIsInstance(action, SimulaeNode)
        self.assertEqual(action.ID, "action-1")
        self.assertEqual(action.Nodetype, ACT)
        self.assertIn(ACT, META_NODE_TYPES)
        self.assertEqual(action.References[NAME], "Heal")
        self.assertEqual(action.References[ACT], "increment")
        self.assertEqual(action.to_dict()["action"], "increment")

    def test_action_mutates_mapping_bucket(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 5})
        action = SimulaeAction(
            {
                "action": SimulaeEffectActionType.INCREMENT,
                "bucket": "attributes",
                "key": "health",
                "value": 4,
            }
        )

        report = action.apply(target)

        self.assertTrue(report["applied"])
        self.assertEqual(report["bucket"], ATTRIBUTES)
        self.assertEqual(report["before"], 5)
        self.assertEqual(report["after"], 9)
        self.assertEqual(target.get_attribute("health"), 9)

    def test_action_can_apply_to_multiple_targets(self):
        target_1 = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        target_2 = SimulaeNode(given_id="target-2", nodetype=OBJ, attributes={"health": 20})
        action = SimulaeAction(
            {"action": "decrement", "bucket": "attributes", "key": "health", "value": 5}
        )

        report = action.apply(targets=[target_1, target_2])

        self.assertTrue(report["applied"])
        self.assertEqual(report["target_ids"], ["target-1", "target-2"])
        self.assertEqual(target_1.get_attribute("health"), 5)
        self.assertEqual(target_2.get_attribute("health"), 15)
        self.assertEqual(len(report["targets"]), 2)

    def test_action_updates_memory_and_relations(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        component = SimulaeNode(given_id="component-1", nodetype=OBJ, references={NAME: "Part"})
        memory_action = SimulaeAction(
            {
                "action": "set",
                "bucket": MEMORY,
                "category": EVENTS,
                "key": "event-1",
                "value": {"summary": "remembered"},
            }
        )
        relation_action = SimulaeAction(
            {
                "action": "add",
                "bucket": RELATIONS,
                "relation_type": COMPONENTS,
                "node": component,
            }
        )

        self.assertTrue(memory_action.apply(target)["applied"])
        self.assertTrue(relation_action.apply(target)["applied"])
        self.assertEqual(target.Memory[EVENTS]["event-1"], {"summary": "remembered"})
        self.assertIs(target.Relations[COMPONENTS][OBJ]["component-1"], component)

    def test_action_creates_event_with_effect_context(self):
        source = SimulaeNode(given_id="source-1", nodetype=OBJ)
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        effect = SimulaeEffect("effect-1", name="Strike")
        action = SimulaeAction(
            {
                "action": "create_event",
                "id": "event-1",
                "event_class": "physical",
                "event_type": "damage",
                "event_subtype": "strike",
            },
            effect=effect,
        )

        report = action.apply(target, source=source, observers=["observer-1"])

        self.assertTrue(report["applied"])
        self.assertEqual(report["event_id"], "event-1")
        self.assertIsInstance(report["event"], SimulaeEvent)
        self.assertEqual(report["event"].source_ids, ["source-1"])
        self.assertEqual(report["event"].target_ids, ["target-1"])
        self.assertEqual(report["event"].observer_ids, ["observer-1"])
        self.assertEqual(report["event"].Effects, ["effect-1"])

    def test_action_can_trigger_nested_effect(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 8})
        nested_effect = SimulaeEffect(
            "nested-effect",
            actions=[
                SimulaeAction(
                    {"action": "decrement", "bucket": "attributes", "key": "health", "value": 3}
                )
            ],
        )
        action = SimulaeAction({"action": "trigger_effect", "effect": nested_effect})

        report = action.apply(target)

        self.assertTrue(report["applied"])
        self.assertEqual(report["action"], "trigger_effect")
        self.assertEqual(report["effect_id"], "nested-effect")
        self.assertEqual(target.get_attribute("health"), 5)

    def test_runtime_handles_are_represented_as_json_refs(self):
        def sample_action(**_kwargs):
            return "ok"

        component = SimulaeNode(given_id="component-1", nodetype=OBJ)
        nested_effect = SimulaeEffect("nested-effect")
        actions = [
            SimulaeAction(sample_action),
            SimulaeAction(nested_effect),
            SimulaeAction(
                {
                    "action": "add",
                    "bucket": "relations",
                    "relation_type": COMPONENTS,
                    "node": component,
                }
            ),
        ]

        for action in actions:
            with self.subTest(action=action.to_dict()):
                json.dumps(action.to_dict())

        self.assertIn("callable_ref", actions[0].References)
        self.assertEqual(actions[1].References["effect_id"], "nested-effect")
        self.assertEqual(
            actions[2].References["node"],
            {"node_id": "component-1", "nodetype": OBJ},
        )
