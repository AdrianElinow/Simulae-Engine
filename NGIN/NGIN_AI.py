from collections import deque
from enum import Enum
import uuid

from NGIN.NGIN_Socialization import RESPONSE_WEIGHTS
from .SimulaeNode import *

class Action(Enum):
    GOTO = 1
    ACQUIRE = 2
    TAKE = 3
    USE = 4
    MAKE = 5
    SEARCH = 6
    INTERACT = 7


# Crafting is intentionally small and data-driven for now. The goal is to make
# the planner useful with a few meaningful recipes rather than to cover every
# possible item in the world.
CRAFTING_RECIPES = {
    "stew": {
        "aliases": ["food", "meal", "rations"],
        "result_name": "food",
        "components": ["meat", "water", "herbs"],
        "placement": "inventory",
        "result_checks": {
            "edible": True,
            "drinkable": True,
            "consumable": True,
        },
        "result_attributes": {
            "nutrition": 18,
            "hydration": 12,
            "warmth": 4,
        },
    },
    "tea": {
        "aliases": ["drink", "beverage", "refreshment"],
        "result_name": "drink",
        "components": ["water", "herbs"],
        "placement": "inventory",
        "result_checks": {
            "drinkable": True,
            "consumable": True,
        },
        "result_attributes": {
            "hydration": 14,
            "warmth": 3,
        },
    },
    "medicine": {
        "aliases": ["medicine", "remedy", "medication"],
        "result_name": "medicine",
        "components": ["herbs", "water", "alcohol"],
        "placement": "inventory",
        "result_checks": {
            "consumable": True,
        },
        "result_attributes": {
            "healing": 20,
        },
    },
    "bandage": {
        "aliases": ["bandage", "first aid", "first_aid"],
        "result_name": "bandage",
        "components": ["cloth", "alcohol"],
        "placement": "inventory",
        "result_checks": {
            "consumable": True,
        },
        "result_attributes": {
            "healing": 8,
        },
    },
    "blanket": {
        "aliases": ["blanket", "cover", "cloak"],
        "result_name": "blanket",
        "components": ["cloth", "wool"],
        "placement": "attachments",
        "result_checks": {
            "wearable": True,
        },
        "result_attributes": {
            "warmth": 10,
            "comfort": 4,
        },
    },
    "bed": {
        "aliases": ["bed", "sleep", "shelter"],
        "result_name": "bed",
        "components": ["wood", "cloth", "straw"],
        "placement": "location",
        "result_checks": {
            "deployable": True,
        },
        "result_attributes": {
            "restfulness": 20,
            "comfort": 6,
        },
    },
}


def _normalize_search_key(value):
    """Return a stable case-folded search key for names, IDs, and labels."""

    if value is None:
        return ""

    return normalize_str(str(value)).casefold()


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


class TaskPlan():
    """A goal with ordered pre-actions, a primary action, and post-actions."""

    def __init__(self, target, action, pre_actions=None, post_actions=None):
        self.target = target
        self.action = action
        self.pre_actions = list(pre_actions) if pre_actions else []
        self.post_actions = list(post_actions) if post_actions else []

        # Plans can be compared before execution, so we score the full chain
        # when the plan is created.
        self.heuristic = get_heuristic(self.all_actions(), target=target)

    def all_actions(self):
        """Return the remaining plan steps in execution order."""

        all = []
        
        if self.pre_actions:
            all.extend(
                step for step in (
                    _normalize_action_step(action, self.target)
                    for action in self.pre_actions
                )
                if step
            )

        normalized_action = _normalize_action_step(self.action, self.target)
        if normalized_action:
            all.append(normalized_action)

        if self.post_actions:
            all.extend(
                step for step in (
                    _normalize_action_step(action, self.target)
                    for action in self.post_actions
                )
                if step
            )

        return all
    
    def next_action(self):
        """Pop and return the next executable step."""
        
        if self.pre_actions:
            return _normalize_action_step(self.pre_actions.pop(0), self.target)
        
        if self.action:
            action = self.action
            self.action = None
            return _normalize_action_step(action, self.target)

        if self.post_actions:
            return _normalize_action_step(self.post_actions.pop(0), self.target)

        return None

    def is_complete(self):
        """True when the plan has no remaining work."""

        return not self.pre_actions and self.action is None and not self.post_actions

    def _describe_step(self, step):
        normalized = _normalize_action_step(step, self.target)

        if not normalized:
            return "<empty>"

        action, target = normalized
        action_name = action.name if isinstance(action, Action) else str(action)
        return f"{action_name}({target})"
        

    def summary(self):
        """Return a readable multi-step plan description."""

        summary = str(self)
        summary += "\n\tActions: ["
        first = True
        for action in self.all_actions():
            summary += f"{'' if first else ', '}{self._describe_step(action)}"
            first = False
        summary += "]"
        return summary

    def __str__(self):
        return f"Task : [{self.heuristic}] for [{len(self.all_actions())} actions on {self.target}]"

