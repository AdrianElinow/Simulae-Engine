from collections import deque
from copy import deepcopy
from enum import Enum
from NGIN.ai.lib.ngin_action import SimulaeAction

from NGIN.ai.lib.socialization_constants import SOCIAL_INTERACTION_ALIASES, SOCIAL_INTERACTION_TYPES
from NGIN.implementation.lib.SimulaeNode import *

# Crafting is intentionally small and data-driven for now. The goal is to make
# the planner useful with a few meaningful recipes rather than to cover every
# possible item in the world.

def _normalize_search_key(value):
    """Return a stable case-folded search key for names, IDs, and labels."""

    if value is None:
        return ""

    return normalize_str(str(value)).casefold()


def _normalize_social_key(value):
    """Return a stable lookup key for social-event types and subtypes."""

    if value is None:
        return ""

    # The social notes use mixed punctuation ("greet", "greet!", "sever-ties",
    # etc.) so we collapse separators before comparing labels.
    normalized = normalize_str(str(value)).casefold()
    normalized = normalized.replace("_", " ").replace("-", " ")
    return " ".join(normalized.split())


def _canonical_social_type(value):
    """Map loose social labels to the canonical interaction families."""

    normalized = _normalize_social_key(value)

    if not normalized:
        return None

    if normalized in SOCIAL_INTERACTION_ALIASES:
        return SOCIAL_INTERACTION_ALIASES[normalized]

    for candidate in SOCIAL_INTERACTION_TYPES:
        if _normalize_social_key(candidate) == normalized:
            return candidate

    if _normalize_social_key("summary") == normalized:
        return "Summary"

    return normalize_str(str(value))


def _value_matches(candidate_value, expected_value):
    """Compare two values with the same loose semantics used by node search."""

    if expected_value is None:
        return candidate_value is None

    if isinstance(expected_value, SimulaeNode):
        return (
            isinstance(candidate_value, SimulaeNode)
            and candidate_value.ID == expected_value.ID
            and candidate_value.Nodetype == expected_value.Nodetype
        )

    if isinstance(expected_value, dict):
        if not isinstance(candidate_value, dict):
            return False
        return all(
            _value_matches(candidate_value.get(key), value)
            for key, value in expected_value.items()
        )

    if isinstance(expected_value, (list, tuple, set)):
        return any(_value_matches(candidate_value, value) for value in expected_value)

    return _normalize_search_key(candidate_value) == _normalize_search_key(expected_value)


def _node_matches_criteria(candidate, criteria):
    """Return ``True`` when a node matches a loose string, node, or dict query."""

    if not candidate or criteria is None:
        return False

    if isinstance(criteria, SimulaeNode):
        if criteria.ID and candidate.ID == criteria.ID:
            return True

        if criteria.Nodetype and candidate.Nodetype != criteria.Nodetype:
            return False

        criteria_name = criteria.get_reference(NAME)
        candidate_name = candidate.get_reference(NAME)

        if criteria_name and candidate_name:
            return _normalize_search_key(candidate_name) == _normalize_search_key(criteria_name)

        # A template node with only a nodetype is treated as "any node of this
        # type", which keeps the search helpers useful for planning.
        if not criteria.ID and not criteria_name and criteria.Nodetype:
            return candidate.Nodetype == criteria.Nodetype

        return True

    if isinstance(criteria, str):
        criteria_text = _normalize_search_key(criteria)

        candidate_values = [
            candidate.ID,
            candidate.Nodetype,
            candidate.get_reference(NAME),
        ]
        candidate_values.extend(candidate.References.values())
        candidate_values.extend(candidate.Attributes.values())
        candidate_values.extend(candidate.Checks.keys())
        candidate_values.extend(candidate.Checks.values())
        candidate_values.extend(candidate.Abilities.keys())
        candidate_values.extend(candidate.Abilities.values())

        for candidate_value in candidate_values:
            if candidate_value is None:
                continue
            if _normalize_search_key(candidate_value) == criteria_text:
                return True

        return False

    if isinstance(criteria, dict):
        for key, expected_value in criteria.items():
            if key == ID:
                if not _value_matches(candidate.ID, expected_value):
                    return False
                continue

            if key == NODETYPE:
                if not _value_matches(candidate.Nodetype, expected_value):
                    return False
                continue

            if key == NAME:
                if not _value_matches(candidate.get_reference(NAME), expected_value):
                    return False
                continue

            if key == REFERENCES:
                if not _value_matches(candidate.References, expected_value):
                    return False
                continue

            if key == ATTRIBUTES:
                if not _value_matches(candidate.Attributes, expected_value):
                    return False
                continue

            if key == CHECKS:
                if not _value_matches(candidate.Checks, expected_value):
                    return False
                continue

            if key == ABILITIES:
                if not _value_matches(candidate.Abilities, expected_value):
                    return False
                continue

            if key in candidate.References:
                if not _value_matches(candidate.References.get(key), expected_value):
                    return False
                continue

            if key in candidate.Attributes:
                if not _value_matches(candidate.Attributes.get(key), expected_value):
                    return False
                continue

            if key in candidate.Checks:
                if not _value_matches(candidate.Checks.get(key), expected_value):
                    return False
                continue

            if key in candidate.Abilities:
                if not _value_matches(candidate.Abilities.get(key), expected_value):
                    return False
                continue

            return False

        return True

    return _value_matches(candidate, criteria)


