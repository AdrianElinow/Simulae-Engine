import unittest

from NGIN.implementation.lib.ConditionRule import ConditionRuleType
from NGIN.implementation.lib.SimulaeAction import SimulaeAction, SimulaeEffectActionType
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeEffect import SimulaeEffect
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.implementation.lib.SimulaeSelector import SimulaeSelector
from NGIN.utilities.lib.SimulaeConstants import (
    ABILITIES,
    ATTRIBUTES,
    CHECKS,
    COMPONENTS,
    CONTENTS,
    EVENTS,
    MEMORY,
    NAME,
    OBJ,
    POI,
    REFERENCES,
    RELATIONS,
)

"""Documentation-inspired SimulaeAction and SimulaeEffect examples.

These tests translate the wiki's intended uses into executable examples. They
cover core Simulae Effect documentation examples such as walking, stabilizing
bleeding, inanimate object abilities, damage, transmutation, and event creation,
plus a broad smoke-test over the video game inspiration structure.
"""


INSPIRATION_GAME_CONTEXTS = [
    ("Aneurism IV", "rot_pressure"),
    ("Beta Decay", "radiation_pressure"),
    ("Darkest Dungeon", "stress_pressure"),
    ("Deus Ex", "augmentation_pressure"),
    ("Dishonored", "chaos_pressure"),
    ("Dwarf Fortress", "fortress_pressure"),
    ("Elder Scrolls: Oblivion", "quest_pressure"),
    ("Elder Scrolls: Skyrim", "civil_war_pressure"),
    ("Fallout: New Vegas", "reputation_pressure"),
    ("Far Cry 2", "fire_pressure"),
    ("Far Cry 3", "outpost_pressure"),
    ("Far Cry 4", "faction_pressure"),
    ("Far Cry 5", "resistance_pressure"),
    ("Hitman: World of Assassination", "suspicion_pressure"),
    ("Offworld Trading Company", "market_pressure"),
    ("Prey 2017", "station_pressure"),
    ("RimWorld", "colony_pressure"),
    ("Shadows of Doubt", "investigation_pressure"),
    ("System Shock 2", "system_pressure"),
    ("Trouble in Terrorist Town", "trust_pressure"),
    ("Weird West", "reputation_pressure"),
]


def condition(given_id, property_path, rule, value=None):
    return SimulaeCondition(given_id, property_path, rule, value)


def selector(*conditions):
    return SimulaeSelector(conditions)


class TestSimulaeActionDocumentationExamples(unittest.TestCase):
    def test_hitman_disguise_action_updates_social_state_and_memory(self):
        # Hitman inspiration: disguises and suspicion are social state changes,
        # and the action records the moment as memory for later systems.
        operative = SimulaeNode(
            given_id="agent-47",
            nodetype=POI,
            references={NAME: "Agent 47", "disguise": "Suit"},
            checks={"suspicious": True},
        )
        action = SimulaeAction(
            SimulaeEffectActionType.UPDATE,
            acceptance_selector=selector(
                condition("only-people", ["Nodetype"], ConditionRuleType.EQUALS, POI)
            ),
            values={
                f"{REFERENCES}.disguise": "Staff",
                f"{CHECKS}.suspicious": False,
                f"{MEMORY}.{EVENTS}.disguise-change": {
                    "inspiration": "Hitman: World of Assassination",
                    "summary": "Changed disguise to move through the venue.",
                },
            },
        )

        events = action.act(targets=[operative])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].References["action_type"], "update")
        self.assertEqual(operative.References["disguise"], "Staff")
        self.assertFalse(operative.Checks["suspicious"])
        self.assertEqual(
            operative.Memory[EVENTS]["disguise-change"]["inspiration"],
            "Hitman: World of Assassination",
        )

    def test_aneurism_scavenging_can_transmute_scrap_into_contraband_weapon(self):
        # Aneurism IV inspiration: scavenging/crafting can transmute one contained
        # item into another and create heat because weapons affect law pressure.
        locker = SimulaeNode(given_id="locker-1", nodetype=OBJ, references={NAME: "Locker"})
        scrap = SimulaeNode(given_id="scrap-metal", nodetype=OBJ, references={NAME: "Scrap Metal"})
        shiv = SimulaeNode(
            given_id="improvised-shiv",
            nodetype=OBJ,
            references={NAME: "Improvised Shiv"},
            checks={"contraband": True},
        )
        locker.set_relation(scrap, relation_type=CONTENTS)
        action = SimulaeAction(
            SimulaeEffectActionType.TRANSMUTE,
            output_nodes=[
                {"path": [RELATIONS, CONTENTS], "node": scrap, "op": "remove"},
                {"path": [RELATIONS, CONTENTS], "node": shiv, "op": "add"},
            ],
            values={f"{CHECKS}.created_heat": True},
        )

        events = action.act(targets=[locker])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].References["action_type"], "transmute")
        self.assertNotIn("scrap-metal", locker.Relations[CONTENTS][OBJ])
        self.assertIs(locker.Relations[CONTENTS][OBJ]["improvised-shiv"], shiv)
        self.assertTrue(locker.Checks["created_heat"])


