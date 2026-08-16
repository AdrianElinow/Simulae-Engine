import unittest

from NGIN.implementation.lib.ConditionRule import ConditionRuleType
from NGIN.implementation.lib.SimulaeAction import SimulaeAction
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeEffect import SimulaeEffect, SimulaeEffectActionType
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.implementation.lib.SimulaeSelector import SimulaeSelector
from NGIN.utilities.lib.SimulaeConstants import (
    ABILITIES,
    ATTRIBUTES,
    CHECKS,
    COMPONENTS,
    EFX,
    EVENTS,
    MEMORY,
    NAME,
    OBJ,
    REFERENCES,
    RELATIONS,
)


"""Focused SimulaeEffect unit tests.

These tests verify that effects gate targets with conditions, apply ordered
actions, and return only SimulaeEvent objects.
"""


def condition(given_id, property_path, rule, value=None):
    return SimulaeCondition(given_id, property_path, rule, value)


def action(action_type, **kwargs):
    return SimulaeAction(action_type, **kwargs)


class TestSimulaeEffect(unittest.TestCase):
    def test_effect_initializes_as_meta_node_with_conditions_and_actions(self):
        effect = SimulaeEffect(
            "effect-1",
            name="Bruise",
            conditions=[
                condition("condition-1", [ATTRIBUTES, "health"], ConditionRuleType.GREATER_THAN, 0)
            ],
            actions=[
                action(SimulaeEffectActionType.DECREMENT, values={f"{ATTRIBUTES}.health": 5})
            ],
        )

        self.assertEqual(effect.ID, "effect-1")
        self.assertEqual(effect.Nodetype, EFX)
        self.assertEqual(effect.References[NAME], "Bruise")
        self.assertEqual(len(effect.Conditions), 1)
        self.assertEqual(len(effect.Actions), 1)
        self.assertIsInstance(effect.Conditions[0], SimulaeCondition)
        self.assertIsInstance(effect.Actions[0], SimulaeAction)

    def test_effect_rejects_non_simulae_condition_and_action_inputs(self):
        with self.assertRaises(TypeError):
            SimulaeEffect(
                "effect-1",
                conditions=[{"path": [ATTRIBUTES, "health"], "rule": "greater_than", "value": 0}],
            )

        with self.assertRaises(TypeError):
            SimulaeEffect(
                "effect-1",
                actions=[
                    {
                        "action": SimulaeEffectActionType.DECREMENT,
                        "values": {f"{ATTRIBUTES}.health": 5},
                    }
                ],
            )

    def test_conditions_gate_effect_application(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 0})
        effect = SimulaeEffect(
            "effect-1",
            conditions=[
                condition("condition-1", [ATTRIBUTES, "health"], ConditionRuleType.GREATER_THAN, 0)
            ],
            actions=[
                action(SimulaeEffectActionType.DECREMENT, values={f"{ATTRIBUTES}.health": 5})
            ],
        )

        events = effect.apply(targets=[target])

        self.assertEqual(events, [])
        self.assertEqual(target.get_attribute("health"), 0)

    def test_effect_applies_action_value_paths(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    SimulaeEffectActionType.UPDATE,
                    values={
                        f"{REFERENCES}.{NAME}": "Changed",
                        f"{CHECKS}.bleeding": True,
                        f"{ABILITIES}.walk": "disabled",
                        f"{MEMORY}.{EVENTS}.effect-1": {"summary": "Changed"},
                    },
                    calculations=[
                        {"path": [ATTRIBUTES, "health"], "op": "decrement", "amount": 3},
                    ],
                )
            ],
        )

        events = effect.apply(targets=[target])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].References["action_type"], "update")
        self.assertEqual(events[0].Effects, ["effect-1"])
        self.assertEqual(target.get_reference(NAME), "Changed")
        self.assertEqual(target.get_attribute("health"), 7)
        self.assertTrue(target.get_check("bleeding"))
        self.assertEqual(target.Abilities["walk"], "disabled")
        self.assertEqual(target.Memory[EVENTS]["effect-1"], {"summary": "Changed"})

    def test_effect_removes_state_with_paths(self):
        target = SimulaeNode(
            given_id="target-1",
            nodetype=OBJ,
            references={NAME: "Before"},
            attributes={"health": 10},
            checks={"bleeding": True},
            abilities={"walk": "disabled"},
        )
        target.Memory[EVENTS]["effect-1"] = {"summary": "Before"}
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    SimulaeEffectActionType.REMOVE,
                    values=[
                        [REFERENCES, NAME],
                        [ATTRIBUTES, "health"],
                        [CHECKS, "bleeding"],
                        [ABILITIES, "walk"],
                        [MEMORY, EVENTS, "effect-1"],
                    ],
                )
            ],
        )

        events = effect.apply(targets=[target])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].References["action_type"], "remove")
        self.assertNotIn(NAME, target.References)
        self.assertNotIn("health", target.Attributes)
        self.assertNotIn("bleeding", target.Checks)
        self.assertNotIn("walk", target.Abilities)
        self.assertNotIn("effect-1", target.Memory[EVENTS])

    def test_action_acceptance_selector_filters_effect_targets(self):
        wounded = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        healthy = SimulaeNode(given_id="target-2", nodetype=OBJ, attributes={"health": 120})
        selector = SimulaeSelector(
            [
                condition("wounded", [ATTRIBUTES, "health"], ConditionRuleType.LESS_THAN, 100)
            ]
        )
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    SimulaeEffectActionType.INCREMENT,
                    acceptance_selector=selector,
                    values={f"{ATTRIBUTES}.health": 5},
                )
            ],
        )

        events = effect.apply(targets=[wounded, healthy])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].target_ids, ["target-1"])
        self.assertEqual(wounded.get_attribute("health"), 15)
        self.assertEqual(healthy.get_attribute("health"), 120)

    def test_output_nodes_can_add_and_remove_relations(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        component = SimulaeNode(given_id="component-1", nodetype=OBJ, references={NAME: "Part"})
        add_effect = SimulaeEffect(
            "add-effect",
            actions=[
                action(
                    SimulaeEffectActionType.COMPOSE,
                    output_nodes=[{"path": [RELATIONS, COMPONENTS], "node": component}],
                )
            ],
        )
        remove_effect = SimulaeEffect(
            "remove-effect",
            actions=[
                action(
                    SimulaeEffectActionType.DECOMPOSE,
                    output_nodes=[{"path": [RELATIONS, COMPONENTS], "node": component}],
                )
            ],
        )

        add_events = add_effect.apply(targets=[target])
        remove_events = remove_effect.apply(targets=[target])

        self.assertEqual(add_events[0].References["action_type"], "compose")
        self.assertEqual(remove_events[0].References["action_type"], "decompose")
        self.assertNotIn("component-1", target.Relations[COMPONENTS][OBJ])

    def test_nested_effects_and_event_creation(self):
        source = SimulaeNode(given_id="source-1", nodetype=OBJ)
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        nested = SimulaeEffect(
            "nested-effect",
            actions=[
                action(SimulaeEffectActionType.DECREMENT, values={f"{ATTRIBUTES}.health": 2})
            ],
        )
        effect = SimulaeEffect(
            "effect-1",
            name="Strike",
            actions=[
                action(SimulaeEffectActionType.TRIGGER_EFFECT, output_templates=[nested]),
                action(
                    SimulaeEffectActionType.CREATE_EVENT,
                    output_templates={
                        "id": "event-1",
                        "class": "physical",
                        "type": "damage",
                        "subtype": "strike",
                    },
                ),
            ],
        )

        events = effect.apply(targets=[target], sources=[source])

        self.assertEqual(len(events), 3)
        self.assertEqual(target.get_attribute("health"), 8)
        self.assertEqual(events[0].References["action_type"], "trigger_effect")
        self.assertEqual(events[1].References["action_type"], "decrement")
        self.assertEqual(events[2].ID, "event-1")
        self.assertIsInstance(events[2], SimulaeEvent)
        self.assertEqual(events[2].source_ids, ["source-1"])
        self.assertEqual(events[2].target_ids, ["target-1"])
        self.assertEqual(events[2].Effects, ["effect-1"])

    def test_apply_supports_multiple_sources_observers_targets_and_summary_event(self):
        source_1 = SimulaeNode(given_id="source-1", nodetype=OBJ)
        source_2 = SimulaeNode(given_id="source-2", nodetype=OBJ)
        observer_1 = SimulaeNode(given_id="observer-1", nodetype=OBJ)
        target_1 = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        target_2 = SimulaeNode(given_id="target-2", nodetype=OBJ, attributes={"health": 20})
        effect = SimulaeEffect(
            "effect-1",
            name="Area Strike",
            conditions=[
                condition("condition-1", [ATTRIBUTES, "health"], ConditionRuleType.GREATER_THAN, 0),
                condition("condition-2", [ATTRIBUTES, "health"], ConditionRuleType.LESS_THAN_OR_EQUAL, 20),
            ],
            actions=[
                action(SimulaeEffectActionType.DECREMENT, values={f"{ATTRIBUTES}.health": 5})
            ],
        )

        events = effect.apply(
            targets=[target_1, target_2],
            sources=[source_1, source_2, "source-2"],
            observers=[observer_1, "observer-2"],
            create_event=True,
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(target_1.get_attribute("health"), 5)
        self.assertEqual(target_2.get_attribute("health"), 15)
        self.assertEqual(events[0].source_ids, ["source-1", "source-2"])
        self.assertEqual(events[0].observer_ids, ["observer-1", "observer-2"])
        self.assertEqual(events[-1].References["effect_occurred"], True)
        self.assertEqual(events[-1].target_ids, ["target-1", "target-2"])

    def test_create_events_action_can_emit_multiple_events(self):
        source = SimulaeNode(given_id="source-1", nodetype=OBJ)
        observer = SimulaeNode(given_id="observer-1", nodetype=OBJ)
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    SimulaeEffectActionType.CREATE_EVENTS,
                    output_templates=[
                        {
                            "id": "event-1",
                            "class": "physical",
                            "type": "damage",
                            "subtype": "puncture",
                            "sources": ["source-override"],
                            "observers": ["observer-override"],
                        },
                        {
                            "id": "event-2",
                            "type": "status",
                            "subtype": "bleeding",
                            "targets": ["target-2"],
                        },
                    ],
                )
            ],
        )

        events = effect.apply(targets=[target], sources=[source], observers=[observer])

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].ID, "event-1")
        self.assertEqual(events[1].ID, "event-2")
        self.assertEqual(events[0].source_ids, ["source-override"])
        self.assertEqual(events[0].observer_ids, ["observer-override"])
        self.assertEqual(events[0].target_ids, ["target-1"])
        self.assertEqual(events[1].target_ids, ["target-2"])