def _normalize_action_step(step, default_target=None):
    """Normalize a loose action entry to `(Action, target)` form.

    The planner currently mixes bare `Action` entries and explicit tuples. This
    helper keeps the execution code simple by making both shapes behave the
    same way.
    """

    if not step:
        return None

    if isinstance(step, (tuple, list)):
        if len(step) == 0:
            return None
        if len(step) == 1:
            return _normalize_action_step(step[0], default_target)
        return step[0], step[1]

    return step, default_target


def get_targets_nearby_node(node, target_criteria, world_state=None, include_adjacent_locations=True):
    '''
    Get list of SimulaeNodes in the same location as ``node`` that match
    ``target_criteria``. When a shared world root is available, adjacent
    locations are also searched so travel plans can discover real map nodes.
    
    :param node: Description
    :param target_criteria: Description
    '''
    
    if not node:
        return []

    world_state = world_state or getattr(node, "world_state", None)
    loc_id = node.get_location() if hasattr(node, "get_location") else None

    location_node = None

    if hasattr(node, 'Nodetype') and node.Nodetype == LOC:
        location_node = node
    elif world_state and loc_id:
        location_node = world_state.get_relation_by_ID(loc_id)
        if location_node and location_node.Nodetype != LOC:
            location_node = None
    else:
        # The actor may or may not have a direct handle to the actual location
        # node. Try the current node first, then fall back to any known relation
        # that looks like the location reference.
        if loc_id and hasattr(node, 'get_relations_by_criteria'):
            location_candidates = node.get_relations_by_criteria(loc_id)
            for candidate in location_candidates:
                if candidate and candidate.Nodetype == LOC and candidate.ID == loc_id:
                    location_node = candidate
                    break

    matches = []
    seen_ids = set()

    def add_candidate(candidate):
        if not candidate or candidate.ID in seen_ids:
            return

        if _node_matches_criteria(candidate, target_criteria):
            seen_ids.add(candidate.ID)
            matches.append(candidate)

    if location_node:
        add_candidate(location_node)

        for candidate in location_node.get_relations_by_criteria(target_criteria):
            add_candidate(candidate)

        if include_adjacent_locations:
            for adjacent in location_node.get_adjacent_locations() or []:
                add_candidate(adjacent)

                for candidate in adjacent.get_relations_by_criteria(target_criteria):
                    add_candidate(candidate)

    return matches


def get_best_heuristic(dataset, action, minimize=True):
    
    optimum_output = None
    best = None

    for item in dataset:
        output = get_heuristic(action(item))

        if optimum_output is None:
            optimum_output = output
            best = item
        elif minimize and output < optimum_output:
            optimum_output = output
            best = item
        elif not minimize and output > optimum_output:
            optimum_output = output
            best = item

    return best

def get_heuristic(actions, actor: SimulaeNode | None = None, target: SimulaeNode | None = None):
    """Score an action chain. Lower scores represent cheaper plans."""

    value = 0

    for action in actions:
        if not action:
            continue

        normalized = _normalize_action_step(action, target)

        if not normalized:
            continue

        act, step_target = normalized

        if act == SimulaeAction.GOTO:
            if actor and step_target:
                logAll('getting distance from ',actor,'to',step_target)
            value += distance_between(actor, step_target)
        elif act == SimulaeAction.TAKE:
            value += 1
        elif act == SimulaeAction.USE:
            value += 1
        elif act == SimulaeAction.MAKE:
            value += 2
        elif act == SimulaeAction.SEARCH:
            value += 2
        elif act == SimulaeAction.INTERACT:
            value += 1
        elif act == SimulaeAction.ACQUIRE:
            value += 2
        else:
            value += 3

    return value


