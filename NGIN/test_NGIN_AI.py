import unittest

from NGIN.NGIN_Socialization import RESPONSE_WEIGHTS, SOCIAL_INTERACTION_QUALIFIERS, SOCIAL_INTERACTION_TYPES
from .NGIN_AI import *

class Test_NGIN_AI_Planning(unittest.TestCase):

    def setUp(self):
        self.actor = NGIN_Simulae_Actor(generate_person())

        # give actor medicine
        #self.actor.Relations[CONTENTS]['medicine'] = SimulaeNode(given_id='medicine', nodetype=OBJ)

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
        self.assertEqual(hunger_plan.action, Action.USE)
        self.assertGreaterEqual(len(hunger_plan.all_actions()), 1)

        before_hunger = self.actor.get_attribute(HUNGER)
        completed_action = self.actor.act_next()

        after_hunger = self.actor.get_attribute(HUNGER)

        self.assertIsNotNone(completed_action)
        self.assertIsNotNone(before_hunger)
        self.assertIsNotNone(after_hunger)
        
        if before_hunger and after_hunger: # for linter
           self.assertTrue((after_hunger < before_hunger))
    
        self.assertEqual(
            self.actor.get_relations_by_criteria("food", relation_types=(CONTENTS, ATTACHMENTS)),
            [],
        )

    def test_TaskPlan_next_action_sequence(self):
        """A plan should expose its steps in execution order."""

        plan = TaskPlan(
            "food",
            Action.USE,
            pre_actions=[Action.SEARCH, (Action.TAKE, "food")],
            post_actions=[(Action.INTERACT, "friend")],
        )

        self.assertEqual(plan.next_action(), (Action.SEARCH, "food"))
        self.assertEqual(plan.next_action(), (Action.TAKE, "food"))
        self.assertEqual(plan.next_action(), (Action.USE, "food"))
        self.assertEqual(plan.next_action(), (Action.INTERACT, "friend"))
        self.assertIsNone(plan.next_action())

    def test_world_state_search_and_goto_resolve_real_locations(self):
        """SEARCH and GOTO should use the attached world graph."""

        world, loc_a, loc_b, loc_c = self._build_linear_world()

        self.actor.attach_world_state(world)
        self.actor.set_location(loc_a)

        self.assertIs(self.actor.resolve_world_node("camp", nodetype=LOC), loc_c)

        search_plan = TaskPlan("camp", Action.SEARCH)
        search_result = self.actor.act(search_plan)

        self.assertEqual(search_result, (Action.SEARCH, "camp"))
        self.assertIn(LOC, self.actor.Memory)
        self.assertIn(loc_c.ID, self.actor.Memory[LOC])

        route = self.actor.pathfind_to(loc_c)
        self.assertEqual(len(route), 2)
        self.assertEqual(route[0], (Action.GOTO, loc_b))
        self.assertEqual(route[1], (Action.GOTO, loc_c))
        self.assertEqual(self.actor.get_world_distance_to(loc_c), 3)
        self.assertEqual(self.actor.pathfind_to(loc_a), [])
        self.assertEqual(distance_between(self.actor, loc_c), 3)

        goto_plan = TaskPlan("camp", Action.GOTO)
        goto_result = self.actor.act(goto_plan)

        self.assertEqual(goto_result[0], Action.GOTO)
        self.assertEqual(goto_result[1].ID, loc_c.ID)
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
        self.assertIs(self.actor.resolve_world_node(SimulaeNode(given_id="template", nodetype=LOC, references={NAME: "camp"}), nodetype=LOC), loc_c)
        self.assertIs(self.actor.get_current_location_node(), loc_a)

        search_plan = TaskPlan("lantern", Action.SEARCH)
        search_result = self.actor.act(search_plan)
        self.assertEqual(search_result, (Action.SEARCH, "lantern"))
        self.assertIn(OBJ, self.actor.Memory)
        self.assertIn(lantern.ID, self.actor.Memory[OBJ])
        self.assertEqual(self.actor.get_relations_by_criteria("lantern", relation_types=(CONTENTS, ATTACHMENTS)), [])

        acquire_route = self.actor.acquire_vague_target("lantern")
        self.assertEqual(acquire_route, [(Action.GOTO, loc_b), (Action.TAKE, lantern)])

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
        self.assertEqual(self.actor.get_recipe(food_target), (None, ["meat", "water", "herbs"]))
        self.assertEqual(self.actor.acquire(food_target), [(Action.MAKE, food_target)])

        make_result = self.actor.act(TaskPlan(food_target, Action.MAKE))

        self.assertEqual(make_result[0], Action.MAKE)
        crafted_food = make_result[1]
        self.assertEqual(crafted_food.get_reference(NAME), "food")
        self.assertEqual(
            len(self.actor.get_relations_by_criteria("food", relation_types=(CONTENTS, ATTACHMENTS))),
            1,
        )
        self.assertEqual(self.actor.get_relations_by_criteria("meat", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("water", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("herbs", relation_types=(CONTENTS, ATTACHMENTS)), [])

        self.actor.set_attribute(HUNGER, 90)
        self.actor.set_attribute(THIRST, 80)

        use_result = self.actor.act(TaskPlan(food_target, Action.USE))

        self.assertEqual(use_result[0], Action.USE)
        self.assertLess(self.actor.get_attribute(HUNGER), 90)
        self.assertLess(self.actor.get_attribute(THIRST), 80)
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

        self.assertEqual(self.actor.get_recipe_definition("meal")["recipe_name"], "stew")
        self.assertEqual(self.actor.get_recipe_definition("first aid")["recipe_name"], "bandage")
        self.assertEqual(self.actor.get_recipe_definition("cover")["recipe_name"], "blanket")
        self.assertEqual(self.actor.get_recipe_definition("sleep")["recipe_name"], "bed")
        self.assertIsNone(self.actor.get_recipe_definition("unknown recipe"))
        self.assertFalse(self.actor.can_make("unknown recipe"))
        self.assertTrue(self.actor.can_make("meal"))

        blanket_result = self.actor.act(TaskPlan(blanket_target, Action.MAKE))
        self.assertEqual(blanket_result[0], Action.MAKE)
        self.assertEqual(blanket_result[1].get_reference(NAME), "blanket")
        self.assertEqual(blanket_result[1].get_reference("Placement"), "attachments")
        self.assertEqual(self.actor.get_relations_by_criteria("blanket", relation_types=(ATTACHMENTS,)), [blanket_result[1]])
        self.assertEqual(self.actor.get_relations_by_criteria("cloth", relation_types=(CONTENTS, ATTACHMENTS)), [])
        self.assertEqual(self.actor.get_relations_by_criteria("wool", relation_types=(CONTENTS, ATTACHMENTS)), [])

        wood = SimulaeNode(given_id="wood-1", nodetype=OBJ, references={NAME: "wood"})
        cloth_2 = SimulaeNode(given_id="cloth-2", nodetype=OBJ, references={NAME: "cloth"})
        straw = SimulaeNode(given_id="straw-1", nodetype=OBJ, references={NAME: "straw"})

        self.actor.set_relation(wood, CONTENTS)
        self.actor.set_relation(cloth_2, CONTENTS)
        self.actor.set_relation(straw, CONTENTS)

        bed_result = self.actor.act(TaskPlan(bed_target, Action.MAKE))
        self.assertEqual(bed_result[0], Action.MAKE)
        self.assertEqual(bed_result[1].get_reference(NAME), "bed")
        self.assertEqual(bed_result[1].get_reference("Placement"), "location")
        current_location = self.actor.get_current_location_node()
        self.assertIsNotNone(current_location)
        self.assertEqual(current_location.get_relations_by_criteria("bed"), [bed_result[1]])
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

        blanket_result = self.actor.act(TaskPlan(blanket, Action.USE))
        self.assertEqual(blanket_result[0], Action.USE)
        self.assertEqual(self.actor.get_relations_by_criteria("blanket", relation_types=(ATTACHMENTS,)), [blanket])
        self.assertEqual(self.actor.get_relations_by_criteria("blanket", relation_types=(CONTENTS,)), [])
        self.assertGreater(self.actor.get_attribute(TEMPERATURE), 25)

        bed_result = self.actor.act(TaskPlan(bed, Action.USE))
        self.assertEqual(bed_result[0], Action.USE)
        self.assertEqual(self.actor.get_relations_by_criteria("bed", relation_types=(CONTENTS, ATTACHMENTS)), [])

        current_location = self.actor.get_current_location_node()
        self.assertIsNotNone(current_location)
        self.assertEqual(current_location.get_relations_by_criteria("bed"), [bed])
        self.assertLess(self.actor.get_attribute(EXHAUSTION), 90)

class Test_NGIN_AI_Socialize(unittest.TestCase):

    def setUp(self):
        self.actor = NGIN_Simulae_Actor(generate_person())
        self.actor_partner = NGIN_Simulae_Actor(generate_person())

    def test_NGIN_AI_socialize_clone(self):
        # no initial relationship
        self.assertFalse(self.actor.has_relation(self.actor_partner.ID, self.actor_partner.Nodetype))

        # calculate relationship
        relationship = self.actor.determine_relationship(self.actor_partner, interaction=None)

        if not relationship:
            self.fail("Relationship should not be None")

        self.assertIsNotNone(relationship)
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

            if not appraisal:
                self.fail("Appraisal should not be None")

            self.assertIsNotNone(appraisal)

            # Todo AE: add additional assertions


    def test_NGIN_AI_select_response(self):
        # create a social event
       

        pass


def actor_tick_test(actor: SimulaeNode):
    # increment all status attributes    
    for attr in actor.Attributes:
        if attr in STATUS_ATTRIBUTES:
            attribute_value = actor.get_attribute(attr)

            if not attribute_value:
                attribute_value = 0

            actor.set_attribute(attr, attribute_value + 1)

if __name__ == '__main__':
    unittest.main()
