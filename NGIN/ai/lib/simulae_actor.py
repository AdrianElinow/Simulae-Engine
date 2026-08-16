import uuid
from collections import deque
from .socialization_constants import SOCIAL_INTERACTION_TYPES, SOCIAL_INTERACTION_QUALIFIERS, RESPONSE_WEIGHTS, EVENT_CLASSES, EVENT_VISIBILITIES, SOCIAL_RESPONSE_CANDIDATES, SOCIAL_RESPONSE_SUBTYPES, CRAFTING_RECIPES
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from .ngin_action import SimulaeAction 
from .task_plan import TaskPlan
from .socialization_utils import _canonical_social_type, _node_matches_criteria, _normalize_search_key, _normalize_social_key, get_heuristic, get_targets_nearby_node, nodes_are_adjacent
from NGIN.utilities.lib.ngin_utils import logAll, logWarning
from NGIN.utilities.lib.SimulaeConstants import *

class SimulaeActor(SimulaeNode):

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

        self.tasks = { priority:[] for priority in TASK_PRIORITIES }

        self.Attributes[STATUS_THRESHOLDS] = {
            THREAT: {
                MIN: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAX: 90
            },
            HUNGER: {
                MIN: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAX: 90
            },
            THIRST: {
                MIN: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAX: 90
            },
            EXHAUSTION: {
                MIN: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAX: 90
            },
            SICK: {
                MIN: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAX: 90
            },
            TEMPERATURE: {
                MIN: 10,
                LOW: 20,
                VALUE: 50,
                HIGH: 80,
                MAX: 90
            },
            LONELINESS: {
                MIN: 10,
                LOW: 20,
                VALUE: 0,
                HIGH: 80,
                MAX: 90
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
            return TaskPlan(target, SimulaeAction.USE, acquisition)

        if task == THIRST:
            target = SimulaeNode(given_id='drink', nodetype=OBJ, references={NAME: 'drink'})
            acquisition = self.acquire(target)
            return TaskPlan(target, SimulaeAction.USE, acquisition)

        if task in [SLEEP, EXHAUSTION]:
            target = SimulaeNode(given_id='bed', nodetype=OBJ, references={NAME: 'bed'})
            acquisition = self.acquire(target)
            return TaskPlan(target, SimulaeAction.USE, acquisition)

        if task == SICK:
            target = SimulaeNode(given_id='medicine', nodetype=OBJ, references={NAME: 'medicine'})
            acquisition = self.acquire(target)
            return TaskPlan(target, SimulaeAction.USE, acquisition)

        if task == LONELINESS:
            target = SimulaeNode(given_id='friend', nodetype=POI, references={NAME: 'friend'})
            # Social contact is search-first. We do not "take" people.
            return TaskPlan(target, SimulaeAction.INTERACT, [(SimulaeAction.SEARCH, target)])

        if task in [HOT, COLD]:
            target = SimulaeNode(given_id='shelter', nodetype=LOC, references={NAME: 'shelter'})
            return TaskPlan(target, SimulaeAction.GOTO, [(SimulaeAction.SEARCH, target)])

        return None

    def plan_threat_reaction(self):
        """Build a simple defensive fallback when the actor feels threatened."""

        logAll('plan_threat_reaction()')

        # We do not yet have combat or tactical terrain, so the safest short
        # term reaction is to search for cover and then move toward it.
        target = SimulaeNode(given_id='cover', nodetype=LOC, references={NAME: 'cover'})
        return TaskPlan(target, SimulaeAction.GOTO, [(SimulaeAction.SEARCH, target)])

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

        if action == SimulaeAction.GOTO:
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

        if action == SimulaeAction.ACQUIRE:
            # Umbrella action used by some plan builders. We resolve it into a
            # lightweight acquire attempt so the caller gets a visible step.
            acquisition_plan = self.acquire(resolved_target)
            if acquisition_plan:
                logAll(f'acquired route for {resolved_target}: {acquisition_plan}')
            return next_action

        if action == SimulaeAction.SEARCH:
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

        if action == SimulaeAction.TAKE:
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

        if action == SimulaeAction.USE:
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

        if action == SimulaeAction.MAKE:
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

        if action == SimulaeAction.INTERACT:
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
        temp_threshold = self.get_status_threshold(TEMPERATURE, MAX)
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
        temp_threshold = self.get_status_threshold(TEMPERATURE, MIN)
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
                return [(SimulaeAction.GOTO, resolved_target)]

            return [(SimulaeAction.GOTO, target)]

        if len(path) <= 1:
            return []

        # The first node in the path is our current location, so only emit the
        # remaining hops.
        return [(SimulaeAction.GOTO, loc) for loc in path[1:]]

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
                actions = [(SimulaeAction.TAKE, candidate)]
            else:
                candidate_location = candidate.get_location()

                if candidate_location:
                    actions = self.pathfind_to(candidate_location)
                    actions.append((SimulaeAction.TAKE, candidate))
                else:
                    actions = [(SimulaeAction.SEARCH, candidate)]

            route_options.append((get_heuristic(actions, actor=self, target=candidate), actions))

        if route_options:
            _, best_route = min(route_options, key=lambda item: item[0])
            return best_route

        return None
    
    def has_node(self, node: SimulaeNode):
        """Return True when the actor already owns or has equipped a node."""

        return bool(self.get_relations_by_criteria(node, relation_types=(CONTENTS, ATTACHMENTS)))


    def acquire(self, target: SimulaeNode | str):
        """Plan how to obtain a target node or target-like item."""
  
        # do we already have one?
        if target is SimulaeNode and self.has_node(target):
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

            actions.append((SimulaeAction.MAKE,target)) # make item
            return actions

        # we are SOL
        return [(SimulaeAction.SEARCH, target)]
    
    def status_summary(self):
        summary = f"Actor: {self.summary()}\n"
        
        for attr in self.Attributes:
            summary += f"{attr}: {self.get_attribute(attr)}\n"

        return summary

    def _normalize_social_parties(self, parties):
        """Return a clean list of interaction partners."""

        if parties is None:
            return []

        if isinstance(parties, (list, tuple, set)):
            return [party for party in parties if party]

        return [parties]

    def _summarize_social_party(self, party):
        """Convert a party into a small serializable summary for history."""

        if not party:
            return None

        if isinstance(party, dict):
            return {
                "id": party.get("id") or party.get("ID"),
                "name": party.get("name") or party.get(NAME),
                "nodetype": party.get("nodetype") or party.get(NODETYPE),
            }

        if isinstance(party, SimulaeNode):
            return {
                "id": party.ID,
                "name": party.get_reference(NAME),
                "nodetype": party.Nodetype,
            }

        return {
            "id": str(party),
            "name": str(party),
            "nodetype": None,
        }

    def _normalize_social_event(self, social_event):
        """Coerce a loose prompt or response record into a stable dictionary."""

        def pick(source, *keys):
            if not source:
                return None

            if isinstance(source, dict):
                for key in keys:
                    if key in source and source[key] not in (None, ""):
                        return source[key]
                return None

            getter = getattr(source, "get_reference", None)
            if callable(getter):
                for key in keys:
                    value = getter(key)
                    if value not in (None, ""):
                        return value

            for key in keys:
                value = getattr(source, key, None)
                if value not in (None, ""):
                    return value

            return None

        qualifiers = {}
        source_qualifiers = pick(social_event, "qualifiers", "Qualifiers")

        if isinstance(source_qualifiers, dict):
            for qualifier_name, qualifier_value in source_qualifiers.items():
                canonical_name = qualifier_name
                for canonical_candidate in SOCIAL_INTERACTION_QUALIFIERS:
                    if _normalize_social_key(canonical_candidate) == _normalize_social_key(qualifier_name):
                        canonical_name = canonical_candidate
                        break
                qualifiers[canonical_name] = qualifier_value

        for canonical_candidate in SOCIAL_INTERACTION_QUALIFIERS:
            qualifier_value = pick(social_event, canonical_candidate, canonical_candidate.lower(), canonical_candidate.casefold())
            if qualifier_value not in (None, ""):
                qualifiers.setdefault(canonical_candidate, qualifier_value)

        def summarize(value):
            if isinstance(value, SimulaeNode):
                return self._summarize_social_party(value)
            if isinstance(value, (list, tuple, set)):
                return [summarize(item) for item in value]
            return value

        event_type = pick(social_event, "response_type", "event_type", "eventtype", "type")
        event_subtype = pick(social_event, "response_subtype", "event_subtype", "eventsubtype", "subtype")

        return {
            "event_type": _canonical_social_type(event_type),
            "event_subtype": _normalize_social_key(event_subtype) or None,
            "response_type": _canonical_social_type(pick(social_event, "response_type")) or _canonical_social_type(event_type),
            "response_subtype": _normalize_social_key(pick(social_event, "response_subtype")) or _normalize_social_key(event_subtype) or None,
            "domain": pick(social_event, "domain") or qualifiers.get("Domain"),
            "polarity": pick(social_event, "polarity") or qualifiers.get("Polarity"),
            "force": pick(social_event, "force") or qualifiers.get("Force"),
            "honesty": pick(social_event, "honesty") or qualifiers.get("Honesty"),
            "visibility": pick(social_event, "visibility") or qualifiers.get("Visibility"),
            "evidence": pick(social_event, "evidence") or qualifiers.get("Evidence"),
            "authority": pick(social_event, "authority") or qualifiers.get("Authority"),
            "time": pick(social_event, "time") or qualifiers.get("Time"),
            "topic": pick(social_event, "topic"),
            "subject": pick(social_event, "subject"),
            "claim": pick(social_event, "claim"),
            "question": pick(social_event, "question"),
            "source": summarize(pick(social_event, "source", "speaker", "actor")),
            "target": summarize(pick(social_event, "target", "listener", "recipient")),
            "sources": summarize(pick(social_event, "sources")) or [],
            "targets": summarize(pick(social_event, "targets")) or [],
            "observers": summarize(pick(social_event, "observers")) or [],
            "qualifiers": qualifiers,
            "content": summarize(pick(social_event, "content", "payload", "information_target", "inquiry_target")),
        }

    def _response_candidates_for_event_type(self, event_type):
        """Return the most plausible response families for a prompt type."""

        if not event_type:
            return list(SOCIAL_RESPONSE_CANDIDATES["default"])

        return list(SOCIAL_RESPONSE_CANDIDATES.get(event_type, SOCIAL_RESPONSE_CANDIDATES["default"]))

    def _select_response_subtype(self, response_type, social_event, appraisal, conversation_history):
        """Pick a small subtype label so the response reads like a real act."""

        history = conversation_history if isinstance(conversation_history, list) else []
        prompt_type = social_event.get("event_type")

        if response_type == "Open":
            return "acknowledge" if history else "greet"

        if response_type == "Close":
            if prompt_type in {"Close", "Turn", "Boundary"}:
                return "farewell"
            return "withdraw"

        if response_type == "Inform":
            if prompt_type == "Inquire":
                return "answer"
            if appraisal.get("credibility", 0) < 0:
                return "clarify"
            return "share"

        if response_type == "Inquire":
            if prompt_type == "Inform":
                if appraisal.get("credibility", 0) <= 0:
                    return "clarify"
                return "probe"
            if prompt_type == "Open":
                return "ask"
            return "probe"

        if response_type == "Stance":
            return "agree" if appraisal.get("valence", 0) >= 0 else "refuse"

        if response_type == "Affect":
            return "praise" if appraisal.get("valence", 0) >= 0 else "criticize"

        if response_type == "Negotiate":
            return "offer" if appraisal.get("fairness", 0) >= 0 else "counteroffer"

        if response_type == "Boundary":
            return "set-boundary"

        if response_type == "Coordinate":
            return "organize"

        if response_type == "Direct":
            return "request"

        if response_type == "Influence":
            return "reassure" if appraisal.get("valence", 0) >= 0 else "pressure"

        if response_type == "Deceive":
            return "conceal"

        if response_type == "Topic":
            return "stay-topic"

        if response_type == "Summary":
            return "summarize"

        subtype_options = SOCIAL_RESPONSE_SUBTYPES.get(response_type, SOCIAL_RESPONSE_SUBTYPES["default"])
        return subtype_options[0] if subtype_options else "share"

    def _resolve_selected_response_content(self, response_type, social_event, appraisal, conversation_history):
        """Resolve a small payload for information-like responses."""

        def first_non_empty(*values):
            for value in values:
                if value not in (None, "", [], {}, ()):
                    return value
            return None

        history = conversation_history if isinstance(conversation_history, list) else []
        qualifiers = social_event.get("qualifiers") or {}

        topic = first_non_empty(
            social_event.get("topic"),
            social_event.get("subject"),
            social_event.get("claim"),
        )
        domain = first_non_empty(
            social_event.get("domain"),
            qualifiers.get("Domain"),
        )
        evidence = first_non_empty(
            social_event.get("evidence"),
            qualifiers.get("Evidence"),
        )
        question = first_non_empty(
            social_event.get("question"),
            social_event.get("content", {}).get("question") if isinstance(social_event.get("content"), dict) else None,
        )
        source = first_non_empty(
            social_event.get("source"),
            social_event.get("prompt_event", {}).get("source") if isinstance(social_event.get("prompt_event"), dict) else None,
        )
        time = first_non_empty(social_event.get("time"), qualifiers.get("Time"))

        if not topic and history:
            recent = history[-1]
            if isinstance(recent, dict):
                recent_prompt = recent.get("prompt_event") if isinstance(recent.get("prompt_event"), dict) else {}
                recent_response = recent.get("response") if isinstance(recent.get("response"), dict) else {}
                recent_content = recent_response.get("content") if isinstance(recent_response, dict) else {}
                topic = first_non_empty(
                    recent_prompt.get("topic") if isinstance(recent_prompt, dict) else None,
                    recent_prompt.get("subject") if isinstance(recent_prompt, dict) else None,
                    recent_prompt.get("claim") if isinstance(recent_prompt, dict) else None,
                    recent_content.get("topic") if isinstance(recent_content, dict) else None,
                    recent_content.get("subject") if isinstance(recent_content, dict) else None,
                )

        base_payload = {
            "response_type": response_type,
            "topic": topic,
            "domain": domain,
            "subject": social_event.get("subject"),
            "claim": social_event.get("claim"),
            "question": question,
            "evidence": evidence,
            "time": time,
            "source": source,
        }

        if response_type == "Inform":
            return {
                **base_payload,
                "intent": "answer_or_share",
                "information_target": base_payload,
            }

        if response_type == "Inquire":
            if evidence in {"None", "none", "Weak", "weak", None}:
                intent = "ask_for_evidence"
            elif not time:
                intent = "ask_for_timeframe"
            elif not topic:
                intent = "ask_for_subject"
            else:
                intent = "ask_for_clarification"

            return {
                **base_payload,
                "intent": intent,
                "inquiry_target": base_payload,
            }

        if response_type == "Open":
            return {
                **base_payload,
                "intent": "greet_or_acknowledge",
            }

        if response_type == "Close":
            return {
                **base_payload,
                "intent": "terminate_exchange",
            }

        if response_type == "Stance":
            return {
                **base_payload,
                "intent": "align_or_resist",
            }

        return {
            **base_payload,
            "intent": response_type.lower() if isinstance(response_type, str) else "respond",
        }

    def appraise_social_event(self, social_event):
        """Turn a social prompt into a compact appraisal record."""

        normalized_event = self._normalize_social_event(social_event)
        event_type = normalized_event.get("event_type")
        event_subtype = normalized_event.get("event_subtype")
        qualifiers = normalized_event.get("qualifiers") or {}

        appraisal = {
            "event_type": event_type,
            "event_subtype": event_subtype,
            "qualifiers": qualifiers,
            "domain": normalized_event.get("domain"),
            "polarity": normalized_event.get("polarity"),
            "force": normalized_event.get("force"),
            "honesty": normalized_event.get("honesty"),
            "visibility": normalized_event.get("visibility"),
            "evidence": normalized_event.get("evidence"),
            "authority": normalized_event.get("authority"),
            "time": normalized_event.get("time"),
            "topic": normalized_event.get("topic"),
            "subject": normalized_event.get("subject"),
            "claim": normalized_event.get("claim"),
            "question": normalized_event.get("question"),
            "source": normalized_event.get("source"),
            "target": normalized_event.get("target"),
            "salience": 0,
            "valence": 0,
            "fairness": 0,
            "credibility": 0,
            "urgency": 0,
            "intent_hostility": 0,
            "threat": {
                "physical": 0,
                "social": 0,
                "status": 0,
                "emotional": 0,
                "moral": 0,
                "identity": 0,
                "resource": 0,
            },
        }

        def bump(field, amount):
            appraisal[field] += amount

        def bump_threat(field, amount):
            appraisal["threat"][field] = max(0, appraisal["threat"][field] + amount)

        # Core interaction families contribute a coarse first-pass interpretation.
        if event_type == "Open":
            bump("valence", 3)
            bump("fairness", 1)
            bump("credibility", 1)
            bump("intent_hostility", -2)
        elif event_type == "Close":
            bump("valence", -2)
            bump("urgency", 1)
            bump_threat("social", 1)
            bump_threat("emotional", 1)
        elif event_type == "Turn":
            bump("urgency", 1)
            if event_subtype == "interrupt":
                bump("intent_hostility", 2)
                bump_threat("social", 1)
            elif event_subtype == "cede":
                bump("valence", 1)
        elif event_type == "Topic":
            bump("urgency", 1)
        elif event_type == "Inform":
            bump("credibility", 1)
            bump("fairness", 1)
            if event_subtype == "retract":
                bump("valence", -1)
                bump("credibility", -2)
                bump("intent_hostility", 1)
        elif event_type == "Inquire":
            bump("urgency", 1)
            if event_subtype == "challenge":
                bump("intent_hostility", 1)
                bump_threat("social", 1)
        elif event_type == "Stance":
            bump("fairness", 1)
            if event_subtype in {"agree", "accept", "validate"}:
                bump("valence", 2)
            elif event_subtype in {"deny", "refuse", "invalidate", "disagree"}:
                bump("valence", -2)
                bump("intent_hostility", 1)
        elif event_type == "Influence":
            bump("urgency", 1)
            bump("intent_hostility", 1)
            if event_subtype in {"reassure", "persuade", "dissuade"}:
                bump("valence", 1)
            elif event_subtype in {"pressure", "threaten"}:
                bump("valence", -2)
                bump_threat("social", 1)
                bump_threat("emotional", 1)
        elif event_type == "Affect":
            if event_subtype in {"comfort", "commiserate", "praise", "apologize", "joke"}:
                bump("valence", 2)
                bump_threat("emotional", 1)
            elif event_subtype in {"criticize", "insult", "complain"}:
                bump("valence", -2)
                bump("intent_hostility", 1)
                bump_threat("social", 1)
                bump_threat("emotional", 1)
        elif event_type == "Direct":
            bump("urgency", 1)
            bump_threat("status", 1)
            if event_subtype in {"demand", "command"}:
                bump("intent_hostility", 2)
                bump_threat("social", 1)
            elif event_subtype in {"request", "delegate"}:
                bump("valence", -1)
        elif event_type == "Negotiate":
            bump("fairness", 2)
            if event_subtype in {"offer", "volunteer"}:
                bump("valence", 2)
            elif event_subtype == "counteroffer":
                bump("valence", 1)
        elif event_type == "Boundary":
            bump("intent_hostility", 1)
            bump_threat("social", 2)
            if event_subtype == "set boundary":
                bump("valence", 1)
            elif event_subtype == "violate boundary":
                bump("valence", -3)
                bump_threat("identity", 1)
        elif event_type == "Coordinate":
            bump("urgency", 1)
            if event_subtype in {"rally", "organize", "promote"}:
                bump("valence", 2)
            elif event_subtype in {"demote", "resign"}:
                bump("valence", -1)
                bump_threat("status", 1)
        elif event_type == "Deceive":
            bump("fairness", -3)
            bump("credibility", -5)
            bump("intent_hostility", 3)
            bump_threat("moral", 2)
            bump_threat("social", 1)
        elif event_type == "Summary":
            bump("credibility", 1)

        # Qualifiers from the wiki provide the nuanced shading.
        polarity = _normalize_social_key(appraisal["polarity"] or qualifiers.get("Polarity"))
        if polarity == "positive":
            bump("valence", 2)
        elif polarity == "negative":
            bump("valence", -2)
            bump("intent_hostility", 1)
            bump_threat("social", 1)

        force = _normalize_social_key(appraisal["force"] or qualifiers.get("Force"))
        if force == "high":
            bump("urgency", 2)
            bump("intent_hostility", 2)
            bump_threat("social", 1)
            bump_threat("emotional", 1)
        elif force == "medium":
            bump("urgency", 1)
            bump("intent_hostility", 1)

        honesty = _normalize_social_key(appraisal["honesty"] or qualifiers.get("Honesty"))
        if honesty == "truthful":
            bump("credibility", 2)
            bump("fairness", 1)
        elif honesty == "deceptive":
            bump("credibility", -3)
            bump("fairness", -2)
            bump("intent_hostility", 2)
            bump_threat("moral", 2)

        evidence = _normalize_social_key(appraisal["evidence"] or qualifiers.get("Evidence"))
        if evidence == "strong":
            bump("credibility", 2)
            bump("fairness", 1)
        elif evidence == "weak":
            bump("credibility", 1)
        elif evidence == "none":
            bump("credibility", -1)
            bump("urgency", 1)

        visibility = _normalize_social_key(appraisal["visibility"] or qualifiers.get("Visibility"))
        if visibility == "public" and appraisal["intent_hostility"] > 0:
            bump_threat("social", 1)
        elif visibility in {"private", "dyadic"}:
            bump("intent_hostility", -1)

        authority = _normalize_social_key(appraisal["authority"] or qualifiers.get("Authority"))
        if authority == "superior":
            bump("urgency", 1)
            bump("intent_hostility", -1)
            bump_threat("status", 1)
        elif authority == "subordinate":
            bump_threat("status", 1)

        time_scope = _normalize_social_key(appraisal["time"] or qualifiers.get("Time"))
        if time_scope in {"future", "ongoing"} and event_type in {"Direct", "Negotiate", "Coordinate"}:
            bump("urgency", 1)
        elif time_scope == "past" and event_type in {"Inform", "Inquire"}:
            bump("credibility", 1)

        domain = _normalize_social_key(appraisal["domain"] or qualifiers.get("Domain"))
        if domain == "resource":
            bump_threat("resource", 2)
            bump("urgency", 1)
        elif domain == "task":
            bump("urgency", 1)
            bump_threat("status", 1)
        elif domain == "relationship":
            bump_threat("social", 1)
            bump_threat("emotional", 1)
        elif domain == "identity":
            bump_threat("identity", 1)
            bump_threat("social", 1)
        elif domain == "policy":
            bump_threat("status", 1)

        appraisal["salience"] = max(
            0,
            abs(appraisal["valence"]) +
            abs(appraisal["intent_hostility"]) +
            appraisal["urgency"] +
            max(appraisal["threat"].values()),
        )

        return appraisal
    
    def handle_social_interaction(self, social_event, parties, conversation_history):
        """Resolve a prompt, choose a response, and persist the exchange."""

        normalized_event = self._normalize_social_event(social_event)
        appraisal = self.appraise_social_event(normalized_event)
        relevant_parties = self._normalize_social_parties(parties)

        # Evaluate candidate responses after the appraisal has reduced the
        # problem space. The response payload stays shallow so tests can inspect
        # it without needing to traverse a large event graph.
        response = self.select_response(
            normalized_event,
            appraisal,
            relevant_parties,
            conversation_history,
        )

        if not response:
            return None

        record = {
            "id": str(uuid.uuid4()),
            "responder": self._summarize_social_party(self),
            "prompt_event": normalized_event,
            "prompt_event_type": normalized_event.get("event_type"),
            "prompt_event_subtype": normalized_event.get("event_subtype"),
            "appraisal": appraisal,
            "response": response,
            "response_type": response.get("response_type"),
            "response_subtype": response.get("response_subtype"),
            "response_content": response.get("content"),
            "parties": [self._summarize_social_party(party) for party in relevant_parties],
        }

        social_memory = self.Memory.setdefault(SOCIAL, {})
        social_memory[record["id"]] = record

        if isinstance(conversation_history, list):
            conversation_history.append(record)

        return record

    def select_response(self, # includes emotional state
                        social_event,
                        appraisal,
                        relevant_parties,
                        conversation_history):
        """Choose the most plausible social response for the current prompt."""

        normalized_event = self._normalize_social_event(social_event)
        if appraisal is None:
            appraisal = self.appraise_social_event(normalized_event)

        parties = self._normalize_social_parties(relevant_parties)
        if not parties:
            return None

        prompt_type = normalized_event.get("event_type")
        if not prompt_type:
            return None

        response_options = self._response_candidates_for_event_type(prompt_type)
        if not response_options:
            return None

        history = conversation_history if isinstance(conversation_history, list) else []
        personality = self.get_personality() or {}
        politics = self.get_political_beliefs() or {}

        def factor_score(scale, key):
            factor = scale.get(key) if scale else None
            if not factor or not isinstance(factor, (tuple, list)) or len(factor) < 2:
                return 0.0

            try:
                index, strength = factor
                return ((float(index) - 3.0) * float(strength)) / 20.0
            except Exception:
                return 0.0

        def appraisal_bias(response_type):
            if response_type == "Open":
                return appraisal.get("valence", 0) * 2
            if response_type == "Close":
                return appraisal.get("intent_hostility", 0) * 2 + appraisal.get("urgency", 0)
            if response_type == "Inform":
                return appraisal.get("credibility", 0) * 2 + appraisal.get("fairness", 0)
            if response_type == "Inquire":
                return max(0, 3 - appraisal.get("credibility", 0)) + appraisal.get("urgency", 0)
            if response_type == "Stance":
                return abs(appraisal.get("intent_hostility", 0)) + abs(appraisal.get("valence", 0))
            if response_type == "Affect":
                return (appraisal.get("valence", 0) * 2) - appraisal.get("intent_hostility", 0)
            if response_type == "Negotiate":
                return appraisal.get("fairness", 0) + appraisal.get("urgency", 0)
            if response_type == "Direct":
                return appraisal.get("urgency", 0) + appraisal.get("intent_hostility", 0)
            if response_type == "Boundary":
                return appraisal.get("intent_hostility", 0) + appraisal["threat"]["social"]
            if response_type == "Coordinate":
                return appraisal.get("urgency", 0) + appraisal.get("fairness", 0)
            if response_type == "Influence":
                return appraisal.get("intent_hostility", 0) + appraisal.get("urgency", 0)
            if response_type == "Deceive":
                return max(0, 4 - appraisal.get("credibility", 0)) + appraisal.get("intent_hostility", 0)
            if response_type == "Topic":
                return appraisal.get("urgency", 0)
            if response_type == "Summary":
                return appraisal.get("credibility", 0)
            return 0.0

        def history_bias(response_type):
            if not history:
                return 0.0

            last_entry = history[-1]
            if not isinstance(last_entry, dict):
                return 0.0

            def entry_type(entry, *keys):
                if not isinstance(entry, dict):
                    return None

                for key in keys:
                    value = entry.get(key)
                    if value not in (None, ""):
                        return value

                return None

            last_response_type = _canonical_social_type(
                entry_type(last_entry, "response_type", "event_type", "eventtype", "type")
            )
            last_prompt = last_entry.get("prompt_event")
            last_prompt_type = _canonical_social_type(
                entry_type(last_prompt, "event_type", "eventtype", "type", "response_type")
            ) if isinstance(last_prompt, dict) else None

            bias = 0.0

            if prompt_type == "Open":
                if last_response_type == "Open":
                    if response_type == "Inquire":
                        bias += 18
                    elif response_type == "Inform":
                        bias += 8
                    elif response_type == "Open":
                        bias -= 15
                elif last_response_type == "Close" and response_type == "Open":
                    bias += 8

            if prompt_type == "Inform":
                if last_prompt_type == "Inquire" and last_response_type == "Inform":
                    if response_type == "Inquire":
                        bias += 15
                    elif response_type == "Inform":
                        bias += 5
                elif last_response_type == "Inform" and response_type == "Inquire":
                    bias += 8

            if prompt_type == "Inquire" and last_response_type == "Inform" and response_type == "Inquire":
                bias += 6

            if response_type == last_response_type:
                bias -= 2

            return bias

        def personality_bias(response_type):
            bias = 0.0

            if response_type == "Open":
                traits = [("Empathy", 0.8), ("Cooperativeness", 0.8), ("Social-Energy", 1.0), ("Trust", 0.4)]
                policies = [("Diplomacy", 0.2)]
            elif response_type == "Inform":
                traits = [("Conscientiousness", 0.9), ("Curiosity", 0.5), ("Trust", 0.4), ("Cognitive-Style", 0.3)]
                policies = [("Legality", 0.2)]
            elif response_type == "Inquire":
                traits = [("Curiosity", 1.0), ("Trust", 0.5), ("Conscientiousness", 0.4)]
                policies = [("Diplomacy", 0.2)]
            elif response_type == "Stance":
                traits = [("Assertiveness", 0.9), ("Conflict-Style", 0.8), ("Conscience", 0.4), ("Trust", -0.3)]
                policies = [("Legality", 0.2), ("Justice", 0.2)]
            elif response_type == "Affect":
                traits = [("Empathy", 1.0), ("Attachment", 0.7), ("Social-Energy", 0.4)]
                policies = [("Culture", 0.1)]
            elif response_type == "Negotiate":
                traits = [("Cooperativeness", 1.0), ("Conscientiousness", 0.4), ("Curiosity", 0.2)]
                policies = [("Diplomacy", 0.4), ("Legality", 0.1)]
            elif response_type == "Direct":
                traits = [("Assertiveness", 0.8), ("Ambition", 0.5), ("Conscientiousness", 0.3)]
                policies = [("Militancy", 0.3), ("Government", 0.1)]
            elif response_type == "Boundary":
                traits = [("Assertiveness", 0.8), ("Resilience", 0.5), ("Trust", -0.2)]
                policies = [("Legality", 0.4), ("Justice", 0.2)]
            elif response_type == "Coordinate":
                traits = [("Conscientiousness", 0.8), ("Cooperativeness", 0.8), ("Social-Energy", 0.3)]
                policies = [("Government", 0.4), ("Diplomacy", 0.3)]
            elif response_type == "Influence":
                traits = [("Assertiveness", 0.7), ("Ambition", 0.4), ("Trust", -0.2)]
                policies = [("Militancy", 0.3), ("Diplomacy", 0.1)]
            elif response_type == "Deceive":
                traits = [("Trust", -1.0), ("Conscience", -0.8), ("Adaptability", 0.2), ("Risk", 0.2)]
                policies = [("Legality", -0.2)]
            elif response_type == "Close":
                traits = [("Resilience", 0.5), ("Conflict-Style", 0.2), ("Trust", -0.1)]
                policies = [("Diplomacy", 0.1)]
            else:
                traits = []
                policies = []

            for trait_name, weight in traits:
                bias += factor_score(personality, trait_name) * weight

            for policy_name, weight in policies:
                bias += factor_score(politics, policy_name) * weight

            return bias

        weights = {}

        for index, response_type in enumerate(response_options):
            if self.hard_gate(parties, appraisal, response_type, normalized_event, history):
                continue

            base_weight = 1.0
            base_score = float((len(response_options) - index) * 10)
            score = base_score * base_weight
            score += appraisal_bias(response_type)
            score += history_bias(response_type)
            score += personality_bias(response_type)

            # A tiny tie-breaker keeps earlier candidates stable if all other
            # factors line up exactly.
            score += max(0.0, 0.01 * (len(response_options) - index))

            weights[response_type] = score

        if not weights:
            return None

        max_value = max(weights.values())
        max_keys = [response for response, value in weights.items() if value == max_value]
        if not max_keys:
            return None

        response_type = max_keys[0]
        response_subtype = self._select_response_subtype(response_type, normalized_event, appraisal, history)
        return {
            "response_type": response_type,
            "response_subtype": response_subtype,
            "content": self._resolve_selected_response_content(response_type, normalized_event, appraisal, history),
            "score": max_value,
            "prompt_event_type": normalized_event.get("event_type"),
        }

    def hard_gate(self, npcs, appraisal, response, social_event, conversation_history):
        """Reject responses that are semantically impossible or unsupported."""

        parties = self._normalize_social_parties(npcs)
        normalized_event = self._normalize_social_event(social_event)
        prompt_type = normalized_event.get("event_type")
        response_type = _canonical_social_type(response)

        if not parties:
            return True

        if not prompt_type or not response_type:
            return True

        allowed_responses = self._response_candidates_for_event_type(prompt_type)
        if response_type not in allowed_responses:
            return True

        return False
    