def distance_between(actor: SimulaeNode, target: SimulaeNode):
    '''
    Determine distance between actor and target. If they are adjacent (i.e. share a location), return 1. 
    
    :param actor: Description
    :param target: Description
    '''

    if not actor or not target:
        return 3

    if hasattr(actor, "get_world_distance_to"):
        world_distance = actor.get_world_distance_to(target)
        if world_distance is not None:
            return world_distance

    if isinstance(actor, str) and isinstance(target, str):
        return 1 if normalize_str(actor).casefold() == normalize_str(target).casefold() else 3

    if isinstance(target, str) and hasattr(actor, 'get_location'):
        return 1 if normalize_str(actor.get_location() or "").casefold() == normalize_str(target).casefold() else 3

    if isinstance(actor, str) and hasattr(target, 'get_location'):
        return 1 if normalize_str(target.get_location() or "").casefold() == normalize_str(actor).casefold() else 3

    if nodes_are_adjacent(actor, target):
        return 1
    else:
        return 3 # todo AE: implement LOC search

def nodes_are_adjacent(node1: SimulaeNode, node2: SimulaeNode):
    '''
    True if node1 and node2 are in the same location (i.e. they have a common LOC relation)
    
    :param node1: Description
    :param node2: Description
    '''

    if not node1 or not node2:
        return False

    if isinstance(node1, str) and isinstance(node2, str):
        return normalize_str(node1).casefold() == normalize_str(node2).casefold()

    if isinstance(node1, str) and hasattr(node2, 'get_location'):
        return normalize_str(node2.get_location() or "").casefold() == normalize_str(node1).casefold()

    if isinstance(node2, str) and hasattr(node1, 'get_location'):
        return normalize_str(node1.get_location() or "").casefold() == normalize_str(node2).casefold()

    loc1 = node1.get_location() if hasattr(node1, 'get_location') else None
    loc2 = node2.get_location() if hasattr(node2, 'get_location') else None

    if hasattr(node1, 'Nodetype') and node1.Nodetype == LOC:
        loc1 = node1.ID

    if hasattr(node2, 'Nodetype') and node2.Nodetype == LOC:
        loc2 = node2.ID

    if loc1 and loc2:
        return normalize_str(loc1).casefold() == normalize_str(loc2).casefold()

    if hasattr(node1, 'ID') and hasattr(node2, 'ID'):
        return node1.ID == node2.ID

    if loc1 and hasattr(node2, 'ID'):
        return normalize_str(loc1).casefold() == normalize_str(node2.ID).casefold()

    if loc2 and hasattr(node1, 'ID'):
        return normalize_str(loc2).casefold() == normalize_str(node1.ID).casefold()

    return False



def generate_person(location=None):
        '''
        Test function to generate a person with some default attributes and relations for testing purposes
        
        :param location: Description
        '''

        individual = SimulaeNode(nodetype=POI)

        individual.set_reference(NAME, "individual")

        individual.set_attribute(HUNGER, 0)
        individual.set_attribute(THIRST, 0)
        individual.set_attribute(EXHAUSTION, 0)
        individual.set_attribute(SICK, 0)
        individual.set_attribute(TEMPERATURE, 50)
        individual.set_attribute(LONELINESS, 0)
        individual.set_attribute(EXHAUSTION, 0)

        if location:
            # Give the generated person a real starting location so world-aware
            # search and travel helpers can work immediately in tests.
            individual.set_location(location)
        
        return individual

def generate_food_item():
    '''
    Test function to generate a food item with some default attributes and relations for testing purposes
    '''

    food = SimulaeNode(nodetype=OBJ)

    food.set_reference(NAME, "food")

    food.set_check('edible', True)
    food.set_check('consumable', True)
    food.set_attribute('nutrition', 10)

    return food

def generate_drink_item():
    '''
    Test function to generate a drink item with some default attributes and relations for testing purposes
    '''

    drink = SimulaeNode(nodetype=OBJ)

    drink.set_reference(NAME, "drink")

    drink.set_check('drinkable', True)
    drink.set_check('consumable', True)
    drink.set_attribute('hydration', 10)

    return drink
