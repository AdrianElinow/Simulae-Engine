import json
import unittest

from NGIN.implementation.lib.ConditionRule import ConditionRuleType
from NGIN.implementation.lib.SimulaeAction import SimulaeAction, SimulaeEffectActionType
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeEffect import SimulaeEffect
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.implementation.lib.SimulaeSelector import SimulaeSelector
from NGIN.utilities.lib.SimulaeConstants import (
    ACT,
    ATTRIBUTES,
    COMPONENTS,
    META_NODE_TYPES,
    NAME,
    OBJ,
    RELATIONS,
)


"""Focused SimulaeAction unit tests.

These tests verify the compact action API and the event-only execution contract:
actions mutate accepted nodes and return SimulaeEvent objects describing what
occurred.
"""


def condition(given_id, property_path, rule, value=None):
    return SimulaeCondition(given_id, property_path, rule, value)


class TestSimulaeAction(unittest.TestCase):
    def test_action_uses_simple_meta_node_shape(self):
        action = SimulaeAction(
            SimulaeEffectActionType.INCREMENT,
            values={f"{ATTRIBUTES}.health": 4},
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

    def test_action_updates_target_state_and_returns_action_event(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 5})
        action = SimulaeAction(
            SimulaeEffectActionType.UPDATE,
            values={
                (ATTRIBUTES, "health"): 9,
                f"{ATTRIBUTES}.stamina": 3,
            },
        )

        events = action.act(targets=[target])

        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], SimulaeEvent)
        self.assertEqual(events[0].References["action_type"], "update")
        self.assertEqual(events[0].References["event_type"], "update")
        self.assertEqual(events[0].target_ids, ["target-1"])
        self.assertEqual(target.get_attribute("health"), 9)
        self.assertEqual(target.get_attribute("stamina"), 3)
        changes = events[0].References["details"]["changes"]
        self.assertEqual(len(changes), 2)
        self.assertTrue(all("applied" not in change for change in changes))

    def test_action_applies_calculations_to_multiple_targets(self):
        target_1 = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        target_2 = SimulaeNode(given_id="target-2", nodetype=OBJ, attributes={"health": 20})
        action = SimulaeAction(
            SimulaeEffectActionType.UPDATE,
            calculations=[
                {"path": [ATTRIBUTES, "health"], "op": "decrement", "amount": 5},
            ],
        )

        events = action.act(targets=[target_1, target_2])

        self.assertEqual(len(events), 2)
        self.assertEqual([event.target_ids[0] for event in events], ["target-1", "target-2"])
        self.assertEqual(target_1.get_attribute("health"), 5)
        self.assertEqual(target_2.get_attribute("health"), 15)

    def test_conditions_and_acceptance_selector_gate_actions(self):
        wounded_object = SimulaeNode(given_id="obj-1", nodetype=OBJ, attributes={"health": 50})
        healthy_object = SimulaeNode(given_id="obj-2", nodetype=OBJ, attributes={"health": 120})
        accepted = SimulaeSelector(
            [
                condition("is-obj", ["Nodetype"], ConditionRuleType.EQUALS, OBJ),
            ]
        )
        needs_healing = condition("wounded", [ATTRIBUTES, "health"], ConditionRuleType.LESS_THAN, 100)
        action = SimulaeAction(
            SimulaeEffectActionType.INCREMENT,
            conditions=[needs_healing],
            acceptance_selector=accepted,
            values={f"{ATTRIBUTES}.health": 25},
        )

        events = action.act(targets=[wounded_object, healthy_object])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].target_ids, ["obj-1"])
        self.assertEqual(wounded_object.get_attribute("health"), 75)
        self.assertEqual(healthy_object.get_attribute("health"), 120)

    def test_output_nodes_can_be_composed_into_relation_paths(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        component = SimulaeNode(given_id="component-1", nodetype=OBJ, references={NAME: "Part"})
        action = SimulaeAction(
            SimulaeEffectActionType.COMPOSE,
            output_nodes=[
                {
                    "path": [RELATIONS, COMPONENTS],
                    "node": component,
                }
            ],
        )

        events = action.act(targets=[target])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].References["action_type"], "compose")
        self.assertIs(target.Relations[COMPONENTS][OBJ]["component-1"], component)

    def test_nested_effects_are_outputs_for_trigger_effect_actions(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 8})
        nested_effect = SimulaeEffect(
            "nested-effect",
            actions=[
                SimulaeAction(
                    SimulaeEffectActionType.DECREMENT,
                    values={f"{ATTRIBUTES}.health": 3},
                )
            ],
        )
        action = SimulaeAction(
            SimulaeEffectActionType.TRIGGER_EFFECT,
            output_templates=[nested_effect],
        )

        events = action.act(targets=[target])

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].References["action_type"], "trigger_effect")
        self.assertEqual(events[1].References["action_type"], "decrement")
        self.assertEqual(target.get_attribute("health"), 5)

    def test_event_templates_create_events(self):
        source = SimulaeNode(given_id="source-1", nodetype=OBJ)
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        effect = SimulaeEffect("effect-1", name="Strike")
        action = SimulaeAction(
            SimulaeEffectActionType.CREATE_EVENT,
            output_templates={
                "id": "event-1",
                "class": "physical",
                "type": "damage",
                "subtype": "strike",
            },
        )

        events = action.act(targets=[target], sources=[source], observers=["observer-1"], effects=[effect])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].ID, "event-1")
        self.assertEqual(events[0].References["action_type"], "create_event")
        self.assertEqual(events[0].source_ids, ["source-1"])
        self.assertEqual(events[0].target_ids, ["target-1"])
        self.assertEqual(events[0].observer_ids, ["observer-1"])
        self.assertEqual(events[0].Effects, ["effect-1"])

    def test_output_objects_are_represented_as_json_refs(self):
        component = SimulaeNode(given_id="component-1", nodetype=OBJ)
        nested_effect = SimulaeEffect("nested-effect")
        action = SimulaeAction(
            SimulaeEffectActionType.COMPOSE,
            output_nodes=[component],
            output_templates=[nested_effect],
        )

        data = action.to_dict()

        json.dumps(data)
        self.assertEqual(data["output_nodes"], [{"node_id": "component-1", "nodetype": OBJ}])
        self.assertEqual(data["output_templates"], [{"effect_id": "nested-effect"}])
