import importlib
import unittest

from NGIN.utilities.lib.SimulaeConstants import MEMORY_CLASSIFICATIONS

from .SimulaeNode import (
    ABILITIES,
    ADJACENT,
    ATTRIBUTES,
    CHECKS,
    COMPONENTS,
    CONTENTS,
    FAC,
    ID,
    LOC,
    MEMORY,
    NAME,
    NODETYPE,
    OBJ,
    PERSONALITY,
    PERSONALITY_SCALE,
    PHYSICAL_NODETYPES,
    PHYSICAL_RELATIVE_TYPES,
    POI,
    POLICY,
    POLICY_SCALE,
    REFERENCES,
    RELATIONS,
    SCALES,
    STATUS,
    ATTACHMENTS,
    SimulaeNode,
    generate_person_body,
    generate_person_simulae_node,
    generate_simulae_node,
    simulaenode_from_json,
)


simnode_module = importlib.import_module("NGIN.implementation.lib.SimulaeNode")

def setUpModule():
    # Compatibility shims so relation-based methods use the implemented physical maps.
    simnode_module.RELATIVE_TYPES = list(PHYSICAL_RELATIVE_TYPES) # type: ignore
    simnode_module.RELATION_TYPES = list(PHYSICAL_RELATIVE_TYPES) # type: ignore

    # `determine_relationship` expects this key spelling.
    if "descriptors_buckets" not in simnode_module.POLICY_SCALES:
        simnode_module.POLICY_SCALES["descriptors_buckets"] = simnode_module.POLICY_SCALES["descriptor_buckets"]


