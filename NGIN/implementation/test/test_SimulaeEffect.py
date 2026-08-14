import unittest

from NGIN.implementation.lib.SimulaeAction import SimulaeAction
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition, ConditionRuleType
from NGIN.implementation.lib.SimulaeEffect import SimulaeEffect, SimulaeEffectActionType
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
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
)


def condition(given_id, property_path, rule, value):
    simulae_condition = SimulaeCondition(given_id)
    simulae_condition.property_path = property_path
    simulae_condition.rule = rule
    simulae_condition.value = value
    return simulae_condition


def action(spec):
    return SimulaeAction(spec)


class TestSimulaeEffect(unittest.TestCase):
    def test_effect_initializes_as_meta_node_with_conditions_and_actions(self):
        effect = SimulaeEffect(
            "effect-1",
            name="Bruise",
            conditions=[
                condition("condition-1", [ATTRIBUTES, "health"], ConditionRuleType.GREATER_THAN, 0)
            ],
            actions=[
                action({"action": "decrement", "bucket": "attributes", "key": "health", "value": 5})
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
                actions=[{"action": "decrement", "bucket": "attributes", "key": "health", "value": 5}],
            )

        with self.assertRaises(TypeError):
            SimulaeEffect(
                "effect-1",
                conditions=[lambda **_kwargs: True],
            )

        with self.assertRaises(TypeError):
            SimulaeEffect(
                "effect-1",
                actions=[lambda **_kwargs: None],
            )

    def test_conditions_gate_effect_application(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 0})
        effect = SimulaeEffect(
            "effect-1",
            conditions=[
                condition("condition-1", [ATTRIBUTES, "health"], ConditionRuleType.GREATER_THAN, 0)
            ],
            actions=[
                action({"action": "decrement", "bucket": "attributes", "key": "health", "value": 5})
            ],
        )

        report = effect.apply(target)

        self.assertFalse(report["applied"])
        self.assertEqual(target.get_attribute("health"), 0)
        self.assertEqual(report["conditions"][0]["passed"], False)

    def test_condition_rule_enum_can_be_used_in_effect_conditions(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 5})
        effect = SimulaeEffect(
            "effect-1",
            conditions=[
                condition("condition-1", [ATTRIBUTES, "health"], ConditionRuleType.GREATER_THAN, 0)
            ],
            actions=[
                action({"action": "decrement", "bucket": "attributes", "key": "health", "value": 2})
            ],
        )

        report = effect.apply(target)

        self.assertTrue(report["applied"])
        self.assertEqual(target.get_attribute("health"), 3)

    def test_effect_action_type_enum_can_be_used_in_actions(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 5})
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    {
                        "action": SimulaeEffectActionType.INCREMENT,
                        "bucket": "attributes",
                        "key": "health",
                        "value": 4,
                    }
                )
            ],
        )

        report = effect.apply(target)

        self.assertTrue(report["applied"])
        self.assertEqual(target.get_attribute("health"), 9)

    def test_applies_reference_attribute_check_ability_and_memory_actions(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action({"action": "set", "bucket": "references", "key": NAME, "value": "Changed"}),
                action({"action": "decrement", "bucket": "attributes", "key": "health", "value": 3}),
                action({"action": "set", "bucket": "checks", "key": "bleeding", "value": True}),
                action({"action": "set", "bucket": "abilities", "key": "walk", "value": "disabled"}),
                action(
                    {
                        "action": "set",
                        "bucket": "memory",
                        "category": EVENTS,
                        "key": "effect-1",
                        "value": {"summary": "Changed"},
                    }
                ),
            ],
        )

        report = effect.apply(target)

        self.assertTrue(report["applied"])
        self.assertEqual(target.get_reference(NAME), "Changed")
        self.assertEqual(target.get_attribute("health"), 7)
        self.assertTrue(target.get_check("bleeding"))
        self.assertEqual(target.Abilities["walk"], "disabled")
        self.assertEqual(target.Memory[EVENTS]["effect-1"], {"summary": "Changed"})
        self.assertEqual(len(report["actions"]), 5)
        self.assertTrue(all(action["applied"] for action in report["actions"]))

    def test_removes_node_state_actions(self):
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
                action({"action": "remove", "bucket": REFERENCES, "key": NAME}),
                action({"action": "remove", "bucket": ATTRIBUTES, "key": "health"}),
                action({"action": "remove", "bucket": CHECKS, "key": "bleeding"}),
                action({"action": "remove", "bucket": ABILITIES, "key": "walk"}),
                action({"action": "remove", "bucket": MEMORY, "category": EVENTS, "key": "effect-1"}),
            ],
        )

        report = effect.apply(target)

        self.assertTrue(report["applied"])
        self.assertNotIn(NAME, target.References)
        self.assertNotIn("health", target.Attributes)
        self.assertNotIn("bleeding", target.Checks)
        self.assertNotIn("walk", target.Abilities)
        self.assertNotIn("effect-1", target.Memory[EVENTS])

    def test_adds_and_removes_relations(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        component = SimulaeNode(given_id="component-1", nodetype=OBJ, references={NAME: "Part"})
        add_effect = SimulaeEffect(
            "add-effect",
            actions=[
                action(
                    {
                        "action": "add",
                        "bucket": "relations",
                        "relation_type": COMPONENTS,
                        "node": component,
                    }
                )
            ],
        )
        remove_effect = SimulaeEffect(
            "remove-effect",
            actions=[
                action(
                    {
                        "action": "remove",
                        "bucket": "relations",
                        "relation_type": COMPONENTS,
                        "nodetype": OBJ,
                        "node_id": "component-1",
                    }
                )
            ],
        )

        self.assertTrue(add_effect.apply(target)["actions"][0]["applied"])
        self.assertIs(target.Relations[COMPONENTS][OBJ]["component-1"], component)
        self.assertTrue(remove_effect.apply(target)["actions"][0]["applied"])
        self.assertNotIn("component-1", target.Relations[COMPONENTS][OBJ])

    def test_relation_transmute_replaces_component(self):
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        old_component = SimulaeNode(given_id="old-component", nodetype=OBJ)
        new_component = SimulaeNode(given_id="new-component", nodetype=OBJ)
        target.set_relation(old_component, relation_type=COMPONENTS)
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    {
                        "action": "transmute",
                        "bucket": "relations",
                        "relation_type": COMPONENTS,
                        "old_node_id": old_component.ID,
                        "old_nodetype": OBJ,
                        "node": new_component,
                    }
                )
            ],
        )

        action_report = effect.apply(target)["actions"][0]

        self.assertTrue(action_report["applied"])
        self.assertNotIn(old_component.ID, target.Relations[COMPONENTS][OBJ])
        self.assertIs(target.Relations[COMPONENTS][OBJ][new_component.ID], new_component)

    def test_nested_effects_and_event_creation(self):
        source = SimulaeNode(given_id="source-1", nodetype=OBJ)
        target = SimulaeNode(given_id="target-1", nodetype=OBJ, attributes={"health": 10})
        nested = SimulaeEffect(
            "nested-effect",
            actions=[
                action({"action": "decrement", "bucket": "attributes", "key": "health", "value": 2})
            ],
        )
        effect = SimulaeEffect(
            "effect-1",
            name="Strike",
            actions=[
                action(nested),
                action(
                    {
                        "action": "create_event",
                        "id": "event-1",
                        "event_class": "physical",
                        "event_type": "damage",
                        "event_subtype": "strike",
                    }
                ),
            ],
        )

        report = effect.apply(target, source=source)

        self.assertTrue(report["applied"])
        self.assertEqual(target.get_attribute("health"), 8)
        self.assertTrue(report["actions"][0]["applied"])
        self.assertEqual(report["actions"][1]["event_id"], "event-1")
        event = report["actions"][1]["event"]
        self.assertIsInstance(event, SimulaeEvent)
        self.assertEqual(event.source_ids, ["source-1"])
        self.assertEqual(event.target_ids, ["target-1"])
        self.assertEqual(event.Effects, ["effect-1"])

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
                action({"action": "decrement", "bucket": "attributes", "key": "health", "value": 5})
            ],
        )

        report = effect.apply(
            targets=[target_1, target_2],
            sources=[source_1, source_2, "source-2"],
            observers=[observer_1, "observer-2"],
            create_event=True,
        )

        self.assertTrue(report["applied"])
        self.assertEqual(report["target_ids"], ["target-1", "target-2"])
        self.assertEqual(report["source_ids"], ["source-1", "source-2"])
        self.assertEqual(report["observer_ids"], ["observer-1", "observer-2"])
        self.assertEqual(target_1.get_attribute("health"), 5)
        self.assertEqual(target_2.get_attribute("health"), 15)
        self.assertEqual(len(report["targets"]), 2)
        self.assertEqual(len(report["events"]), 1)

        event = report["events"][0]["event"]
        self.assertEqual(event.source_ids, ["source-1", "source-2"])
        self.assertEqual(event.target_ids, ["target-1", "target-2"])
        self.assertEqual(event.observer_ids, ["observer-1", "observer-2"])

    def test_create_events_action_can_emit_multiple_events(self):
        source = SimulaeNode(given_id="source-1", nodetype=OBJ)
        observer = SimulaeNode(given_id="observer-1", nodetype=OBJ)
        target = SimulaeNode(given_id="target-1", nodetype=OBJ)
        effect = SimulaeEffect(
            "effect-1",
            actions=[
                action(
                    {
                        "action": "create_events",
                        "event_class": "physical",
                        "sources": ["source-override"],
                        "observers": ["observer-override"],
                        "events": [
                            {
                                "id": "event-1",
                                "event_type": "damage",
                                "event_subtype": "puncture",
                            },
                            {
                                "id": "event-2",
                                "event_type": "status",
                                "event_subtype": "bleeding",
                                "targets": ["target-2"],
                            },
                        ],
                    }
                )
            ],
        )

        report = effect.apply(target, source=source, observers=[observer])

        self.assertTrue(report["applied"])
        self.assertEqual(len(report["events"]), 2)
        self.assertEqual(report["events"][0]["event_id"], "event-1")
        self.assertEqual(report["events"][1]["event_id"], "event-2")
        self.assertEqual(report["events"][0]["event"].source_ids, ["source-override"])
        self.assertEqual(report["events"][0]["event"].observer_ids, ["observer-override"])
        self.assertEqual(report["events"][0]["event"].target_ids, ["target-1"])
        self.assertEqual(report["events"][1]["event"].target_ids, ["target-2"])