class NGIN_Simulae_Actor(SimulaeNode):

    def __init__(self, simulae_node: SimulaeNode):
        super().__init__(
            given_id=simulae_node.ID,
            nodetype=simulae_node.Nodetype,
            references=simulae_node.References,
            attributes=simulae_node.Attributes,
            relations=simulae_node.Relations,
            checks=simulae_node.Checks,
            abilities=simulae_node.Abilities,
        )

        self.inventory = {}

        self.priorities: list = []
        self.plans = {}

        self.tasks = { priority:[] for priority in TASK_PRIORITIES}

        self.Attributes[STATUS_THRESHOLDS] = {
            THREAT: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAXIMUM: 90
            },
            HUNGER: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAXIMUM: 90
            },
            THIRST: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAXIMUM: 90
            },
            EXHAUSTION: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAXIMUM: 90
            },
            SICK: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAXIMUM: 90
            },
            TEMPERATURE: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 50,
                HIGH: 80,
                MAXIMUM: 90
            },
            LONELINESS: {
                MINIMUM: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAXIMUM: 90
            }
        }

        self.priority_modifiers = {
            THREAT: 10,
            THIRST: 9,
            HUNGER: 8,
            SICK: 7,
            EXHAUSTION: 6,
            HOT: 5,
            COLD: 5,
            LONELINESS: 4,
            CRITICAL_PRIORITY: 10,
            HIGH_PRIORITY: 8,
            MEDIUM_PRIORITY: 7,
            LOW_PRIORITY: 6
        }

        # The actor can be attached to a world root later. When that happens we
        # build a lightweight lookup table so pathfinding and search work
        # against the real map instead of only the actor's local relations.
        self.world_state = None
        self.world_index: dict[str, SimulaeNode] = {}
        self.world_name_index: dict[str, list[SimulaeNode]] = {}
        self.world_location_index: dict[str, SimulaeNode] = {}
        self.world_location_graph: dict[str, set[str]] = {}

    def attach_world_state(self, world_state: SimulaeNode | None):
        """Attach a shared world root and rebuild cached lookup tables."""

        logAll("attach_world_state(", world_state, ")")

        self.world_state = world_state
        self.rebuild_world_index()
        return self.world_state

    def rebuild_world_index(self):
        """Walk the world graph and cache ID, name, and location lookups."""

        logAll("rebuild_world_index()")

        self.world_index = {}
        self.world_name_index = {}
        self.world_location_index = {}
        self.world_location_graph = {}

        if not self.world_state:
            return

        visited = set()

        for node in self._iter_world_nodes(self.world_state, visited):
            self.world_index[node.ID] = node

            name = node.get_reference(NAME)
            if name:
                key = _normalize_search_key(name)
                self.world_name_index.setdefault(key, []).append(node)

            if node.Nodetype == LOC:
                self.world_location_index[node.ID] = node

        # Build a location-only adjacency graph for BFS travel plans.
        for loc_id, loc_node in self.world_location_index.items():
            self.world_location_graph[loc_id] = {
                adjacent.ID
                for adjacent in (loc_node.get_adjacent_locations() or [])
                if adjacent and adjacent.Nodetype == LOC
            }

    def _iter_world_nodes(self, node: SimulaeNode | None, visited=None):
        """Yield every node reachable from ``node`` exactly once."""

        if not node:
            return

        if visited is None:
            visited = set()

        if node.ID in visited:
            return

        visited.add(node.ID)
        yield node

        for relation_type, relation_map in getattr(node, "Relations", {}).items():
            if not relation_map:
                continue

            for nodetype_map in relation_map.values():
                for child in nodetype_map.values():
                    if child and child.ID not in visited:
                        yield from self._iter_world_nodes(child, visited)

    def find_world_nodes(self, criteria, only_locations: bool = False):
        """Search the attached world index for nodes that match ``criteria``."""

        logAll("find_world_nodes(", criteria, ", only_locations=", only_locations, ")")

        if self.world_state and not self.world_index:
            self.rebuild_world_index()

        if not self.world_state:
            # Fallback to the actor's own physical relations when no shared
            # world root is attached yet.
            matches = self.get_relations_by_criteria(criteria, relation_types=(CONTENTS, COMPONENTS, ATTACHMENTS, ADJACENT))
            if only_locations:
                return [node for node in matches if node and node.Nodetype == LOC]
            return matches

        matches = []
        seen_ids = set()

        for node in self.world_index.values():
            if not node or node.ID in seen_ids:
                continue

            if only_locations and node.Nodetype != LOC:
                continue

            if _node_matches_criteria(node, criteria):
                seen_ids.add(node.ID)
                matches.append(node)

        return matches

    def resolve_world_node(self, criteria, nodetype: str | None = None):
        """Return the best single world node for ``criteria`` if possible."""

        logAll("resolve_world_node(", criteria, ", nodetype=", nodetype, ")")

        matches = self.find_world_nodes(criteria, only_locations=(nodetype == LOC))

        if nodetype:
            matches = [node for node in matches if node and node.Nodetype == nodetype]

        if not matches:
            return None

        if len(matches) == 1:
            return matches[0]

        if isinstance(criteria, SimulaeNode):
            criteria_id = criteria.ID
            criteria_name = criteria.get_reference(NAME)
        else:
            criteria_id = criteria if isinstance(criteria, str) else None
            criteria_name = criteria if isinstance(criteria, str) else None

        def score(node):
            value = 0

            if criteria_id and node.ID == criteria_id:
                value -= 100

            if criteria_name:
                candidate_name = node.get_reference(NAME)
                if candidate_name and _normalize_search_key(candidate_name) == _normalize_search_key(criteria_name):
                    value -= 50

            if nodetype and node.Nodetype == nodetype:
                value -= 20

            # Prefer the closest location when multiple matches remain.
            if node.Nodetype == LOC:
                distance = self.get_world_distance_to(node)
                if distance is not None:
                    value += distance

            return value

        return min(matches, key=score)

    def get_current_location_node(self):
        """Resolve the actor's current location reference into a real node."""

        logAll("get_current_location_node()")

        location_id = self.get_location()
        if not location_id:
            return None

        if self.world_state and not self.world_index:
            self.rebuild_world_index()

        if self.world_state:
            node = self.world_index.get(location_id) or self.world_state.get_relation_by_ID(location_id)
            if node and node.Nodetype == LOC:
                return node

        # Local fallback: if the actor already knows the location as a direct
        # relation, return that node even when no shared world root is attached.
        matches = self.get_relations_by_criteria(location_id, relation_types=(CONTENTS, ATTACHMENTS, COMPONENTS, ADJACENT))
        for match in matches:
            if match and match.Nodetype == LOC and match.ID == location_id:
                return match

        return None

    def _resolve_location_target(self, target):
        """Normalize a target into the actual location node we should travel to."""

        logAll("_resolve_location_target(", target, ")")

        if target is None:
            return None

        if self.world_state and not self.world_index:
            self.rebuild_world_index()

        if isinstance(target, SimulaeNode):
            if target.Nodetype == LOC:
                if target.ID in self.world_index:
                    return self.world_index[target.ID]

                return target

            target_location = target.get_location()
            if target_location:
                resolved_location = self.resolve_world_node(target_location, nodetype=LOC)
                if resolved_location:
                    return resolved_location

            return self.resolve_world_node(target, nodetype=LOC)

        return self.resolve_world_node(target, nodetype=LOC)

    def get_world_path_to(self, target):
        """Return the shortest location path to ``target`` as real nodes."""

        logAll("get_world_path_to(", target, ")")

        if self.world_state and not self.world_index:
            self.rebuild_world_index()

        start = self.get_current_location_node()
        end = self._resolve_location_target(target)

        if not end:
            return None

        if start and start.ID == end.ID:
            return [start]

        if not start or not self.world_location_graph:
            return None

        queue = deque([(start.ID, [start.ID])])
        visited = {start.ID}

        while queue:
            current_id, path = queue.popleft()

            for adjacent_id in self.world_location_graph.get(current_id, set()):
                if adjacent_id in visited:
                    continue

                next_path = path + [adjacent_id]

                if adjacent_id == end.ID:
                    resolved_path = []
                    for loc_id in next_path:
                        loc_node = self.world_location_index.get(loc_id)
                        if loc_node:
                            resolved_path.append(loc_node)
                    return resolved_path

                visited.add(adjacent_id)
                queue.append((adjacent_id, next_path))

        return None

    def get_world_distance_to(self, target):
        """Return the travel distance to ``target`` when the world is known."""

        logAll("get_world_distance_to(", target, ")")

        path = self.get_world_path_to(target)

        if path is None:
            return None

        return len(path)

    def plan(self):
        """Build plans for every currently prioritized goal."""

        logAll('plan()')

        if not self.priorities:
            self.prioritize()
        
        plans = {}

        for goal in self.priorities:
            logAll('Planning for goal:', goal)

            priority, task = goal

            plan = self.plan_task(task)

            if plan:
                plans[task] = plan
                continue
            
            logAll('no plan for',task)
        
        self.plans = plans
        
    def plan_task(self, task: str) -> TaskPlan | list | str | None:
        """Translate a prioritized goal into a concrete `TaskPlan`."""

        logAll('plan_task(',task,')')

        if task in STATUS_ATTRIBUTES or task == SLEEP:
            return self.plan_status_task(task)
        elif task == THREAT:
            return self.plan_threat_reaction()
        else:
            logAll('no planning for',task)
            return None

    def plan_status_task(self, task):
        """Create a survival-oriented plan for a basic status need."""

        logAll('plan_status_task(',task,')')

        # The target is intentionally fuzzy. The acquisition helpers can match
        # by ID, name, or relation data, so a named template is enough.
        if task == HUNGER:
            target = SimulaeNode(given_id='food', nodetype=OBJ, references={NAME: 'food'})
            acquisition = self.acquire(target)
            return TaskPlan(target, Action.USE, acquisition)

        if task == THIRST:
            target = SimulaeNode(given_id='drink', nodetype=OBJ, references={NAME: 'drink'})
            acquisition = self.acquire(target)
            return TaskPlan(target, Action.USE, acquisition)

        if task in [SLEEP, EXHAUSTION]:
            target = SimulaeNode(given_id='bed', nodetype=OBJ, references={NAME: 'bed'})
            acquisition = self.acquire(target)
            return TaskPlan(target, Action.USE, acquisition)

        if task == SICK:
            target = SimulaeNode(given_id='medicine', nodetype=OBJ, references={NAME: 'medicine'})
            acquisition = self.acquire(target)
            return TaskPlan(target, Action.USE, acquisition)

        if task == LONELINESS:
            target = SimulaeNode(given_id='friend', nodetype=POI, references={NAME: 'friend'})
            # Social contact is search-first. We do not "take" people.
            return TaskPlan(target, Action.INTERACT, [(Action.SEARCH, target)])

        if task in [HOT, COLD]:
            target = SimulaeNode(given_id='shelter', nodetype=LOC, references={NAME: 'shelter'})
            return TaskPlan(target, Action.GOTO, [(Action.SEARCH, target)])

        return None

    def plan_threat_reaction(self):
        """Build a simple defensive fallback when the actor feels threatened."""

        logAll('plan_threat_reaction()')

        # We do not yet have combat or tactical terrain, so the safest short
        # term reaction is to search for cover and then move toward it.
        target = SimulaeNode(given_id='cover', nodetype=LOC, references={NAME: 'cover'})
        return TaskPlan(target, Action.GOTO, [(Action.SEARCH, target)])

    def act_next(self, prioritized=False):
        """Execute one step from the highest-priority active plan."""

        logAll('act_next(',prioritized,')')

        if not self.priorities:
            if prioritized:
                logAll("no priorities??")
                return None

            logAll('re-prioritizing')
            self.prioritize()
            return self.act_next(prioritized=True)

        while self.priorities:
            task = self.priorities[0]

            if not task:
                logAll('no task?')
                self.priorities.pop(0)
                continue
            
            priority, goal = task

            if goal not in self.plans or self.plans[goal] is None:
                self.plans[goal] = self.plan_task(goal)

            plan = self.plans.get(goal)

            logAll(f"Need to solve: {goal} (priority: {priority})")

            if not plan:
                logAll(f'no plan for {goal}')
                self.priorities.pop(0)
                continue

            if plan.is_complete():
                self.priorities.pop(0)
                self.plans.pop(goal, None)
                continue

            logAll(plan.summary())

            completed_action = self.act(plan)

            if plan.is_complete():
                self.priorities.pop(0)
                self.plans.pop(goal, None)

            return completed_action

        return None

    def act(self, plan: TaskPlan):
        """Execute one plan step and apply the state change it implies."""

        next_action = plan.next_action()
        if not next_action:
            return None

        action, target = next_action
        resolved_target = target if target is not None else plan.target

        if action == Action.GOTO:
            # First try the shared world index so strings like "camp" resolve
            # to the actual location node rather than being stored verbatim.
            destination = self._resolve_location_target(resolved_target)

            if destination:
                self.set_location(destination)
                logAll(f'went to {destination}')
                return (action, destination)

            # Fall back to the older ID-based behavior when the actor does not
            # know about the world yet. This keeps the action usable in isolated
            # unit tests.
            if isinstance(resolved_target, SimulaeNode):
                if resolved_target.Nodetype == LOC:
                    self.set_location(resolved_target)
                else:
                    resolved_loc = resolved_target.get_location()
                    if resolved_loc:
                        self.set_location_by_ID(resolved_loc)
                    else:
                        self.set_location_by_ID(resolved_target.ID)
            else:
                self.set_location_by_ID(str(resolved_target))

            logAll(f'went to {resolved_target}')
            return next_action

        if action == Action.ACQUIRE:
            # Umbrella action used by some plan builders. We resolve it into a
            # lightweight acquire attempt so the caller gets a visible step.
            acquisition_plan = self.acquire(resolved_target)
            if acquisition_plan:
                logAll(f'acquired route for {resolved_target}: {acquisition_plan}')
            return next_action

        if action == Action.SEARCH:
            # Search first looks in the actor's immediate area and then across
            # the world index. We keep the result in memory so later actions can
            # reason about it without having to scan again.
            matches = get_targets_nearby_node(self, resolved_target, world_state=self.world_state)

            if not matches and self.world_state:
                matches = self.find_world_nodes(resolved_target)

            if matches:
                for match in matches:
                    self.Memory.setdefault(match.Nodetype, {})[match.ID] = match

                    if match.Nodetype == OBJ and match.get_location() == self.get_location():
                        # Items found in the same location are treated as
                        # discoverable and available to the actor.
                        self.set_relation(match, CONTENTS)
                logAll(f'search found {len(matches)} match(es) for {resolved_target}')
            else:
                logAll(f'search found no matches for {resolved_target}')
            return next_action

        if action == Action.TAKE:
            candidate = self._resolve_owned_candidate(resolved_target, relation_types=(CONTENTS, ATTACHMENTS))

            if not candidate:
                nearby_matches = get_targets_nearby_node(self, resolved_target, world_state=self.world_state)
                for nearby_candidate in nearby_matches:
                    if nearby_candidate and nearby_candidate.Nodetype == OBJ:
                        candidate = nearby_candidate
                        break

            if not candidate:
                logWarning(f'Cannot take {resolved_target} -> no matching node found')
                return None

            current_location = self.get_current_location_node()
            candidate_location_id = candidate.get_location()
            candidate_location = self.resolve_world_node(candidate_location_id, nodetype=LOC) if candidate_location_id else None

            # Remove the item from the place it was found before moving it into
            # the actor's inventory.
            if candidate_location:
                self._remove_node_from_location(candidate, candidate_location)

            self._remove_node_from_actor_relations(candidate)

            if current_location:
                candidate.set_location_by_ID(current_location.ID)
            elif candidate_location_id:
                candidate.set_location_by_ID(candidate_location_id)

            self.set_relation(candidate, CONTENTS)
            logAll(f'took {candidate}')
            return (action, candidate)

        if action == Action.USE:
            candidate = self._resolve_owned_candidate(resolved_target, relation_types=(CONTENTS, ATTACHMENTS))

            if not candidate:
                current_location = self.get_current_location_node()
                if current_location:
                    local_matches = current_location.get_relations_by_criteria(resolved_target)
                    if local_matches:
                        candidate = local_matches[0]

            if not candidate:
                logWarning(f'Cannot use {resolved_target} -> item not owned or known')
                return None

            effects = self._apply_item_use_effects(candidate)
            placement = _normalize_search_key(candidate.get_reference("Placement"))
            item_name = _normalize_search_key(candidate.get_reference(NAME))
            current_location = self.get_current_location_node()

            if candidate.get_check('deployable') or placement == "location" or item_name == "bed":
                # Deployable items become part of the current location instead
                # of staying in inventory.
                if current_location:
                    candidate_location_id = candidate.get_location()
                    if candidate_location_id:
                        old_location = self.resolve_world_node(candidate_location_id, nodetype=LOC)
                        if old_location:
                            self._remove_node_from_location(candidate, old_location)

                    self._remove_node_from_actor_relations(candidate)
                    current_location.set_relation(candidate, CONTENTS)
                    candidate.set_location_by_ID(current_location.ID)
                logAll(f'deployed {candidate} with effects {effects}')
                return (action, candidate)

            if candidate.get_check('wearable') or placement == "attachments" or item_name in {"blanket", "cloak", "cover"}:
                # Wearable items move from contents to attachments.
                candidate_location_id = candidate.get_location()
                if candidate_location_id:
                    old_location = self.resolve_world_node(candidate_location_id, nodetype=LOC)
                    if old_location:
                        self._remove_node_from_location(candidate, old_location)

                self._remove_node_from_actor_relations(candidate)
                self.set_relation(candidate, ATTACHMENTS)

                if current_location:
                    candidate.set_location_by_ID(current_location.ID)

                logAll(f'used {candidate} as attachment with effects {effects}')
                return (action, candidate)

            if candidate.get_check('consumable') or candidate.get_check('edible') or candidate.get_check('drinkable') or item_name in ['food', 'drink', 'medicine', 'bandage', 'stew', 'tea']:
                candidate_location_id = candidate.get_location()
                if candidate_location_id:
                    old_location = self.resolve_world_node(candidate_location_id, nodetype=LOC)
                    if old_location:
                        self._remove_node_from_location(candidate, old_location)

                self._remove_node_from_actor_relations(candidate)
                logAll(f'consumed {candidate} with effects {effects}')
                return (action, candidate)

            logAll(f'used {candidate} with effects {effects}')
            return (action, candidate)

        if action == Action.MAKE:
            recipe = self.get_recipe_definition(resolved_target)

            if not recipe:
                logWarning(f'Cannot make {resolved_target} -> no recipe found')
                return None

            required_components = recipe.get("components", [])
            component_nodes = []

            for component in required_components:
                component_node = self._resolve_owned_candidate(component, relation_types=(CONTENTS, ATTACHMENTS))

                if not component_node:
                    logWarning(f'Cannot make {resolved_target} -> missing component {component}')
                    return None

                component_nodes.append(component_node)

            for component_node in component_nodes:
                component_location_id = component_node.get_location()
                if component_location_id:
                    component_location = self.resolve_world_node(component_location_id, nodetype=LOC)
                    if component_location:
                        self._remove_node_from_location(component_node, component_location)
                self._remove_node_from_actor_relations(component_node)

            candidate = self._craft_item(resolved_target, recipe)
            placement = _normalize_search_key(candidate.get_reference("Placement"))
            current_location = self.get_current_location_node()

            if placement == "attachments":
                self._remove_node_from_actor_relations(candidate)
                self.set_relation(candidate, ATTACHMENTS)
                if current_location:
                    candidate.set_location_by_ID(current_location.ID)
            elif placement == "location":
                if current_location:
                    current_location.set_relation(candidate, CONTENTS)
                    candidate.set_location_by_ID(current_location.ID)
                else:
                    self.set_relation(candidate, CONTENTS)
            else:
                self.set_relation(candidate, CONTENTS)
                if current_location:
                    candidate.set_location_by_ID(current_location.ID)

            logAll(f'made {candidate}')
            return (action, candidate)

        if action == Action.INTERACT:
            logAll(f'interacted with {resolved_target}')
            return next_action

        logAll(f'unhandled action {action} for target {resolved_target}')
        return next_action
            

    def prioritize(self):
        """Order current goals from most urgent to least urgent."""

        logAll('prioritize()')
        ''' Prioritize actions based on current needs '''
        ''' Follow rough Maslow's hierarchy of needs '''

        self.priorities = []

        # individuals have priority modifiers (based on their personality traits)

        # if we are threatened -> prioritize defense

        if self.is_threatened():
            self.priorities.append((self.priority_modifiers[THREAT], THREAT))

        # if we are starving, dehydrated, exhausted, deathly ill, etc

        if self.is_starving():
            self.priorities.append((self.priority_modifiers[HUNGER], HUNGER))
        if self.is_dehydrated():
            self.priorities.append((self.priority_modifiers[THIRST], THIRST))
        if self.is_exhausted():
            self.priorities.append((self.priority_modifiers[EXHAUSTION], EXHAUSTION))
        if self.is_overheated():
            self.priorities.append((self.priority_modifiers[HOT], HOT))
        if self.is_freezing():
            self.priorities.append((self.priority_modifiers[COLD], COLD))
        if self.is_ill():
            self.priorities.append((self.priority_modifiers[SICK], SICK))
        if self.is_lonely():
            self.priorities.append((self.priority_modifiers[LONELINESS], LONELINESS))

        # Also handle tasks by priority level

        for task_priority, tasks in self.tasks.items():
            for task in tasks:
                self.priorities.append((self.priority_modifiers[task_priority], task))

        # Higher modifiers represent more urgent needs.
        self.priorities.sort(key=lambda x: x[0], reverse=True)

    def is_threatened(self):
        return False # todo AE: implement
    
    def is_starving(self):
        hunger = self.get_attribute(HUNGER)
        hunger_threshold = self.get_status_threshold(HUNGER, HIGH)
        if hunger and hunger_threshold and hunger >= hunger_threshold:
            return True
        return False 
    
    def is_dehydrated(self):
        thirst = self.get_attribute(THIRST)
        thirst_threshold = self.get_status_threshold(THIRST, HIGH)
        if thirst and thirst_threshold and thirst >= thirst_threshold:
            return True
        return False
    
    def is_exhausted(self):
        exhaustion = self.get_attribute(EXHAUSTION)
        exhaustion_threshold = self.get_status_threshold(EXHAUSTION, HIGH)
        if exhaustion and exhaustion_threshold and exhaustion >= exhaustion_threshold:
            return True
        return False
    
    def is_hot(self):
        temp = self.get_attribute(TEMPERATURE)
        temp_threshold = self.get_status_threshold(TEMPERATURE, HIGH)
        if temp and temp_threshold and temp >= temp_threshold:
            return True
        return False
    
    def is_overheated(self):
        temp = self.get_attribute(TEMPERATURE)
        temp_threshold = self.get_status_threshold(TEMPERATURE, MAXIMUM)
        if temp and temp_threshold and temp >= temp_threshold:
            return True
        return False
    
    def is_cold(self):
        temp = self.get_attribute(TEMPERATURE)
        temp_threshold = self.get_status_threshold(TEMPERATURE, LOW)
        if temp and temp_threshold and temp <= temp_threshold:
            return True
        return False

    def is_freezing(self):
        temp = self.get_attribute(TEMPERATURE)
        temp_threshold = self.get_status_threshold(TEMPERATURE, MINIMUM)
        if temp and temp_threshold and temp <= temp_threshold:
            return True
        return False
    
    def is_ill(self):
        sick = self.get_attribute(SICK)
        sick_threshold = self.get_status_threshold(SICK, LOW)
        if sick and sick_threshold and sick >= sick_threshold:
            return True
        return False
    
    def is_lonely(self): 
        loneliness = self.get_attribute(LONELINESS)
        loneliness_threshold = self.get_status_threshold(LONELINESS, LOW)
        if loneliness and loneliness_threshold and loneliness >= loneliness_threshold:
            return True
        return False
    
    def pathfind_to(self, target):
        """Return a travel plan to the target's real map location."""

        path = self.get_world_path_to(target)

        if path is None:
            resolved_target = self._resolve_location_target(target)
            if resolved_target:
                return [(Action.GOTO, resolved_target)]

            return [(Action.GOTO, target)]

        if len(path) <= 1:
            return []

        # The first node in the path is our current location, so only emit the
        # remaining hops.
        return [(Action.GOTO, loc) for loc in path[1:]]

    def _target_label(self, target):
        """Return the most useful readable label for a target."""

        if isinstance(target, SimulaeNode):
            return target.get_reference(NAME) or target.ID

        if target is None:
            return None

        return str(target)
    
    def can_make(self, target):
        """True when the target maps to a known recipe."""

        return self.get_recipe_definition(target) is not None
    
    def get_recipe(self, target):
        """Return the workstation label and component list for ``target``."""

        recipe = self.get_recipe_definition(target)

        if not recipe:
            return None, []

        return recipe.get("workstation"), list(recipe.get("components", []))

    def get_recipe_definition(self, target):
        """Return the full crafting recipe dictionary for ``target``."""

        logAll("get_recipe_definition(", target, ")")

        target_label = self._target_label(target)
        if not target_label:
            return None

        target_key = _normalize_search_key(target_label)

        for recipe_name, recipe in CRAFTING_RECIPES.items():
            candidate_labels = [recipe_name, recipe.get("result_name")]
            candidate_labels.extend(recipe.get("aliases", []))

            normalized_labels = {
                _normalize_search_key(candidate_label)
                for candidate_label in candidate_labels
                if candidate_label
            }

            if target_key in normalized_labels:
                recipe_copy = dict(recipe)
                recipe_copy["recipe_name"] = recipe_name
                recipe_copy.setdefault("result_name", recipe_name)
                return recipe_copy

        return None

    def _resolve_owned_candidate(self, target, relation_types=(CONTENTS, ATTACHMENTS)):
        """Find a candidate item that the actor already owns or is wearing."""

        owned = self.get_relations_by_criteria(target, relation_types=relation_types)

        if owned:
            return owned[0]

        return None

    def _remove_node_from_actor_relations(self, node):
        """Remove a node from every physical bucket in the actor's inventory."""

        if not node:
            return False

        removed = False

        for relation_type in PHYSICAL_RELATIVE_TYPES:
            relation_bucket = self.Relations.get(relation_type, {}).get(node.Nodetype, {})
            if node.ID in relation_bucket:
                del relation_bucket[node.ID]
                removed = True

        return removed

    def _remove_node_from_location(self, node, location_node):
        """Remove a node from a specific location's contents bucket."""

        if not node or not location_node:
            return False

        location_bucket = location_node.Relations.get(CONTENTS, {}).get(node.Nodetype, {})

        if node.ID in location_bucket:
            del location_bucket[node.ID]
            return True

        return False

    def _apply_item_use_effects(self, candidate):
        """Apply survival-oriented effects from an item and report the changes."""

        effects = {}

        def reduce_status(attribute_name, amount):
            if not amount:
                return

            current_value = self.get_attribute(attribute_name) or 0
            new_value = max(0, current_value - max(0, int(amount)))
            self.set_attribute(attribute_name, new_value)
            effects[attribute_name] = new_value

        item_name = _normalize_search_key(candidate.get_reference(NAME))

        nutrition = candidate.get_attribute("nutrition")
        if nutrition is None and (candidate.get_check("edible") or item_name in {"food", "stew", "meal", "rations"}):
            nutrition = 10
        if nutrition:
            reduce_status(HUNGER, nutrition)

        hydration = candidate.get_attribute("hydration")
        if hydration is None and (candidate.get_check("drinkable") or item_name in {"drink", "tea", "water", "beverage"}):
            hydration = 10
        if hydration:
            reduce_status(THIRST, hydration)

        healing = candidate.get_attribute("healing")
        if healing is None and (candidate.get_check("consumable") or item_name in {"medicine", "bandage"}):
            healing = 10
        if healing:
            reduce_status(SICK, healing)
            reduce_status(EXHAUSTION, max(1, int(healing / 4)))

        restfulness = candidate.get_attribute("restfulness")
        if restfulness is None and (candidate.get_check("deployable") or item_name == "bed"):
            restfulness = 20
        if restfulness:
            reduce_status(EXHAUSTION, restfulness)
            effects["restfulness"] = restfulness

        warmth = candidate.get_attribute("warmth")
        if warmth is None and (candidate.get_check("wearable") or item_name in {"blanket", "cloak", "cover"}):
            warmth = 10
        if warmth:
            temperature = self.get_attribute(TEMPERATURE)
            if temperature is None:
                temperature = 50

            if temperature < 50:
                self.set_attribute(TEMPERATURE, min(50, temperature + warmth))
            effects[TEMPERATURE] = self.get_attribute(TEMPERATURE)

        comfort = candidate.get_attribute("comfort")
        if comfort:
            reduce_status(LONELINESS, comfort)

        return effects

    def _craft_item(self, target, recipe):
        """Create a crafted item that inherits the recipe's effects and checks."""

        result_name = self._target_label(target) or recipe.get("result_name") or recipe["recipe_name"]

        crafted = SimulaeNode(
            given_id=str(uuid.uuid4()),
            nodetype=OBJ,
            references={
                NAME: result_name,
                "CraftingRecipe": recipe["recipe_name"],
                "Placement": recipe.get("placement", "inventory"),
            },
            attributes=dict(recipe.get("result_attributes", {})),
            checks=dict(recipe.get("result_checks", {})),
        )

        crafted.set_reference("RecipeResult", recipe.get("result_name", recipe["recipe_name"]))

        return crafted

    def get_status_threshold(self, threshold: str, subkey: str | None = None) -> int | float | None:
        logAll("get_status_threshold(",threshold,", ",subkey,")")

        thresholds = self.get_attribute(STATUS_THRESHOLDS)

        if not thresholds:
            logWarning("No status thresholds found for actor")
            return None
        
        if type(thresholds) != dict:
            logAll("Invalid thresholds format for",threshold,":",thresholds)
            return None

        if threshold in thresholds:
            if subkey and subkey in thresholds[threshold]:
                return thresholds[threshold][subkey]
            elif not subkey:
                return thresholds[threshold]

        return None

    def has_vague(self, target):
        return bool(self.get_relations_by_criteria(target, relation_types=(CONTENTS, ATTACHMENTS)))

    def acquire_vague_target(self, target):
        """Return a concrete action chain for a loosely specified target."""

        if self.has_vague(target):
            return [] # base case -> already have it

        # Look locally first so existing inventory / nearby objects win over a
        # farther-away world search.
        candidates = get_targets_nearby_node(self, target, world_state=self.world_state)

        if not candidates:
            candidates = self.find_world_nodes(target)

        target_nodetype = target.Nodetype if isinstance(target, SimulaeNode) else None
        if target_nodetype:
            candidates = [candidate for candidate in candidates if candidate and candidate.Nodetype == target_nodetype]

        route_options = []

        for candidate in candidates:
            if not candidate:
                continue

            if candidate.Nodetype == LOC:
                actions = self.pathfind_to(candidate)
            elif nodes_are_adjacent(self, candidate):
                actions = [(Action.TAKE, candidate)]
            else:
                candidate_location = candidate.get_location()

                if candidate_location:
                    actions = self.pathfind_to(candidate_location)
                    actions.append((Action.TAKE, candidate))
                else:
                    actions = [(Action.SEARCH, candidate)]

            route_options.append((get_heuristic(actions, actor=self, target=candidate), actions))

        if route_options:
            _, best_route = min(route_options, key=lambda item: item[0])
            return best_route

        return None
    
    def has_node(self, node: SimulaeNode):
        """Return True when the actor already owns or has equipped a node."""

        return bool(self.get_relations_by_criteria(node, relation_types=(CONTENTS, ATTACHMENTS)))


    def acquire(self, target: SimulaeNode):
        """Plan how to obtain a target node or target-like item."""
  
        # do we already have one?
        if self.has_node(target):
            return [] # base case -> already have it

        actions = self.acquire_vague_target(target)

        if actions is not None:
            return actions

        # Do we know how to make it?
        if self.can_make(target):
            crafting_loc, required_components = self.get_recipe(target)
            actions = []

            if required_components:
                for component in required_components: # acquire components
                    component_actions = self.acquire(component)
                    if component_actions:
                        actions.extend(component_actions)

            if crafting_loc:
                actions.extend(self.pathfind_to(crafting_loc)) # go to workstation

            actions.append((Action.MAKE,target)) # make item
            return actions

        # we are SOL
        return [(Action.SEARCH, target)]
    
    def status_summary(self):
        summary = f"Actor: {self.summary()}\n"
        
        for attr in self.Attributes:
            summary += f"{attr}: {self.get_attribute(attr)}\n"

        return summary

    def appraise_social_event(self, social_event):

        appraisal = {
            "valence": 0, # how positive or negative is this encounter?
            "fairness": 0, # how fair or unfair is this encounter?
            "credibility": 0, # how credible is this encounter?
            "urgency": 0, # how urgent is this encounter?
            "intent_hostility": 0, # how hostile do we perceive the intent of this encounter to be?
            "threat": {
                "physical": 0, # Physical threat (to our body, health, safety, etc)
                "social": 0, # Social Threat (to our social standing, relationships, etc)
                "status": 0, # Status Threat (to our power, influence, job, etc)
                "emotional": 0, # Emotional Threat (to our emotional well-being, mental health, etc)
                "moral": 0, # Moral Threat (to our values, beliefs, etc)
                "identity": 0, # Identity Threat (to our sense of self, who we are, etc)
                "resource": 0 # Resource Threat (to our possessions, money, etc)
            },
        }

        # TODO AE: Calculate appraisal Here



        return appraisal
    
    def handle_social_interaction(self, social_event, parties, conversation_history):
        
        # get appraisal of the social event
        appraisal = self.appraise_social_event(social_event)

        # determine meaning?

        # evaluate response options 

        # select response

        response = self.select_response(social_event,
                                        appraisal,
                                        parties,
                                        conversation_history)
        
        return response

    def select_response(self, # includes emotional state
                        social_event,
                        appraisal,
                        relevant_parties,
                        conversation_history):
        weights = {}

        # get event response options
        response_options = []

        for response in response_options:
            base_weight = RESPONSE_WEIGHTS[social_event.type].get(response, 1.0)
            
            personality_weight = 1.0 # todo AE: calculate personality weight based on NPC's personality traits and the nature of the response (e.g. if response is aggressive, then weight would be higher for NPCs with aggressive traits)
            political_weight = 1.0 # todo AE: calculate political weight based on NPC's political beliefs and the nature of the response (e.g. if response is politically charged, then weight would be higher for NPCs with strong political beliefs)
            appraisal_weight = 1.0 # todo AE: calculate appraisal weight based on the NPC's appraisal of the social event and how well the response addresses that appraisal (e.g. if NPC appraises the event as highly threatening, then a response that effectively mitigates that threat would have a higher weight)
            relationship_weight = 1.0 # todo AE: calculate relationship weight based on the NPC's relationship with the relevant parties and how well the response aligns with that relationship (e.g. if NPC has a close relationship with the instigator of the event, then a response that defends or supports that instigator would have a higher weight)
            past_interaction_weight = 1.0 # todo AE: calculate past interaction weight based on the NPC's past interactions with the relevant parties and how well the response aligns with those past interactions (e.g. if NPC has had positive interactions with the instigator in the past, then a response that is supportive of the instigator would have a higher weight)
            conversation_history_weight = 1.0 # todo AE: calculate conversation history weight based on the NPC's conversation history with the relevant parties and how well the response aligns with that conversation history (e.g. if NPC has had a recent argument with the instigator, then a response that de-escalates the situation might have a higher weight)

            # apply modifiers
            weight = base_weight * personality_weight * political_weight * appraisal_weight * relationship_weight * past_interaction_weight * conversation_history_weight

            # floor and clamp
            weight = max(0.001, min(weight, 1000.0))
            weights[response] = weight

        # select response based on weights
        if weights:
            max_value = max(weights.values())
            max_keys = [k for k, v in weights.items() if v == max_value]   

            return max_keys[0] if max_keys else None

        return None

    def hard_gate(self, npcs, appraisal, response, social_event, conversation_history):
        return False # todo AE: implement
    

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

        if act == Action.GOTO:
            if actor and step_target:
                logAll('getting distance from ',actor,'to',step_target)
                value += distance_between(actor, step_target)
            else:
                logWarning(f"get_heuristic( action = {Action.GOTO}(goto), .. ) -> actor and target are {None}(none)")
        elif act == Action.TAKE:
            value += 1
        elif act == Action.USE:
            value += 1
        elif act == Action.MAKE:
            value += 2
        elif act == Action.SEARCH:
            value += 2
        elif act == Action.INTERACT:
            value += 1
        elif act == Action.ACQUIRE:
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