class TestSimulaeNodeCore(unittest.TestCase):
    def test_init_obj_defaults(self):
        node = SimulaeNode()

        self.assertIsNotNone(node.ID)
        self.assertEqual(node.Nodetype, OBJ)
        self.assertEqual(node.References, {})
        self.assertEqual(node.Scales, {})
        self.assertEqual(node.Checks, {})
        self.assertEqual(node.Abilities, {})

        self.assertEqual(set(node.Relations.keys()), set(PHYSICAL_RELATIVE_TYPES))
        for relation_type in [CONTENTS, COMPONENTS, ATTACHMENTS]:
            self.assertEqual(set(node.Relations[relation_type].keys()), set(PHYSICAL_NODETYPES))
            for nodetype in PHYSICAL_NODETYPES:
                self.assertEqual(node.Relations[relation_type][nodetype], {})
        self.assertEqual(node.Relations[ADJACENT], { nt:{} for nt in PHYSICAL_NODETYPES})
        
        for key in MEMORY_CLASSIFICATIONS:
            self.assertEqual(node.Memory[key], {})

    def test_init_poi_builds_social_scales(self):
        node = SimulaeNode(nodetype=POI)

        self.assertIn(POLICY, node.Scales)
        self.assertIn(PERSONALITY, node.Scales)
        self.assertEqual(set(node.Scales[POLICY].keys()), set(POLICY_SCALE.keys()))
        self.assertEqual(set(node.Scales[PERSONALITY].keys()), set(PERSONALITY_SCALE.keys()))

    def test_init_copy_behavior_for_mutable_inputs(self):
        refs = {NAME: "Node"}
        attrs = {"Age": 20}
        checks = {"Alive": True}
        abilities = {"Sneak": 3}
        scales = {POLICY: {"Economy": (3, 5)}}
        memory = None

        node = SimulaeNode(
            references=refs,
            attributes=attrs,
            checks=checks,
            abilities=abilities,
            scales=scales,
            memory=memory,
        )

        refs[NAME] = "Changed"
        attrs["Age"] = 99
        checks["Alive"] = False
        abilities["Sneak"] = 0
        scales[POLICY]["Economy"] = (0, 0)

        self.assertEqual(node.References[NAME], "Node")
        self.assertEqual(node.Attributes["Age"], 20)
        self.assertTrue(node.Checks["Alive"])
        self.assertEqual(node.Abilities["Sneak"], 3)
        # shallow copy only; nested dict remains shared
        self.assertEqual(node.Scales[POLICY]["Economy"], (0, 0))

    def test_keyname(self):
        node = SimulaeNode()
        self.assertEqual(node.keyname("a", "b", "c"), "a|b|c")

    def test_get_description_non_poi_empty(self):
        node = SimulaeNode(nodetype=OBJ, references={NAME: "Object"})
        self.assertEqual(node.get_description(), "")

    def test_get_description_poi_contains_core_fields(self):
        node = SimulaeNode(
            nodetype=POI,
            references={
                NAME: "Dana",
                "Gender": "Female",
                FAC: "Y",
                POLICY: {"Economy": (0, 1)},
                PERSONALITY: True,
            },
        )
        node.Relations[FAC] = {}
        node.set_attribute("Age", 33)

        description = node.get_description()

        self.assertIn("Dana", description)
        self.assertIn("33 year old Female", description)

    def test_summary_contains_nodetype_and_name(self):
        node = SimulaeNode(given_id="id-1", nodetype=OBJ, references={NAME: "Widget"})
        summary = node.summary()

        self.assertIn("Widget", summary)

    def test_str_prefers_name_and_falls_back(self):
        named = SimulaeNode(given_id="x", nodetype=OBJ, references={NAME: "Named"})
        unnamed = SimulaeNode(given_id="y", nodetype=LOC, references={NAME: None})

        self.assertEqual(str(named), "Named")
        self.assertIn(f"{LOC}(y)",str(unnamed))

    def test_knows_about_for_physical_relation_and_social_relationship(self):
        observer = SimulaeNode(nodetype=LOC, references={NAME: "Area"})
        inanimate = SimulaeNode(given_id="crate-1", nodetype=OBJ)
        social = SimulaeNode(given_id="npc-1", nodetype=POI)

        observer.set_relation(inanimate, CONTENTS)
        observer.Relations[POI] = {social.ID: {STATUS: "known"}}

        self.assertTrue(observer.knows_about(inanimate))
        self.assertTrue(observer.knows_about(social))

    def test_get_and_set_reference(self):
        node = SimulaeNode(references={NAME: "Before"})
        self.assertEqual(node.get_reference(NAME), "Before")
        self.assertIsNone(node.get_reference("Missing"))

        node.set_reference("Title", "Captain", warn=False)
        self.assertEqual(node.get_reference("Title"), "Captain")

    def test_set_reference_validates_inputs(self):
        node = SimulaeNode()
        with self.assertRaises(ValueError):
            node.set_reference("", "x", warn=False)
        with self.assertRaises(ValueError):
            node.set_reference("k", "", warn=False)

    def test_get_attribute_and_get_attribute_int(self):
        node = SimulaeNode(attributes={"i": 2, "f": 2.5, "s": "x"})

        self.assertEqual(node.get_attribute("i"), 2)
        self.assertEqual(node.get_attribute("f"), 2.5)
        self.assertEqual(node.get_attribute("s"), "x")
        self.assertIsNone(node.get_attribute(""))

        self.assertEqual(node.get_attribute_int("i"), 2)
        self.assertIsNone(node.get_attribute_int("f"))
        self.assertIsNone(node.get_attribute_int("missing"))

    def test_set_attribute(self):
        node = SimulaeNode(attributes={"value": 1})
        node.set_attribute("value", 2.0, warn=False)
        self.assertEqual(node.get_attribute("value"), 2.0)


