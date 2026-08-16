import unittest

from NGIN.ai.lib.socialization_constants import SOCIAL_INTERACTION_QUALIFIERS, SOCIAL_INTERACTION_TYPES
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.ai.lib import *

class Test_NGIN_AI_Planning(unittest.TestCase):

    def setUp(self):
        self.actor = SimulaeActor(generate_person())

        # give actor medicine
        #self.actor.Relations[CONTENTS]['medicine'] = SimulaeNode(given_id='medicine', nodetype=OBJ)

    def _require_action_result(self, result: object | None) -> tuple[object, object]:
        """Force an optional action result into a concrete two-item tuple."""

        self.assertIsNotNone(result)
        assert isinstance(result, (tuple, list))
        self.assertGreaterEqual(len(result), 2)
        return result[0], result[1]

    def _require_node(self, node: object | None) -> SimulaeNode:
        """Force an optional node-like value into a concrete SimulaeNode."""

        self.assertIsNotNone(node)
        assert isinstance(node, SimulaeNode)
        return node

    def _require_number(self, value: object | None) -> int | float:
        """Force an optional numeric value into a concrete number."""

        self.assertIsNotNone(value)
        assert isinstance(value, (int, float))
        return value

    def _require_text(self, value: object | None) -> str:
        """Force an optional string value into a concrete string."""

        self.assertIsNotNone(value)
        assert isinstance(value, str)
        return value

    def _require_recipe_definition(self, recipe: object | None) -> dict[str, object]:
        """Force an optional recipe lookup into a concrete dictionary."""

        self.assertIsNotNone(recipe)
        assert isinstance(recipe, dict)
        return recipe

    def _build_linear_world(self):
        """Create a tiny three-node map for travel and search tests."""

        world = SimulaeNode(given_id="world", nodetype="state")

        loc_a = SimulaeNode(given_id="loc-a", nodetype=LOC, references={NAME: "camp start"})
        loc_b = SimulaeNode(given_id="loc-b", nodetype=LOC, references={NAME: "trail"})
        loc_c = SimulaeNode(given_id="loc-c", nodetype=LOC, references={NAME: "camp"})

        # Link the locations into a simple chain so BFS pathfinding has a
        # deterministic route to discover.
        loc_a.add_adjacent_location(loc_b)
        loc_b.add_adjacent_location(loc_c)

        world.set_relation(loc_a, CONTENTS)
        world.set_relation(loc_b, CONTENTS)
        world.set_relation(loc_c, CONTENTS)

        return world, loc_a, loc_b, loc_c

    def _build_linear_world_with_item(self):
        """Create a tiny map plus a nearby object for search/acquire tests."""

        world, loc_a, loc_b, loc_c = self._build_linear_world()

        lantern = SimulaeNode(
            given_id="lantern-1",
            nodetype=OBJ,
            references={NAME: "lantern"},
            attributes={"brightness": 2},
        )

        loc_b.set_relation(lantern, CONTENTS)
        lantern.set_location_by_ID(loc_b.ID)

        return world, loc_a, loc_b, loc_c, lantern

    def test_initial_attributes(self):
        self.assertIsNotNone(self.actor)
        self.assertEqual(self.actor.priorities, [])

    def test_NGIN_AI_plan_empty(self):
        self.actor.plan()
        self.assertEqual(self.actor.priorities, [])

    def test_NGIN_AI_plan_populated(self):
        # Give the actor a concrete hunger target so the planner has something
        # real to reason about and the executor can make visible progress.
        self.actor.set_attribute(HUNGER, 90)
        food = generate_food_item()
        self.actor.set_relation(food, CONTENTS)

        self.actor.prioritize()

        logAll("Priorities: ",self.actor.priorities)

        self.actor.plan()

        self.assertIn(HUNGER, self.actor.plans)

        hunger_plan = self.actor.plans[HUNGER]
        self.assertIsInstance(hunger_plan, TaskPlan)
        self.assertEqual(hunger_plan.action, SimulaeAction.USE)
        self.assertGreaterEqual(len(hunger_plan.all_actions()), 1)

        before_hunger = self._require_number(self.actor.get_attribute(HUNGER))
        completed_action = self.actor.act_next()

        after_hunger = self._require_number(self.actor.get_attribute(HUNGER))

        self.assertIsNotNone(completed_action)
        self.assertLess(after_hunger, before_hunger)
    
        self.assertEqual(
            self.actor.get_relations_by_criteria("food", relation_types=(CONTENTS, ATTACHMENTS)),
            [],
        )

    def test_TaskPlan_next_action_sequence(self):
        """A plan should expose its steps in execution order."""

        plan = TaskPlan(
            "food",
            SimulaeAction.USE,
            pre_actions=[SimulaeAction.SEARCH, (SimulaeAction.TAKE, "food")],
            post_actions=[(SimulaeAction.INTERACT, "friend")],
        )

        self.assertEqual(plan.next_action(), (SimulaeAction.SEARCH, "food"))
        self.assertEqual(plan.next_action(), (SimulaeAction.TAKE, "food"))
        self.assertEqual(plan.next_action(), (SimulaeAction.USE, "food"))
        self.assertEqual(plan.next_action(), (SimulaeAction.INTERACT, "friend"))
        self.assertIsNone(plan.next_action())

    def test_world_state_search_and_goto_resolve_real_locations(self):
        """SEARCH and GOTO should use the attached world graph."""

        world, loc_a, loc_b, loc_c = self._build_linear_world()

        self.actor.attach_world_state(world)
        self.actor.set_location(loc_a)

        resolved_camp = self._require_node(self.actor.resolve_world_node("camp", nodetype=LOC))
        self.assertIs(resolved_camp, loc_c)

        search_plan = TaskPlan("camp", SimulaeAction.SEARCH)
        search_action, search_target = self._require_action_result(self.actor.act(search_plan))

        self.assertEqual(search_action, SimulaeAction.SEARCH)
        self.assertEqual(self._require_text(search_target), "camp")
        self.assertIn(LOC, self.actor.Memory)
        self.assertIn(loc_c.ID, self.actor.Memory[LOC])

        route = self.actor.pathfind_to(loc_c)
        self.assertEqual(len(route), 2)
        self.assertEqual(route[0], (SimulaeAction.GOTO, loc_b))
        self.assertEqual(route[1], (SimulaeAction.GOTO, loc_c))
        self.assertEqual(self.actor.get_world_distance_to(loc_c), 3)
        self.assertEqual(self.actor.pathfind_to(loc_a), [])
        self.assertEqual(distance_between(self.actor, loc_c), 3)

        goto_plan = TaskPlan("camp", SimulaeAction.GOTO)
        goto_action, goto_target = self._require_action_result(self.actor.act(goto_plan))

        self.assertEqual(goto_action, SimulaeAction.GOTO)
        self.assertEqual(self._require_node(goto_target).ID, loc_c.ID)
        self.assertEqual(self.actor.get_location(), loc_c.ID)

    def test_world_index_and_search_helpers_cover_exact_and_loose_matching(self):
        """World indexing should support direct lookups, templates, and nearby search."""

        world, loc_a, loc_b, loc_c, lantern = self._build_linear_world_with_item()

        self.actor.attach_world_state(world)
        self.actor.set_location(loc_a)

        self.assertIs(self.actor.world_index[loc_a.ID], loc_a)
        self.assertIs(self.actor.world_index[lantern.ID], lantern)
        self.assertIn(loc_b.ID, self.actor.world_location_graph[loc_a.ID])
        self.assertIn(loc_c.ID, self.actor.world_location_graph[loc_b.ID])

        nearby_lanterns = get_targets_nearby_node(self.actor, "lantern", world_state=world)
        self.assertEqual([node.ID for node in nearby_lanterns], [lantern.ID])

        nearby_trail = get_targets_nearby_node(self.actor, "trail", world_state=world)
        self.assertEqual([node.ID for node in nearby_trail], [loc_b.ID])

        self.assertEqual(self.actor.find_world_nodes({NAME: "camp"}, only_locations=True), [loc_c])
        resolved_camp = self._require_node(
            self.actor.resolve_world_node(SimulaeNode(given_id="template", nodetype=LOC, references={NAME: "camp"}), nodetype=LOC)
        )
        self.assertIs(resolved_camp, loc_c)
        current_location = self._require_node(self.actor.get_current_location_node())
        self.assertIs(current_location, loc_a)

        search_plan = TaskPlan("lantern", SimulaeAction.SEARCH)
        search_action, search_target = self._require_action_result(self.actor.act(search_plan))
        self.assertEqual(search_action, SimulaeAction.SEARCH)
        self.assertEqual(self._require_text(search_target), "lantern")
        self.assertIn(OBJ, self.actor.Memory)
        self.assertIn(lantern.ID, self.actor.Memory[OBJ])
        self.assertEqual(self.actor.get_relations_by_criteria("lantern", relation_types=(CONTENTS, ATTACHMENTS)), [])

        acquire_route = self.actor.acquire_vague_target("lantern")
        self.assertEqual(acquire_route, [(SimulaeAction.GOTO, loc_b), (SimulaeAction.TAKE, lantern)])

        acquired = self.actor.acquire("lantern")
        self.assertEqual(acquired, acquire_route)

    def test_crafting_recipe_and_consumable_use(self):
        """Crafting should consume ingredients and the crafted item should work."""

        meat = SimulaeNode(given_id="meat-1", nodetype=OBJ, references={NAME: "meat"})
        water = SimulaeNode(given_id="water-1", nodetype=OBJ, references={NAME: "water"})
        herbs = SimulaeNode(given_id="herbs-1", nodetype=OBJ, references={NAME: "herbs"})

        self.actor.set_relation(meat, CONTENTS)
        self.actor.set_relation(water, CONTENTS)
        self.actor.set_relation(herbs, CONTENTS)

        food_target = SimulaeNode(given_id="food", nodetype=OBJ, references={NAME: "food"})

        self.assertTrue(self.actor.can_make(food_target))
        recipe_workstation, recipe_components = self.actor.get_recipe(food_target)
        self.assertIsNone(recipe_workstation)
        self.assertEqual(recipe_components, ["meat", "water", "herbs"])
        self.assertEqual(self.actor.acquire(food_target), [(SimulaeAction.MAKE, food_target)])

        make_action, make_target = self._require_action_result(self.actor.act(TaskPlan(food_target, SimulaeAction.MAKE)))

        self.assertEqual(make_action, SimulaeAction.MAKE)
        crafted_food = self._require_node(make_target)
        self.assertEqual(self._require_text(crafted_food.get_reference(NAME)), "food")
        self.assertEqual(
            len(self.actor.get_relations_by_criteria("food", relation_types=(CONTENTS, ATTACHMENTS))),
            1,
        )
        self.assertEqual(self.actor.get_relations_by_criteria("meat", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("water", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("herbs", relation_types=(CONTENTS, ATTACHMENTS)), [])

        self.actor.set_attribute(HUNGER, 90)
        self.actor.set_attribute(THIRST, 80)

        use_action, use_target = self._require_action_result(self.actor.act(TaskPlan(food_target, SimulaeAction.USE)))

        self.assertEqual(use_action, SimulaeAction.USE)
        self._require_node(use_target)
        self.assertLess(self._require_number(self.actor.get_attribute(HUNGER)), 90)
        self.assertLess(self._require_number(self.actor.get_attribute(THIRST)), 80)
        self.assertEqual(self.actor.get_relations_by_criteria("food", relation_types=(CONTENTS, ATTACHMENTS)), [])

    def test_make_supports_attachment_and_location_placements(self):
        """Crafting should respect recipe placement for wearable and deployable items."""

        world, loc_a, _, _ = self._build_linear_world()
        self.actor.attach_world_state(world)
        self.actor.set_location(loc_a)

        cloth_1 = SimulaeNode(given_id="cloth-1", nodetype=OBJ, references={NAME: "cloth"})
        wool = SimulaeNode(given_id="wool-1", nodetype=OBJ, references={NAME: "wool"})

        self.actor.set_relation(cloth_1, CONTENTS)
        self.actor.set_relation(wool, CONTENTS)

        blanket_target = SimulaeNode(given_id="blanket", nodetype=OBJ, references={NAME: "blanket"})
        bed_target = SimulaeNode(given_id="bed", nodetype=OBJ, references={NAME: "bed"})

        self.assertEqual(
            self._require_text(self._require_recipe_definition(self.actor.get_recipe_definition("meal"))["recipe_name"]),
            "stew",
        )
        self.assertEqual(
            self._require_text(self._require_recipe_definition(self.actor.get_recipe_definition("first aid"))["recipe_name"]),
            "bandage",
        )
        self.assertEqual(
            self._require_text(self._require_recipe_definition(self.actor.get_recipe_definition("cover"))["recipe_name"]),
            "blanket",
        )
        self.assertEqual(
            self._require_text(self._require_recipe_definition(self.actor.get_recipe_definition("sleep"))["recipe_name"]),
            "bed",
        )
        self.assertIsNone(self.actor.get_recipe_definition("unknown recipe"))
        self.assertFalse(self.actor.can_make("unknown recipe"))
        self.assertTrue(self.actor.can_make("meal"))

        blanket_action, blanket_target_item = self._require_action_result(self.actor.act(TaskPlan(blanket_target, SimulaeAction.MAKE)))
        self.assertEqual(blanket_action, SimulaeAction.MAKE)
        crafted_blanket = self._require_node(blanket_target_item)
        self.assertEqual(self._require_text(crafted_blanket.get_reference(NAME)), "blanket")
        self.assertEqual(self._require_text(crafted_blanket.get_reference("Placement")), "attachments")
        self.assertEqual(self.actor.get_relations_by_criteria("blanket", relation_types=(ATTACHMENTS,)), [crafted_blanket])
        self.assertEqual(self.actor.get_relations_by_criteria("cloth", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("wool", relation_types=(CONTENTS, ATTACHMENTS)), [])

        wood = SimulaeNode(given_id="wood-1", nodetype=OBJ, references={NAME: "wood"})
        cloth_2 = SimulaeNode(given_id="cloth-2", nodetype=OBJ, references={NAME: "cloth"})
        straw = SimulaeNode(given_id="straw-1", nodetype=OBJ, references={NAME: "straw"})

        self.actor.set_relation(wood, CONTENTS)
        self.actor.set_relation(cloth_2, CONTENTS)
        self.actor.set_relation(straw, CONTENTS)

        bed_action, bed_target_item = self._require_action_result(self.actor.act(TaskPlan(bed_target, SimulaeAction.MAKE)))
        self.assertEqual(bed_action, SimulaeAction.MAKE)
        crafted_bed = self._require_node(bed_target_item)
        self.assertEqual(self._require_text(crafted_bed.get_reference(NAME)), "bed")
        self.assertEqual(self._require_text(crafted_bed.get_reference("Placement")), "location")
        current_location = self._require_node(self.actor.get_current_location_node())
        self.assertEqual(current_location.get_relations_by_criteria("bed"), [crafted_bed])
        self.assertEqual(self.actor.get_relations_by_criteria("wood", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("cloth", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("straw", relation_types=(CONTENTS, ATTACHMENTS)), [])

    def test_apply_item_use_effects_handles_survival_effects(self):
        """The private item-effect helper should update the expected status fields."""

        self.actor.set_attribute(HUNGER, 70)
        self.actor.set_attribute(THIRST, 65)
        self.actor.set_attribute(SICK, 40)
        self.actor.set_attribute(EXHAUSTION, 60)
        self.actor.set_attribute(TEMPERATURE, 20)
        self.actor.set_attribute(LONELINESS, 12)

        hearty_food = SimulaeNode(
            given_id="stew-1",
            nodetype=OBJ,
            references={NAME: "food"},
            attributes={"nutrition": 14, "hydration": 8, "warmth": 5, "comfort": 3},
            checks={"edible": True, "drinkable": True, "consumable": True},
        )

        effects = self.actor._apply_item_use_effects(hearty_food)

        self.assertEqual(effects[HUNGER], 56)
        self.assertEqual(effects[THIRST], 57)
        self.assertEqual(effects[TEMPERATURE], 25)
        self.assertEqual(effects[LONELINESS], 9)

        self.actor.set_attribute(SICK, 40)
        self.actor.set_attribute(EXHAUSTION, 60)

        medicine = SimulaeNode(
            given_id="medicine-1",
            nodetype=OBJ,
            references={NAME: "medicine"},
            attributes={"healing": 12},
            checks={"consumable": True},
        )

        medicine_effects = self.actor._apply_item_use_effects(medicine)

        self.assertEqual(medicine_effects[SICK], 28)
        self.assertEqual(medicine_effects[EXHAUSTION], 57)

    def test_use_moves_wearable_and_deployable_items(self):
        """Wearable items should attach and deployable items should land in the world."""

        world, loc_a, _, _ = self._build_linear_world()

        self.actor.attach_world_state(world)
        self.actor.set_location(loc_a)
        self.actor.set_attribute(TEMPERATURE, 25)
        self.actor.set_attribute(EXHAUSTION, 90)

        blanket = SimulaeNode(
            given_id="blanket-1",
            nodetype=OBJ,
            references={NAME: "blanket"},
            attributes={"warmth": 12},
            checks={"wearable": True},
        )
        bed = SimulaeNode(
            given_id="bed-1",
            nodetype=OBJ,
            references={NAME: "bed"},
            attributes={"restfulness": 20},
            checks={"deployable": True},
        )

        self.actor.set_relation(blanket, CONTENTS)
        self.actor.set_relation(bed, CONTENTS)

        blanket_action, blanket_target_item = self._require_action_result(self.actor.act(TaskPlan(blanket, SimulaeAction.USE)))
        self.assertEqual(blanket_action, SimulaeAction.USE)
        self._require_node(blanket_target_item)
        self.assertEqual(self.actor.get_relations_by_criteria("blanket", relation_types=(ATTACHMENTS,)), [blanket])
        self.assertEqual(self.actor.get_relations_by_criteria("blanket", relation_types=(CONTENTS,)), [])
        self.assertGreater(self._require_number(self.actor.get_attribute(TEMPERATURE)), 25)

        bed_action, bed_target_item = self._require_action_result(self.actor.act(TaskPlan(bed, SimulaeAction.USE)))
        self.assertEqual(bed_action, SimulaeAction.USE)
        self._require_node(bed_target_item)
        self.assertEqual(self.actor.get_relations_by_criteria("bed", relation_types=(CONTENTS, ATTACHMENTS)), [])

        current_location = self._require_node(self.actor.get_current_location_node())
        self.assertEqual(current_location.get_relations_by_criteria("bed"), [bed])
        self.assertLess(self._require_number(self.actor.get_attribute(EXHAUSTION)), 90)

class Test_NGIN_AI_Socialize(unittest.TestCase):

    def setUp(self):
        self.actor = SimulaeActor(generate_person())
        self.actor_partner = SimulaeActor(generate_person())

    def test_NGIN_AI_socialize_clone(self):
        # no initial relationship
        self.assertFalse(self.actor.has_relation(self.actor_partner.ID, self.actor_partner.Nodetype))

        # calculate relationship
        relationship = self.actor.determine_relationship(self.actor_partner, interaction=None)

        if relationship is None:
            self.fail("Relationship should not be None")

        self.assertIsNotNone(relationship)
        assert relationship is not None
        self.assertEqual(relationship[NODETYPE], POI)
        self.assertEqual(relationship[INTERACTIONS], [])
        self.assertEqual(relationship[STATUS], 'new')

    def test_NGIN_AI_appraise_social_event(self):
        # create a social event
        social_event = {
            'eventtype': 'greet',
            'qualifiers': { qualifier: factors[0] for qualifier, factors in SOCIAL_INTERACTION_QUALIFIERS.items() }
        }
        
        # iterate through ALL social event types and validate appraisal
        for social_event_type in SOCIAL_INTERACTION_TYPES:
    
            social_event['eventtype'] = social_event_type
            # also update qualifiers        

            # appraise the social event
            appraisal = self.actor.appraise_social_event(social_event)

            if appraisal is None:
                self.fail("Appraisal should not be None")

            self.assertIsNotNone(appraisal)
            assert appraisal is not None

            # Todo AE: add additional assertions


    def test_NGIN_AI_select_response(self):
        # create a social event
       

        pass


def actor_tick_test(actor: SimulaeNode):
    # increment all status attributes    
    for attr in actor.Attributes:
        if attr in STATUS_ATTRIBUTES:
            attribute_value = actor.get_attribute(attr)

            if attribute_value is None:
                attribute_value = 0

            actor.set_attribute(attr, attribute_value + 1)

if __name__ == '__main__':
    unittest.main()