class TestSimulaeEffectDocumentationExamples(unittest.TestCase):
    def test_walking_effect_costs_energy_and_updates_location(self):
        # Simulae Effect docs: walking is an ability granted by locomotive
        # components, costs energy/oxygen, and updates the actor's location.
        actor = SimulaeNode(
            given_id="walker-1",
            nodetype=POI,
            references={"location": "room-a"},
            attributes={"calories": 100, "oxygen": 10},
            abilities={"walk": "enabled"},
        )
        legs = SimulaeNode(given_id="legs", nodetype=OBJ, references={NAME: "Legs"})
        actor.set_relation(legs, relation_type=COMPONENTS)
        effect = SimulaeEffect(
            "walk-to-room-b",
            conditions=[
                condition("can-walk", [ABILITIES, "walk"], ConditionRuleType.EQUALS, "enabled"),
                condition("has-legs", [RELATIONS, COMPONENTS, OBJ, "legs"], ConditionRuleType.EXISTS),
            ],
            actions=[
                SimulaeAction(
                    SimulaeEffectActionType.UPDATE,
                    values={f"{REFERENCES}.location": "room-b"},
                    calculations=[
                        {"path": [ATTRIBUTES, "calories"], "op": "decrement", "amount": 5},
                        {"path": [ATTRIBUTES, "oxygen"], "op": "decrement", "amount": 1},
                    ],
                )
            ],
        )

        events = effect.apply(targets=[actor])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].References["action_type"], "update")
        self.assertEqual(actor.References["location"], "room-b")
        self.assertEqual(actor.Attributes["calories"], 95)
        self.assertEqual(actor.Attributes["oxygen"], 9)

    def test_bandage_effect_stabilizes_bleeding_body_part(self):
        # Simulae Effect docs: bandages are inanimate objects with a stabilizing
        # ability that lets healing outpace bleeding.
        arm = SimulaeNode(
            given_id="left-arm",
            nodetype=OBJ,
            references={NAME: "Left Arm"},
            checks={"bleeding": True},
            abilities={"heal": "outpaced"},
        )
        bandage = SimulaeNode(given_id="bandage", nodetype=OBJ, references={NAME: "Bandage"})
        effect = SimulaeEffect(
            "bandage-stabilize",
            conditions=[
                condition("is-bleeding", [CHECKS, "bleeding"], ConditionRuleType.EQUALS, True)
            ],
            actions=[
                SimulaeAction(
                    SimulaeEffectActionType.UPDATE,
                    values={
                        f"{CHECKS}.bleeding": False,
                        f"{ABILITIES}.heal": "stabilized",
                    },
                ),
                SimulaeAction(
                    SimulaeEffectActionType.CREATE_EVENT,
                    output_templates={
                        "id": "bandage-event",
                        "class": "medical",
                        "type": "stabilize",
                        "subtype": "bleeding",
                    },
                ),
            ],
        )

        events = effect.apply(targets=[arm], sources=[bandage])

        self.assertEqual(len(events), 2)
        self.assertFalse(arm.Checks["bleeding"])
        self.assertEqual(arm.Abilities["heal"], "stabilized")
        self.assertEqual(events[1].source_ids, ["bandage"])

    def test_damage_effect_can_puncture_organs_disable_ability_and_emit_event(self):
        # Damage model docs: a bullet can puncture an organ, reduce integrity,
        # cause bleeding, compromise an ability, and emit a world event.
        lung = SimulaeNode(
            given_id="lung",
            nodetype=OBJ,
            references={NAME: "Lung"},
            attributes={"integrity": 80},
            checks={"bleeding": False},
            abilities={"breathing": "enabled"},
        )
        bullet = SimulaeNode(given_id="bullet", nodetype=OBJ, references={NAME: "Bullet"})
        effect = SimulaeEffect(
            "bullet-puncture",
            conditions=[
                condition("intact-organ", [ATTRIBUTES, "integrity"], ConditionRuleType.GREATER_THAN, 0)
            ],
            actions=[
                SimulaeAction(
                    SimulaeEffectActionType.UPDATE,
                    values={
                        f"{CHECKS}.bleeding": True,
                        f"{ABILITIES}.breathing": "compromised",
                    },
                    calculations=[
                        {"path": [ATTRIBUTES, "integrity"], "op": "decrement", "amount": 50}
                    ],
                ),
                SimulaeAction(
                    SimulaeEffectActionType.CREATE_EVENT,
                    output_templates={
                        "id": "puncture-event",
                        "class": "physical",
                        "type": "damage",
                        "subtype": "organ-puncture",
                    },
                ),
            ],
        )

        events = effect.apply(targets=[lung], sources=[bullet])

        self.assertEqual(len(events), 2)
        self.assertEqual(lung.Attributes["integrity"], 30)
        self.assertTrue(lung.Checks["bleeding"])
        self.assertEqual(lung.Abilities["breathing"], "compromised")
        self.assertIsInstance(events[1], SimulaeEvent)

    def test_lightswitch_effect_updates_inanimate_light_ability(self):
        # Inanimate object docs: a switch can update a light's ability state and
        # consume electricity when the light turns on.
        light = SimulaeNode(
            given_id="electric-light",
            nodetype=OBJ,
            attributes={"electricity": 10},
            checks={"powered": True},
            abilities={"emit_light": "off"},
        )
        switch = SimulaeNode(given_id="lightswitch", nodetype=OBJ, abilities={"flick": "enabled"})
        effect = SimulaeEffect(
            "turn-on-light",
            conditions=[
                condition("has-power", [CHECKS, "powered"], ConditionRuleType.EQUALS, True)
            ],
            actions=[
                SimulaeAction(
                    SimulaeEffectActionType.UPDATE,
                    values={f"{ABILITIES}.emit_light": "on"},
                    calculations=[
                        {"path": [ATTRIBUTES, "electricity"], "op": "decrement", "amount": 1}
                    ],
                )
            ],
        )

        events = effect.apply(targets=[light], sources=[switch])

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].source_ids, ["lightswitch"])
        self.assertEqual(light.Abilities["emit_light"], "on")
        self.assertEqual(light.Attributes["electricity"], 9)

    def test_aneurism_rot_threshold_triggers_limitation_order_event(self):
        # Aneurism IV Rot docs: high Rot creates pressure and can trigger a
        # Limitation Order event.
        district = SimulaeNode(
            given_id="district-1",
            nodetype=OBJ,
            references={NAME: "Industrial District"},
            attributes={"rot": 85},
            checks={"limitation_order": False},
        )
        effect = SimulaeEffect(
            "rot-limitation-threshold",
            conditions=[
                condition("enough-rot", [ATTRIBUTES, "rot"], ConditionRuleType.GREATER_THAN_OR_EQUAL, 80)
            ],
            actions=[
                SimulaeAction(
                    SimulaeEffectActionType.UPDATE,
                    values={f"{CHECKS}.limitation_order": True},
                ),
                SimulaeAction(
                    SimulaeEffectActionType.CREATE_EVENT,
                    output_templates={
                        "id": "limitation-order",
                        "class": "city",
                        "type": "rot",
                        "subtype": "limitation-order",
                    },
                ),
            ],
        )

        events = effect.apply(targets=[district])

        self.assertEqual(len(events), 2)
        self.assertTrue(district.Checks["limitation_order"])
        self.assertEqual(events[1].References["event_type"], "rot")

    def test_inspiration_video_game_scenarios_can_emit_basic_system_events(self):
        # The Inspirations folder lists many target game scenarios. This broad
        # table-driven test keeps a basic "pressure changes and emits an event"
        # example attached to each listed game without encoding full game rules.
        for game_name, pressure_key in INSPIRATION_GAME_CONTEXTS:
            with self.subTest(game=game_name):
                slug = pressure_key.replace("_", "-")
                scenario = SimulaeNode(
                    given_id=f"{slug}-scenario",
                    nodetype=OBJ,
                    references={NAME: game_name},
                    attributes={pressure_key: 0},
                )
                effect = SimulaeEffect(
                    f"{slug}-effect",
                    actions=[
                        SimulaeAction(
                            SimulaeEffectActionType.INCREMENT,
                            values={f"{ATTRIBUTES}.{pressure_key}": 1},
                        ),
                        SimulaeAction(
                            SimulaeEffectActionType.CREATE_EVENT,
                            output_templates={
                                "id": f"{slug}-event",
                                "class": "inspiration",
                                "type": game_name,
                                "subtype": pressure_key,
                            },
                        ),
                    ],
                )

                events = effect.apply(targets=[scenario])

                self.assertEqual(len(events), 2)
                self.assertEqual(scenario.Attributes[pressure_key], 1)
                self.assertEqual(events[1].References["event_type"], game_name)