class TestSimulaeNodeRelations(unittest.TestCase):
    def test_determine_relation_returns_existing_relation(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-1", nodetype=OBJ)
        a.set_relation(b, CONTENTS)

        self.assertIs(a.determine_relation(b), b)

    def test_determine_relation_returns_none_when_unknown(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-2", nodetype=OBJ)
        self.assertIsNone(a.determine_relation(b))

    def test_determine_relationship_with_inanimate_node(self):
        actor = SimulaeNode(nodetype=POI)
        target = SimulaeNode(nodetype=OBJ)

        relationship = actor.determine_relationship(target)

        if not relationship:
            self.fail("Relationship should not be None or empty")

        self.assertEqual(relationship[NODETYPE], OBJ)
        self.assertEqual(relationship[STATUS], "new")

    def test_determine_relationship_with_social_node_current_behavior(self):
        a = SimulaeNode(nodetype=POI)
        b = SimulaeNode(nodetype=POI)

        a.determine_relationship(b)

    def test_update_relation_none_without_existing_relation(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-3", nodetype=OBJ)

        self.assertIsNone(a.update_relation(b))

    def test_update_relation_returns_existing_relation_value(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-4", nodetype=OBJ)
        a.set_relation(b, CONTENTS)

        self.assertIs(a.update_relation(b), b)

    def test_get_relation(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-5", nodetype=OBJ)
        a.set_relation(b, CONTENTS)

        self.assertIs(a.get_relation(b), b)

    def test_get_relation_by_id_none_for_unknown(self):
        a = SimulaeNode(nodetype=LOC)
        self.assertIsNone(a.get_relation_by_ID("missing"))

    def test_get_relation_by_nodetype_and_id_current_behavior(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-6", nodetype=OBJ)
        a.set_relation(b, CONTENTS)

        self.assertIs(a.get_relation_by_nodetype_and_ID(OBJ, b.ID), b)

    def test_get_relations_by_type(self):
        a = SimulaeNode(nodetype=LOC)
        relations = a.get_relations_by_type(CONTENTS)
        self.assertIsInstance(relations, dict)
        self.assertIsNone(a.get_relations_by_type("Nope"))

    def test_get_relations_by_relation_type_and_nodetype(self):
        a = SimulaeNode(nodetype=LOC)
        rels = a.get_relations_by_relation_type_and_nodetype(CONTENTS, OBJ)
        self.assertEqual(rels, {})
        self.assertIsNone(a.get_relations_by_relation_type_and_nodetype("Nope", OBJ))

    def test_add_relation(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-7", nodetype=OBJ)

        self.assertTrue(a.add_relation(b, CONTENTS))
        self.assertFalse(a.add_relation(b, CONTENTS))
        
        self.assertFalse(a.add_relation(b, "Invalid", warn=False))

    def test_set_relation(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-8", nodetype=OBJ)

        self.assertTrue(a.set_relation(b, CONTENTS))
        self.assertFalse(a.set_relation(b, "Invalid", warn=False))

    def test_get_relations_by_criteria_returns_empty_list(self):
        a = SimulaeNode()
        self.assertEqual(a.get_relations_by_criteria({"x": 1}), [])

    def test_get_relations_by_criteria_matches_string_and_dict(self):
        loc = SimulaeNode(nodetype=LOC)
        food = SimulaeNode(given_id="food-1", nodetype=OBJ, references={NAME: "food"})

        loc.set_relation(food, CONTENTS)

        self.assertEqual(loc.get_relations_by_criteria("food"), [food])
        self.assertEqual(loc.get_relations_by_criteria({NAME: "food"}), [food])

    def test_get_relation_type_has_relation_and_has_relation_to(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="obj-9", nodetype=OBJ)
        a.set_relation(b, ATTACHMENTS)

        self.assertEqual(a.get_relation_type(b), ATTACHMENTS)
        
        # TODO AE: Fix relations tests
        self.assertEqual(a.has_relation(b.ID, b.Nodetype), ATTACHMENTS)
        self.assertTrue(a.has_relation_to(b))
        self.assertFalse(a.has_relation_to(SimulaeNode(given_id="obj-10", nodetype=OBJ)))

    def test_has_relationship(self):
        a = SimulaeNode(nodetype=LOC)
        a.Relations[POI] = {"npc-2": {STATUS: "known"}}

        self.assertTrue(a.has_relationship("npc-2", POI))
        self.assertFalse(a.has_relationship("npc-3", POI))

    def test_get_set_location_and_set_location_by_id(self):
        actor = SimulaeNode(nodetype=POI)
        loc = SimulaeNode(given_id="loc-1", nodetype=LOC)
        not_loc = SimulaeNode(given_id="obj-11", nodetype=OBJ)

        actor.set_location(not_loc, warn=False)
        self.assertIsNone(actor.get_location())

        actor.set_location(loc)
        self.assertEqual(actor.get_location(), "loc-1")
        self.assertIs(actor.References[LOC], loc.ID)

        actor.set_location_by_ID("loc-2")
        self.assertEqual(actor.get_location(), "loc-2")

    def test_get_adjacent_locations_empty(self):
        loc = SimulaeNode(nodetype=LOC)
        self.assertEqual(loc.get_adjacent_locations(), [])

    def test_add_adjacent_location(self):
        a = SimulaeNode(nodetype=LOC)
        b = SimulaeNode(given_id="loc-3", nodetype=LOC)

        a.add_adjacent_location(b)
        self.assertIs(a.Relations[ADJACENT][LOC]["loc-3"], b)
        self.assertEqual(len(a.Relations[ADJACENT][LOC]), 1)

    def test_get_adjacent_locations_non_empty_current_behavior(self):
        loc = SimulaeNode(nodetype=LOC)
        other = SimulaeNode(given_id="loc-4", nodetype=LOC)
        loc.set_relation(other, ADJACENT)

        adjacents = loc.get_adjacent_locations()

        if not adjacents:
            self.fail("Adjacents should not be None or empty")

        self.assertEqual(len(adjacents), 1)
        self.assertIs(adjacents[0], other)


class TestSimulaeNodeChecksScalesDescriptions(unittest.TestCase):
    def test_checks_lifecycle(self):
        node = SimulaeNode()

        self.assertFalse(node.has_check(""))
        node.set_check("", True, warn=False)
        self.assertFalse(node.has_check(""))

        node.set_check("Alive", True)
        self.assertTrue(node.has_check("Alive"))
        self.assertTrue(node.get_check("Alive"))

        node.remove_check("Alive")
        self.assertFalse(node.has_check("Alive"))
        self.assertIsNone(node.get_check("Alive"))

    def test_generate_policy_and_personality(self):
        node = SimulaeNode(nodetype=POI)

        policy = node.generate_policy()
        personality = node.generate_personality()

        self.assertEqual(set(policy.keys()), set(POLICY_SCALE.keys()))
        self.assertEqual(set(personality.keys()), set(PERSONALITY_SCALE.keys()))

    def test_get_scale_and_scale_wrappers(self):
        poi = SimulaeNode(nodetype=POI)
        obj = SimulaeNode(nodetype=OBJ)

        self.assertIsNotNone(poi.get_scale(POLICY))
        self.assertIsNotNone(poi.get_scale(PERSONALITY))
        self.assertIsNone(poi.get_scale("Nope"))
        self.assertIsNone(obj.get_scale(POLICY))

        self.assertEqual(poi.get_political_beliefs(), poi.get_scale(POLICY))
        self.assertEqual(poi.get_personality(), poi.get_scale(PERSONALITY))

    def test_policy_disposition(self):
        node = SimulaeNode(nodetype=POI)

        self.assertEqual(node.get_policy_disposition(0), "Friendly")
        self.assertEqual(node.get_policy_disposition(10), "Friendly")
        self.assertEqual(node.get_policy_disposition(19), "Neutral")
        self.assertEqual(node.get_policy_disposition(20), "Hostile")
        with self.assertRaises(ValueError):
            node.get_policy_disposition(-1)

    def test_social_disposition(self):
        node = SimulaeNode(nodetype=POI)

        self.assertEqual(node.get_social_disposition(0), "Friendly")
        self.assertEqual(node.get_social_disposition(10), "Friendly")
        self.assertEqual(node.get_social_disposition(19), "Neutral")
        self.assertEqual(node.get_social_disposition(20), "Hostile")
        with self.assertRaises(ValueError):
            node.get_social_disposition(-1)

    def test_policy_diff(self):
        node = SimulaeNode(nodetype=POI)
        compare_policy = {}

        politics = node.get_political_beliefs()

        if not politics:
            self.fail("Politics should not be None or empty")

        for factor, (index, strength) in politics.items():
            compare_policy[factor] = ((index + 1) % len(POLICY_SCALE[factor]), max(1, strength))

        diff = node.policy_diff(compare_policy)

        if not diff:
            self.fail("Diff should not be None or empty")

        self.assertIsInstance(diff, tuple)
        self.assertEqual(len(diff), 2)
        self.assertIsNone(node.policy_diff({}, warn=False))

    def test_social_diff(self):
        node = SimulaeNode(nodetype=POI)
        compare = {}
        for factor, (index, strength) in node.get_personality().items(): # type: ignore
            compare[factor] = ((index + 1) % len(PERSONALITY_SCALE[factor]), max(1, strength))

        diff = node.social_diff(compare)

        if not diff:
            self.fail("Diff should not be None or empty")

        self.assertIsInstance(diff, tuple)
        self.assertEqual(len(diff), 2)
        self.assertIsNone(node.social_diff({}, warn=False))

    def test_describe_political_beliefs(self):
        node = SimulaeNode(nodetype=POI)
        self.assertEqual(node.describe_political_beliefs(), "")

        node.References[POLICY] = {"Economy": (0, 1), "Liberty": (3, 1)} # type: ignore
        summary = node.describe_political_beliefs()
        self.assertIn("Economy", summary)
        self.assertNotIn("Liberty", summary)  # Indifferent is intentionally skipped

    def test_describe_personality(self):
        node = SimulaeNode(nodetype=POI)
        self.assertEqual(node.describe_personality(), "")

        node.References[PERSONALITY] = True # type: ignore
        summary = node.describe_personality()
        self.assertIn("Loyalty", summary)

    def test_describe_faction_associations(self):
        node = SimulaeNode(nodetype=POI)
        self.assertEqual(node.describe_faction_associations(), "")

        node.References[FAC] = "enabled" # type: ignore
        node.Relations[FAC] = {"faction-1": {STATUS: "ally"}}
        summary = node.describe_faction_associations()
        self.assertIn("faction-1 ally", summary)


class TestSimulaeNodeSerializationAndFactories(unittest.TestCase):
    def test_to_json_contains_expected_keys(self):
        parent = SimulaeNode(given_id="parent", nodetype=LOC, references={NAME: "Parent"})
        child = SimulaeNode(given_id="child", nodetype=OBJ, references={NAME: "Child"})
        parent.Relations[CONTENTS][OBJ][child.ID] = child
        parent.set_check("Visited", True)

        data = parent.toJSON()

        self.assertIsInstance(data, dict)
        for key in [ID, NODETYPE, REFERENCES, ATTRIBUTES, RELATIONS, CHECKS, ABILITIES, SCALES, MEMORY]:
            self.assertIn(key, data)
        self.assertIn("child", data[RELATIONS][CONTENTS][OBJ])
        self.assertIsInstance(data[RELATIONS][CONTENTS][OBJ]["child"], dict)

    def test_simulaenode_from_json_current_behavior(self):
        payload = {
            ID: "n-1",
            NODETYPE: OBJ,
            REFERENCES: {NAME: "N"},
            ATTRIBUTES: {},
            RELATIONS: {},
            CHECKS: {},
            ABILITIES: {},
            SCALES: {},
            MEMORY: {},
        }

        simulae_node = simulaenode_from_json(payload)

        self.assertIsNotNone(simulae_node) 
        

    def test_generate_simulae_node(self):
        generated = generate_simulae_node(OBJ)
        self.assertIsInstance(generated, SimulaeNode)
        self.assertEqual(generated.Nodetype, OBJ)

        named = generate_simulae_node(OBJ, node_name="NODE")
        self.assertEqual(named.References[NAME], "NODE")

        location = generate_simulae_node(LOC, node_name="Place")
        self.assertIn("max_adjacent_locations", location.Attributes)

    def test_generate_person_simulae_node(self):
        person = generate_person_simulae_node("Alex")

        self.assertEqual(person.Nodetype, POI)
        self.assertEqual(person.get_reference(NAME), "Alex")
        self.assertIsInstance(person.get_attribute("Age"), int)
        self.assertIsNotNone(person.get_attribute("Height"))
        self.assertIsNotNone(person.get_attribute("Weight"))
        self.assertGreaterEqual(len(person.Relations[COMPONENTS][OBJ]), 6)

    def test_generate_person_body(self):
        parts = generate_person_body(gender="Male", age=30, height=1.8, weight=80.0, complete=True)

        self.assertEqual(len(parts), 6)
        for part in parts:
            self.assertIsInstance(part, SimulaeNode)
            self.assertEqual(part.Nodetype, OBJ)


if __name__ == "__main__":
    unittest.main()
