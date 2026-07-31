from __future__ import annotations

import random
import uuid

from NGIN.utilities.lib.SimulaeConstants import *
from NGIN.utilities.lib.ngin_console_log import MAX_ADJACENT_LOCATIONS
from NGIN.utilities.lib.ngin_utils import *
from NGIN.utilities.lib.social_scale_utils import (
    generate_values_for_scales,
    get_scale_diff,
    random_bell_curve_value,
)
from NGIN.NGIN_config.madlibs import *

class SimulaeNode:
    '''
    Simulae Node
    Foundational Unified data-structure for physical, social, and abstract entities in the Simulae world.
    '''

    def __init__(self,  given_id=None, 
                        nodetype=OBJ,
                        references: dict | None = None,
                        attributes: dict | None = None,
                        relations: dict | None = None, 
                        checks: dict | None = None, 
                        abilities: dict | None = None,
                        scales: dict[str, dict] | None = None, 
                        memory: dict | None = None,):
        '''
        Docstring for __init__
        
        :param self: Description
        :param given_id: String ID for this node. If None, a random UUID will be generated.
        :param nodetype: Type of node (see ALL_NODE_TYPES). Default's to OBJ (object)
        :param references: Dictionary of string-to-string 'references'
        :type references: dict[str, Any] | None
        :param attributes: Dictionary of string-to-number 'attributes'
        :type attributes: dict[str, Any] | None
        :param relations: Dictionary of string-to-node 'relations' describing the physical relationship between this node and any referenced nodes
        :type relations: dict[str, Any] | None
        :param checks: Lookup of this node's status 'checks'
        :type checks: dict[str, bool] | None
        :param abilities: Lookup of this node's abilities, if applicable.
        :type abilities: dict[str, Any] | None
        :param scales: Dictionary of string-to-dictionary 'scales' describing this node's positions on various social/political axes if applicable. 
        :type scales: dict[str, dict[str, Any]] | None
        :param memory: Log of events this node has perceived/experienced, if applicable.
        :type memory: list | None
        '''

        self.ID = given_id if given_id else str(uuid.uuid1())
        self.Nodetype = nodetype

        # avoid mutable default arguments being shared between instances
        self.References = {} if references is None else dict(references)
        self.Scales = {} if scales is None else dict(scales)
        self.Attributes = {} if attributes is None else dict(attributes)            
        self.Checks = {} if checks is None else dict(checks)
        self.Abilities = {} if abilities is None else dict(abilities)

        self.Relations = {} if relations is None else dict(relations)
        if relations is not None:
            for k,v in relations.items():
                self.Relations[k] = v

        self.Memory = { category: {} for category in MEMORY_CATEGORIES }
        if memory is not None:
            for k,v in memory.values():
                self.Memory[k] = v

        if self.Nodetype not in META_NODE_TYPES:
            self.__post_init__()

    def __post_init__(self):

        if self.Nodetype not in META_NODE_TYPES:

            if self.Nodetype in SOCIAL_NODE_TYPES:
                self.Scales[POLICY] = self.generate_policy()

                if self.Nodetype is POI:
                    self.Scales[PERSONALITY] = self.generate_personality()


            self.Relations = {
                CONTENTS:{ nt:{} for nt in PHYSICAL_NODETYPES},      # organs for POI, items contained for LOC/OBJ
                COMPONENTS:{ nt:{} for nt in PHYSICAL_NODETYPES},    # limbs for POI, parts for OBJ
                ATTACHMENTS:{ nt:{} for nt in PHYSICAL_NODETYPES},    # accessories, clothing, equipped items for POI, attachments for OBJ
                ADJACENT: { nt:{} for nt in PHYSICAL_NODETYPES} # adjacent locations for LOC
            }

    # References Section

    def keyname(self, *args) -> str:
        return '|'.join(args)
    
    def get_description(self):
        description = ""

        if self.Nodetype == POI:

            associations = self.describe_faction_associations()

            policies = self.describe_political_beliefs()

            personality = self.describe_personality()

            description = f"{self.get_reference(NAME)}, A {self.get_attribute('Age')} year old {self.get_reference('Gender')}"

            if associations:
                description += f"\n--- ASSOCIATIONS ---\n{associations}"

            if personality:
                description += f"\n--- PERSONALITY ---\n{personality}"

            if policies:
                description += f"\n--- POLITICAL BELIEFS ---\n{policies}"

        return description

    def summary(self):
        
        summary = f"{self.Nodetype}:{self.get_reference(NAME)}"

        if self.Nodetype == POI:
            summary += f" {self.get_description()}"

        return summary

    def __str__(self) -> str:
        name = self.get_reference(NAME)

        if name and type(name) == str:
            return name
        
        if self.Nodetype and self.ID:
            return f"{self.Nodetype}({self.ID})"
        
        return ""

    def knows_about(self: SimulaeNode, node: SimulaeNode):
        logAll("knows_about(",node,")")

        knows_about = False

        if node.Nodetype in SOCIAL_NODE_TYPES:
            if self.has_relation(node.ID, node.Nodetype) or self.has_relationship(node.ID, node.Nodetype): # already has relationship
                knows_about = True

        elif node.Nodetype in INANIMATE_NODE_TYPES:
            
            if self.has_relation(node.ID, node.Nodetype): # already has relationship
                knows_about = True

        logAll("-> ",knows_about)
        return knows_about

    def get_reference(self, key: str) -> str | None:
        logAll("get_reference(",key,")")
        
        if key in self.References:
            return self.References[key]

        return None

    def set_reference(self: SimulaeNode, 
                      key: str | None, 
                      value: str | None, 
                      warn: bool = True):
        logAll("set_reference(",key,value,")")

        if not key:
            raise ValueError("Reference key cannot be None or empty")
        
        if not value:
            raise ValueError("Reference value cannot be None or empty")

        if self.References == None or type(self.References) != dict:
            if warn:
                logWarning("References dictionary is invalid! -> initializing to empty dict")
            self.References = {}

        self.References[key] = value # type: ignore

    # Attributes Section

    def get_attribute(self: SimulaeNode, key: str) -> int | float | None:
        logAll("get_attribute(",key,")")

        if not key:
            return None

        attribute = None

        if key in self.Attributes:
            attribute = self.Attributes[key]

        if type(attribute) in [int, float]:
            return attribute
        
        return attribute

    def get_attribute_int(self: SimulaeNode, key: str) -> int | None:
        logAll("get_attribute_int(",key,")")

        attribute = self.get_attribute(key)

        if type(attribute) == int:
            return attribute
        
        return None

    def set_attribute(self: SimulaeNode, 
                      key: str, 
                      value: int | float,
                      warn: bool = True):
        logAll("set_attribute(",key,", ",value,")")

        if key in self.Attributes and \
            type(self.Attributes[key]) != type(value) \
            and warn:
            logWarning(f"Warning: Overwriting attribute '{key}' of type {type(self.Attributes[key])} with value of type {type(value)}")

        self.Attributes[key] = value

    # Relations Section

    def determine_relation(self: SimulaeNode, node: SimulaeNode, interaction=None) -> dict | None:
        '''
        Calculates 'Relation' (Physical Relation) between self and given node
        
        :param self: Description
        :param node: Description
        :param interaction: Description
        :return: Description
        :rtype: Literal['Perfectly Aligned']
        '''

        logAll("determining",self,"(physical) relation to",node)

        relationship = {}

        for relation_type in RELATION_TYPES:
            relation_bucket = self.Relations.get(relation_type)

            if not relation_bucket:
                continue

            node_bucket = relation_bucket.get(node.Nodetype)
            if not node_bucket:
                continue

            if node.ID in node_bucket: # existing relationship found
                return node_bucket[node.ID]

        return None

    def determine_relationship(self: SimulaeNode, node: SimulaeNode, interaction=None):
        '''
        Calculates 'Relationship' (Social Relation) between self and given node
        
        :param self: Description
        :param node: Description
        :param interaction: Description
        :return: Description
        '''

        logAll("determining",self,"social relationship with",node)

        relationship = {
            NODETYPE : node.Nodetype,
            STATUS : "new",
            REPUTATION : [0,0],
            INTERACTIONS : []
        }

        if self.has_relationship(node.ID, node.Nodetype): # existing relationship
            relationship = self.Relations.get(node.Nodetype, {}).get(node.ID, relationship)

            # update existing relationship ?

            return relationship

        else: # new relationship
            if node.Nodetype in SOCIAL_NODE_TYPES: # other node is a social node

                if self.Nodetype in SOCIAL_NODE_TYPES: # self -> social nodetype

                    for scale in [POLICY_SCALES, PERSONALITY_SCALES]:

                        scale_name: str = scale['name']

                        if scale_name not in self.Scales:
                            logWarning(f"Node {self} missing scale '{scale_name}' for relationship calculation")
                            continue

                        if scale_name not in node.Scales:
                            logWarning(f"Node {node} missing scale '{scale_name}' for relationship calculation")
                            continue

                        self_scale = self.get_scale(scale_name)

                        if not self_scale:
                            logWarning(f"Node {self} has no values for scale '{scale_name}' for relationship calculation")
                            continue

                        node_scale = node.get_scale(scale_name) 

                        if not node_scale:
                            logWarning(f"Node {node} has no values for scale '{scale_name}' for relationship calculation")
                            continue

                        scale_diff = get_scale_diff(
                            master_scale=scale['scales'], 
                            scale=self_scale, 
                            comparison_scale=node_scale,
                            descriptors=scale['strength_descriptors'],
                            descriptors_buckets=scale['descriptors_buckets'],
                            scale_center_index=scale['center_index'])


                    relationship[scale_name] = scale_diff # type: ignore
                    #relationship[POLICY_DISPOSITION] = self.get_policy_disposition( scale_diff[0] )

                    return relationship

                # self -> inanimate nodetype

                return relationship

            elif node.Nodetype in INANIMATE_NODE_TYPES: # other node is an inanimate node
                return relationship
        
    def update_relation(self: SimulaeNode, node: SimulaeNode, interaction=None) -> dict | None:
        '''
        Update the (physical) relation between self and given node
        
        :param self: Description
        :type self: SimulaeNode
        :param node: Description
        :type node: SimulaeNode
        :param interaction: Description
        :return: Description
        :rtype: dict[Any, Any] | None
        '''
        
        logAll("update_relation(",node,")")
        
        if not node:
            raise ValueError
        
        for relation_type in PHYSICAL_RELATIVE_TYPES:
            relation_bucket = self.Relations.get(relation_type)

            if not relation_bucket or node.Nodetype not in relation_bucket:
                logWarning(f"Node {self} has no relation type '{relation_type}' in its Relations dictionary")
                continue

            if node.ID in relation_bucket[node.Nodetype]: # existing relationship found
                relationship = relation_bucket[node.Nodetype][node.ID]

                determined_relationship = self.determine_relation(node, interaction)

                if determined_relationship:
                    relation_bucket[node.Nodetype][node.ID] = determined_relationship
                    return determined_relationship

                # no existing relation found 

    def get_relation(self: SimulaeNode, node: SimulaeNode) -> dict | None:
        '''
        Returns Physical relation to given node, if known. Otherwise, 'None'
        
        :param self: Description
        :param node: Description
        :return: Description
        '''

        logAll("get_relation(",node,")")

        relation_type = self.has_relation(node.ID, node.Nodetype)

        if relation_type:
            return self.Relations.get(relation_type, {}).get(node.Nodetype, {}).get(node.ID)
        
        node_bucket = self.Relations.get(node.Nodetype, {})
        if node.ID in node_bucket:
            return node_bucket[node.ID]    

        return None
    
    def get_relation_by_ID(self: SimulaeNode, node_id: str) -> 'SimulaeNode | None':
        logAll("get_relation_by_ID(",node_id,")")

        for relation_type in self.Relations:

            for nodetype in self.Relations[relation_type]:

                if node_id in self.Relations[relation_type][nodetype]: # existing relationship found
                    return self.Relations[relation_type][nodetype][node_id]
            
        return None
        
    # def get_relations_by_nodetype(self: SimulaeNode, nodetype: str) -> dict | None:
    #     logDebug("get_relations_by_nodetype(",nodetype,")")

    #     if nodetype in PHYSICAL_RELATIVE_TYPES:
    #         relations = {}

    #         if nodetype in self.Relations:
    #             relations[nodetype] = self.Relations[nodetype]
                
    def get_relation_by_nodetype_and_ID(self: SimulaeNode, nodetype: str, nid: str) -> 'SimulaeNode | None':
        logAll("get_relation_by_nodetype_and_ID(",nodetype,",",nid,")")

        for relation_type in self.Relations:

            for node_type in self.Relations[relation_type]:

                if self.Relations[relation_type][node_type].get(nid): # existing relationship found
                    return self.Relations[relation_type][node_type][nid]
    
    def get_relations_by_type(self: SimulaeNode, relation_type: str) -> dict | None:
        logAll("get_relations_by_type(",relation_type,")")

        if relation_type in self.Relations:
            return self.Relations[relation_type]
    
    def get_relations_by_relation_type_and_nodetype(self: SimulaeNode, relation_type: str, nodetype: str) -> dict | None:
        logAll("get_relations_by_relation_type_and_nodetype(",relation_type,", ",nodetype,")")

        if relation_type in self.Relations and nodetype in self.Relations[relation_type]:
            return self.Relations[relation_type][nodetype]

        return None
    
    def add_relation(self: SimulaeNode, node: SimulaeNode, relation_type: str = CONTENTS, warn: bool = True):
        '''
        Sets physical relation to given node, if valid.
        
        :param self: Description
        :type self: SimulaeNode
        :param node: Description
        :type node: SimulaeNode
        :param relation_type: Description
        :type relation_type: str
        :return: `True` if relation was successfully set, `False` if not (e.g. invalid relation type or node)
        :rtype: bool
        '''

        logAll("add_relation(",node,", ",relation_type,")")

        if relation_type not in PHYSICAL_RELATIVE_TYPES:
            if warn:
                logWarning(f"Invalid relation type '{relation_type}'. Must be one of {PHYSICAL_RELATIVE_TYPES}")
            return False

        relation_bucket = self.Relations.get(relation_type, {})
        node_bucket = relation_bucket.get(node.Nodetype, {})

        if node_bucket.get(node.ID): # existing relationship found
            return False

        return self.set_relation(node, relation_type)

    def set_relation(self: SimulaeNode,
                     node: SimulaeNode, 
                     relation_type: str = CONTENTS, 
                     warn: bool = True) -> bool:
        '''
        Sets physical relation to given node, if valid.
        
        :param self: Description
        :type self: SimulaeNode
        :param node: Description
        :type node: SimulaeNode
        :param relation_type: Description
        :type relation_type: str
        :return: `True` if relation was successfully set, `False` if not (e.g. invalid relation type or node)
        :rtype: bool
        '''

        logAll("set_relation(",node,")")

        if relation_type not in PHYSICAL_RELATIVE_TYPES:
            if warn:
                logWarning(f"Invalid relation type '{relation_type}'. Must be one of {PHYSICAL_RELATIVE_TYPES}")
            return False

        relation_bucket = self.Relations.setdefault(relation_type, {})
        node_bucket = relation_bucket.setdefault(node.Nodetype, {})

        try: 
            node_bucket[node.ID] = node
        except Exception as e:
            if warn:
                logWarning('Error in set_relation:', str(e))
            return False
        
        return True

    def get_relations_by_criteria(self: SimulaeNode, criteria, relation_types: list[str] | tuple[str, ...] | None = None):
        """Return physical relations that match a loose search criteria.

        Criteria can be a string, a `SimulaeNode`, or a dictionary of field
        matches. This is intentionally forgiving so task planning can search by
        fuzzy labels like `"food"` or structured selectors like `{NAME: "food"}`.
        """

        logAll("get_relations_by_criteria(",criteria,")")

        if not criteria:
            return []

        if relation_types is None:
            relation_types = tuple(self.Relations.keys())

        def values_match(candidate_value, expected_value):
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
                return all(values_match(candidate_value.get(key), value) for key, value in expected_value.items())

            if isinstance(expected_value, (list, tuple, set)):
                return any(values_match(candidate_value, value) for value in expected_value)

            expected_text = normalize_str(str(expected_value)).casefold()
            candidate_text = normalize_str(str(candidate_value)).casefold()
            return candidate_text == expected_text

        def node_matches(candidate: SimulaeNode) -> bool:
            if isinstance(criteria, SimulaeNode):
                if criteria.Nodetype and candidate.Nodetype != criteria.Nodetype:
                    return False

                criteria_name = criteria.get_reference(NAME)
                candidate_name = candidate.get_reference(NAME)

                # Treat ID or NAME as a valid anchor so callers can pass either
                # an exact node or a named template.
                if criteria.ID and candidate.ID == criteria.ID:
                    return True

                if criteria_name and candidate_name and normalize_str(candidate_name).casefold() == normalize_str(criteria_name).casefold():
                    return True

                if criteria.ID and criteria_name:
                    return False

                if criteria.ID and candidate.ID != criteria.ID:
                    return False

                if criteria_name and normalize_str(candidate_name).casefold() != normalize_str(criteria_name).casefold():
                    return False

                return True

            if isinstance(criteria, str):
                criteria_text = normalize_str(criteria).casefold()

                candidate_strings = [
                    candidate.ID,
                    candidate.Nodetype,
                    candidate.get_reference(NAME),
                ]
                candidate_strings.extend(candidate.References.values())
                candidate_strings.extend(candidate.Attributes.values())
                candidate_strings.extend(candidate.Checks.keys())
                candidate_strings.extend(candidate.Checks.values())

                for candidate_value in candidate_strings:
                    if candidate_value is None:
                        continue
                    if normalize_str(str(candidate_value)).casefold() == criteria_text:
                        return True
                return False

            if isinstance(criteria, dict):
                for key, expected_value in criteria.items():
                    if key == ID:
                        if not values_match(candidate.ID, expected_value):
                            return False
                        continue

                    if key == NODETYPE:
                        if not values_match(candidate.Nodetype, expected_value):
                            return False
                        continue

                    if key == NAME:
                        if not values_match(candidate.get_reference(NAME), expected_value):
                            return False
                        continue

                    if key == REFERENCES:
                        if not values_match(candidate.References, expected_value):
                            return False
                        continue

                    if key == ATTRIBUTES:
                        if not values_match(candidate.Attributes, expected_value):
                            return False
                        continue

                    if key == CHECKS:
                        if not values_match(candidate.Checks, expected_value):
                            return False
                        continue

                    if key == ABILITIES:
                        if not values_match(candidate.Abilities, expected_value):
                            return False
                        continue

                    # Fall back to direct lookups across the node's primary
                    # data buckets so callers can search with loose selectors.
                    if key in candidate.References:
                        if not values_match(candidate.References.get(key), expected_value):
                            return False
                        continue

                    if key in candidate.Attributes:
                        if not values_match(candidate.Attributes.get(key), expected_value):
                            return False
                        continue

                    if key in candidate.Checks:
                        if not values_match(candidate.Checks.get(key), expected_value):
                            return False
                        continue

                    if key in candidate.Abilities:
                        if not values_match(candidate.Abilities.get(key), expected_value):
                            return False
                        continue

                    return False

                return True

            return values_match(candidate, criteria)

        matches = []
        seen_ids = set()

        for relation_type in relation_types:
            nodetype_lookup = self.Relations.get(relation_type, {})

            for nodes in nodetype_lookup.values():
                for candidate in nodes.values():
                    if candidate and candidate.ID not in seen_ids and node_matches(candidate):
                        seen_ids.add(candidate.ID)
                        matches.append(candidate)

        return matches
    
    def get_relation_type(self: SimulaeNode, node: SimulaeNode) -> str | None:
        logAll("get_relation_type(",node,")")

        for relation_type in PHYSICAL_RELATIVE_TYPES:
            relation_bucket = self.Relations.get(relation_type, {})
            node_bucket = relation_bucket.get(node.Nodetype, {})

            if node.ID in node_bucket: # existing relationship found
                return relation_type

    def has_relation_to( self: SimulaeNode, node: SimulaeNode ) -> bool:
        logAll("has_relation_to(",node,")")

        return self.has_relation(node.ID, node.Nodetype) is not None

    def has_relation( self: SimulaeNode, node_id: str, nodetype: str ) -> str | None:
        '''
        Determines if self has a physical relation to the given node ID and nodetype
        
        :param self: Description
        :type self: SimulaeNode
        :param node_id: Description
        :type node_id: str
        :param nodetype: Description
        :type nodetype: str
        :return: If a relation exists, the relation type (RELATIVE_TYPES). Otherwise, 'None'
        :rtype: str | None
        '''

        logAll("has_relation(",node_id,", ",nodetype,")")

        for relation_type in PHYSICAL_RELATIVE_TYPES:

            relations_by_type = self.get_relations_by_type(relation_type)

            if relations_by_type and nodetype in relations_by_type:
                if node_id in relations_by_type[nodetype]:
                    return relation_type

    
    def has_relationship( self: SimulaeNode, key: str, nodetype: str ):
        logAll("has_relationship(",key,", ",nodetype,")")

        return key in self.Relations.get(nodetype, {})
    
    # Relations Section - Location and Adjacency

    def get_location(self: SimulaeNode) -> str | None:
        logAll("get_location()")

        return self.get_reference(LOC)
    
    def set_location(self: SimulaeNode, 
                     location_node: SimulaeNode, 
                     warn: bool = True) -> bool:
        logAll("set_location(",location_node,")")

        if location_node.Nodetype != LOC:
            if warn:
                logWarning("Invalid location node type '{0}'. Must be '{1}'".format(location_node.Nodetype, LOC))
            return False

        self.set_reference(LOC, location_node.ID)

        return True

    def set_location_by_ID(self: SimulaeNode, location_id: str):
        logAll("set_location_by_ID(",location_id,")")

        self.set_reference(LOC, location_id)

    def get_adjacent_locations(self: SimulaeNode) -> list[SimulaeNode] | None:
        logAll("get_adjacent_locations()")

        adjacent_locations = self.get_relations_by_relation_type_and_nodetype(ADJACENT, LOC)
        
        if not adjacent_locations:
            return []
        
        return list(adjacent_locations.values())

    def add_adjacent_location(self: SimulaeNode, loc: SimulaeNode, reciprocate=True):
        logAll("add_adjacent_location(",loc,")")

        # check if loc is already an adjacent location

        if self.has_relation(loc.ID, loc.Nodetype):
            logAll("Location is already adjacent")
            return  
        
        # add adjacent relation

        self.set_relation(loc, relation_type=ADJACENT)

    # Checks Section

    def set_check(self: SimulaeNode, 
                  key: str, 
                  value: bool,
                  warn: bool = True):
        logAll("set_check(",key,", ",value,")")

        if not key:
            if warn:
                logWarning("Check key cannot be None or empty")
            return

        self.Checks[key] = value

    def has_check(self: SimulaeNode, key: str) -> bool:
        logAll("has_check(",key,")")

        if not key:
            return False

        return key in self.Checks

    def get_check(self: SimulaeNode, key:str):
        logAll("get_check(",key,")")

        if key in self.Checks:
            return self.Checks[key]
        
        return None

    def remove_check(self: SimulaeNode, 
                     key:str, 
                     warn: bool = True):
        logAll("remove_check(",key,")")

        if not key:
            if warn:
                logWarning("Check key cannot be None or empty")
            return

        if key in self.Checks:
            del self.Checks[key]

    # Scales Section

    def generate_policy(self, use_rng: bool = True):
        logAll("generate_policy()")

        return generate_values_for_scales(POLICY_SCALE, scale_strength_range=POLICY_STRENGTH_RANGE, use_rng=use_rng)
        
    def generate_personality(self, use_rng: bool = True) -> dict:
        logAll("generate_personality()")

        return generate_values_for_scales(PERSONALITY_SCALE, scale_strength_range=PERSONALITY_STRENGTH_RANGE, use_rng=use_rng)
    
    def get_scale(self, scale_name: str) -> dict | None:
        if self.Nodetype == POI:

            if scale_name in self.Scales:
                return self.Scales[scale_name]
            
        return None
    
    def get_political_beliefs(self) -> dict | None:
        return self.get_scale(POLICY)

    def get_personality(self) -> dict | None:
        return self.get_scale(PERSONALITY)

    def get_policy_disposition(self, policy_diff_value):
        logAll("get_policy_disposition(",policy_diff_value,")")

        if policy_diff_value < 0:
            raise ValueError

        # TODO AE: Move descriptions to config
        elif policy_diff_value <= 10:
            return "Friendly"
        elif policy_diff_value < 20:
            return "Neutral"
        elif policy_diff_value >= 20:
            return "Hostile"
        '''    
        elif policy_diff_value == 0:
            return "Perfectly Aligned"
        elif policy_diff_value < 5:
            return "Aligned"
        elif policy_diff_value < 10:
            return "Neutral"
        elif policy_diff_value < 15:
            return "Opposed"
        elif policy_diff_value < 20:
            return "Strongly Opposed"
        elif policy_diff_value > 20:
            return "Diametrically Opposed"
        '''

    def get_social_disposition(self, social_diff_value):
        logAll("get_social_disposition(",social_diff_value,")")

        if social_diff_value < 0:
            raise ValueError

        # TODO AE: Move descriptions to config
        elif social_diff_value <= 10:
            return "Friendly"
        elif social_diff_value < 20:
            return "Neutral"
        elif social_diff_value >= 20:
            return "Hostile"
        
    def policy_diff( self, 
                    compare_policy: dict, 
                    warn: bool = True ):
        self_policy = self.get_political_beliefs()
        
        if not self_policy or not compare_policy:
            if warn:
                logWarning("One or both nodes missing political beliefs scale for policy_diff calculation")
            return None
        
        return get_scale_diff( POLICY_SCALE, self_policy, compare_policy, SOCIAL_DIFFERENTIAL_DESCRIPTORS, [3, 5, 8, 13, 21, 34], 3)
    
    def social_diff( self: SimulaeNode, 
                    compare_personality: dict, 
                    warn: bool = True):
        self_personality = self.get_personality()

        if not self_personality or not compare_personality:
            if warn:
                logWarning("One or both nodes missing personality scale for social_diff calculation")
            return None

        return get_scale_diff( PERSONALITY_SCALE, self_personality, compare_personality, SOCIAL_DIFFERENTIAL_DESCRIPTORS, [3, 5, 8, 13, 21, 34], 3)
    
    def describe_political_beliefs(self, 
                                   warn: bool = True):
        logAll("describe_political_beliefs()")

        summary = ""

        if POLICY not in self.References:
            return ""

        politics = self.References[POLICY]

        if not politics:
            if warn:
                logWarning("No political beliefs scale found in references for node {0}".format(self))
            return ""

        for policy, (stance_index, strength) in politics.items():
            if policy not in POLICY_SCALE:
                continue

            if stance_index == 3:  # Indifferent
                continue

            descr = POLICY_BELIEF_STRENGTH_DESCRIPTORS[strength-1]

            stance_descr = POLICY_SCALE[policy][stance_index]

            summary += f"{policy:<18} | {descr} {stance_descr}\n"

        return summary
    
    def describe_personality(self, 
                             warn: bool = True):
        logAll("describe_personality()")

        if PERSONALITY not in self.References:
            return ""
        
        summary = ""

        personality = self.get_scale(PERSONALITY)

        if not personality:
            if warn:
                logWarning("No personality scale found in references for node {0}".format(self))
            return ""

        for trait, (trait_index, strength) in personality.items():
            if trait not in PERSONALITY_SCALE:
                continue

            descr = PERSONALITY_TRAIT_STRENGTH_DESCRIPTORS[strength-1]

            trait_descr = PERSONALITY_SCALE[trait][trait_index]

            summary += f"""{trait:<18} | {descr} {trait_descr}\n"""
        return summary

    def describe_faction_associations(self):
        logAll("describe_faction_associations()")

        summary = ""

        if FAC not in self.References:
            return ""
        
        for sid, relationship in self.Relations.get(FAC, {}).items():

            summary += f"{sid} {relationship[STATUS]}, "

        return summary

    def toJSON(self: SimulaeNode) -> dict:
        logAll(f"toJSON({self.ID, self.References.get(NAME)})")

        try:

            # break SimulaeNode down into JSON-serializable dict
            d = self.__dict__

            # Process Relations sub-items, containing nested SimulaeNodes, into JSON-serializable dicts    
            
            for relation_type, nodetype_lookup in self.Relations.items():
                logAll("Processing relation type:", relation_type)
                physical_relation_lookup = {}

                for nodetype, nodes in nodetype_lookup.items():
                    
                    if not nodes:
                        continue

                    logAll("\tProcessing nodetype:", nodetype)

                    nodetype_relation_lookup = {}

                    if relation_type == ADJACENT and nodetype != LOC:
                        nodetype_relation_lookup = { node_id: node_id for node_id, node in nodes.items() }
                        continue

                    for node_id, node in nodes.items():
                        logAll("\t\tProcessing node:", relation_type, nodetype, node)

                        if hasattr(node, 'toJSON'):
                            nodetype_relation_lookup[node_id] = node.toJSON()
                        else:
                            nodetype_relation_lookup[node_id] = node
                    
                    physical_relation_lookup[nodetype] = nodetype_relation_lookup

                d[RELATIONS][relation_type] = physical_relation_lookup


            # Process References
            for k,v in self.References.items():
                d[REFERENCES][k] = v

            return d

        except Exception as e:
            print("ERROR WHILE SAVING", type(e), str(e))
            return {}

def simulaenode_from_json(data: dict):
    try:

        if type(data) != type({}):
            raise ValueError(f"from_json | invalid data type: {type(data)}")

        keys = list(data.keys())

        n_id = data[ID] if ID in keys else None
        n_type = data[NODETYPE] if NODETYPE in keys else None
        n_refs = data[REFERENCES] if REFERENCES in keys else {}
        n_attr = data[ATTRIBUTES] if ATTRIBUTES in keys else {}
        n_rels = data[RELATIONS] if RELATIONS in keys else {}
        n_checks = data[CHECKS] if CHECKS in keys else {}
        n_abilities = data[ABILITIES] if ABILITIES in keys else {}
        n_scales = data[SCALES] if SCALES in keys else {}
        n_memory = data[MEMORY] if MEMORY in keys else {}

        if not n_id or not n_type:
            print(f"ERROR | from_json | missing ID or NODETYPE in data: {data}")
            raise ValueError(f"Cannot determine ID or nodetype of entity |\n {data}")

        relations = { nt:{} for nt in ALL_NODE_TYPES }
        for ntype, nodes in n_rels.items():
            logAll(ntype)
            for nid, ndata in nodes.items():
                node = simulaenode_from_json(ndata)
                
                if node:
                    logAll(f"-> {node.ID}")
                    relations[ntype][node.ID] = node
                else:
                    logError(f"Failed to parse node with id {nid} and nodetype {ntype} in relations of node with id {n_id}")
                    pass

        n = SimulaeNode(
            given_id=n_id, 
            nodetype=n_type, 
            references=n_refs, 
            attributes=n_attr, 
            relations=relations, 
            checks=n_checks, 
            abilities=n_abilities,
            scales=n_scales,
            memory=n_memory)
    
        return n   

    except Exception as e:
        logError('Encountered exception while attempting to load SimulaeNode from JSON')
        logError(e)     

    return None
