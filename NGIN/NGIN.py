import sys, os, random

from NGIN.implementation.lib.SimulaeNode import *
from NGIN.utilities.lib.ngin_utils import (
    load_json_from_file,
    save_json_to_file,
    logAll,
    logDebug,
    logError,
    logInfo,
    logWarning,
)
from NGIN.utilities.lib.ngin_console_utils import user_choice, robust_int_entry
from NGIN.utilities.lib.ngin_console_log import WORLD_GEN_POPULATION_GROUP_CHANCE, WORLD_GEN_STICKINESS
from NGIN.NGIN_config.madlibs import (
    FACTION_TYPES,
    MADLIBS_NOUNS,
    MADLIBS_SUFFIXES,
    POLICY_SCALE,
    PRESET_POLICIES,
)
from NGIN.NGIN_config.ngin_missions import NGIN_MISSIONS

class NGIN():

    def __init__(self, mission_struct, settings, save_file=None, is_console=True, generate=True):
        
        if not mission_struct or mission_struct == None:
            raise ValueError("Missing required data: mission_struct")

        if not settings or settings == None:
            raise ValueError("Missing required data: settings")

        self.mission_struct = mission_struct
        self.settings = settings
        self.state = SimulaeNode(
                        "state",        # id
                        "state",             # nodetype
                        {},             # references
                        {},
                        {               # relations
                            FAC:{},
                            PTY:{},
                            POI:{},
                            OBJ:{},
                            LOC:{}
                        },
                        {},
                        {}
                    )

        self.world_root = None
        self.taken_names = []
        self.is_console = is_console

        try:
            if save_file:
                self.import_world(save_file)
        except Exception as e:
            logError(f'Unable to import world data from save file | {e}')

        if not self.state.Relations or not self.state.References and generate:
            logWarning('No world data... generating...')
            self.generate_new_world()

        self.print_location_map()

    def start(self):

        if self.is_console:
            self.start_console()


    def import_world(self, save_file):
        logInfo('importing world data...')
        self.state = simulaenode_from_json(save_file)


    def save_to_file(self, filename: str):
        logAll(f"save_to_file( filename: {filename} )")

        if not self.state:
            raise ValueError("No state to save")

        data = self.state.toJSON()

        save_json_to_file(filename, data, pretty=True)


    def start_console(self):
        ''' Iterates through the game state generating missions based on
                available nodes in the state.
        '''

        actor = self.get_simulae_node_by_id(self.select_actor(randomized=True), POI)

        if not actor:
            logError("Selected actor not found in state!")
            return

        print("You are -> ",actor)
        print(actor.get_description())

        while True:

            #os.system('clear') # clear screen

            #self.validate_state()

            #self.display_state()

            options = self.get_actions(actor=actor)

            mission = self.select_action(options, actor)

            self.resolve_action(actor, mission)

            cmd = input('continue [enter] / [q]uit ?> ')
            if cmd in ['q','quit']:
                sys.exit(0) 


    def select_actor(self, randomized=False):
        logDebug(f"select_actor( randomized: {randomized} )")

        if not self.state:
            raise ValueError("State not initialized")

        actor_nodes = self.state.get_relations_by_relation_type_and_nodetype(CONTENTS, POI)

        if not actor_nodes:
            raise Exception("No actor nodes found in state...")

        options = { node.summary():nid for nid, node in actor_nodes.items()}

        if not options:
            raise Exception("No POI nodes to select from...")

        if not randomized:
            print("Select actor node: (Choose your character)")
            selected_node = user_choice( user_options=list(options.keys()), random_opt=True )
        else:
            selected_node = random.choice(list(options.keys()))

        # return the actor node id
        return options[selected_node]


    def generate_new_world(self):

        logInfo('generating new world')

        # generate networked map of locations

        # small, medium, or large?
       
        self.world_root = generate_simulae_node(LOC, self.get_new_name())

        logInfo('Attach world root: ', self.world_root)
        self.add_loc_to_world(self.world_root)

        world_size = self.settings['world_size']
        lo, hi = self.settings['world_sizes'][world_size]

        num_world_locs = random.randrange(lo, hi)

        for i in range(num_world_locs):
            loc = self.generate_location()

            self.attach_loc(loc)
            

    def print_location_map(self):
        
        if not self.state:
            raise ValueError("State not initialized")

        locations = self.state.get_relations_by_relation_type_and_nodetype(CONTENTS, LOC)

        if not locations:
            logWarning("No locations found in state...")
            return

        loc_map = {}

        for loc_id, loc_node in locations.items():
            
            print(f"{loc_node.Nodetype} {loc_node.References[NAME]}")
            loc_map[loc_id] = loc_node.get_adjacent_locations()

            for adjacent in loc_map[loc_id]:
                print(f"\tLOC {adjacent.get_reference(NAME)}")

        return loc_map

    def get_simulae_node_by_id(self, nid: str, nodetype: str | None = None) -> 'SimulaeNode | None':
        logDebug(f"get_simulae_node_by_id( nid: {nid}, nodetype: {nodetype} )")

        if not self.state:
            raise ValueError("State not initialized")

        if not nid:
            raise ValueError("'nid' cannot be null/empty")

        if not nodetype:

            # search all nodetypes for this id and return the first match (should be unique across all nodetypes)

            return self.state.get_relation_by_ID(nid)

        else:
            return self.state.get_relation_by_nodetype_and_ID(nodetype, nid)

    def attach_loc(self, new_loc: SimulaeNode):

        if not self.state:
            raise ValueError("State not initialized")
        
        if not self.world_root: 
            logError("No world root found to attach location to!")
            return

        # get 'stickiness' setting -> chance to attach to 'current' node
        stickiness = WORLD_GEN_STICKINESS

        # add to world
        self.add_loc_to_world(new_loc)

        visited = [] 
        nodes = [self.world_root]
        
        while nodes:

            loc_node = nodes.pop()

            if not loc_node:
                logWarning("Node not found in state while attaching location!")
                continue

            visited.append(loc_node.ID)

            adjacent_locations = loc_node.get_adjacent_locations()

            # check if this location can accept more adjacent locations based on its 'max_adjacent_locations' attribute
            max_adjacent_locations = loc_node.get_attribute_int('max_adjacent_locations')
        
            if not adjacent_locations: # no adjacent locations

                if max_adjacent_locations and max_adjacent_locations > 0:
                    
                    # attach here
                    if random.random() < stickiness:
                        loc_node.add_adjacent_location(new_loc) # attach to current location
                        #new_loc.add_adjacent_location(loc_node)
                        return # attached!

                # no adjacent locations and no max limit specified. Skip along

            else: # has adjacent locations

                # filter visited nodes to prevent infinite loop due to circular references
                adjs = [ adj for adj in adjacent_locations if adj.ID not in visited ]   

                if random.random() < stickiness:
                    loc_node.add_adjacent_location(new_loc) # attach to current location
                    #new_loc.add_adjacent_location(loc_node)
                    return # attached!
                
                if not adjs and not nodes:
                    loc_node.add_adjacent_location(new_loc) # attach to current location
                    #new_loc.add_adjacent_location(loc_node)
                    return # attached!

                # not attached
                nodes = nodes + adjs # add adjacent locations to 'nodes-to-visit'
                
    def generate_location(self):

        # single-feature-location or multi-location (2-6)

        location = generate_simulae_node(LOC, self.get_new_name())

        # generate feature(s)?

        # generate population
        population, faction = self.generate_population(location)

        for entity in population:

            self.add_node_to_world(entity)

            # set entity's location
            entity.set_location_by_ID(location.ID)

            if faction: # set faction ownership of location
                location.set_reference(FAC, faction.ID)

        return location


    def generate_population(self, location):

        # individual or group?

        population = []
        faction = None

        if random.random() < WORLD_GEN_POPULATION_GROUP_CHANCE:
            population, faction = self.generate_group(location)
            
        else:
            population = [self.generate_individual(location)]

        return population, faction


    def generate_group(self, location):
        logAll("generate_group( location: ", location.summary(), " )")

        # generate new faction
        faction = self.generate_faction()
        self.add_node_to_world(faction)

        # small medium or large? -> generate more individuals
        group_size = random.choice( list(self.settings['groups'].keys()) )

        lo, hi = int(self.settings['groups'][group_size][0]), int(self.settings['groups'][group_size][1])
        num_individuals = random.randrange(lo, hi)

        logAll(f"Generating group of size {num_individuals}")

        group = []
        for i in range(num_individuals):
            individual = self.generate_individual(location, faction)

            # update individual's relation to faction
            #individual.update_relation(faction, interaction="Join")

            #individual.References[FAC] = faction.ID

            #individual.add_reference(FAC, faction.ID)
            #individual.update_relation(faction)

            group.append(individual)

        return group, faction


    def generate_individual(self, location, faction=None):
        logAll("generate_individual( location: ", location.summary(), ", faction: ", faction.summary() if faction else None, " )")

        individual = generate_person_simulae_node(self.get_new_name(), include_body=False)

        individual.set_location(location)
        
        return individual
    
    def add_loc_to_world(self, loc: SimulaeNode):
        logAll(f"add_loc_to_world( loc: {loc.summary()} )")

        if not self.state:
            raise ValueError("State not initialized")
        
        if loc.Nodetype != LOC:
            raise ValueError(f"Expected nodetype 'LOC', got '{loc.Nodetype}'")

        self.state.set_relation(loc, relation_type=CONTENTS)

        name = loc.get_reference(NAME)

        if name:
            if self.taken_names and name not in self.taken_names:
                self.taken_names.append(name)

        current_num_locs = self.state.get_attribute_int('num_locations')

        if not current_num_locs:
            current_num_locs = 0

        self.state.set_attribute('num_locations', current_num_locs + 1)

        if 'LOC_num' not in self.state.Attributes:
            self.state.Attributes['LOC_num'] = 0

        self.state.Attributes['LOC_num'] += 1

    def add_node_to_world(self, node: SimulaeNode):
        logAll(f"add_node_to_world({node.summary()})")

        if not self.state:
            raise ValueError("State not initialized")
        
        self.state.set_relation(node, relation_type=CONTENTS)

        name = node.get_reference(NAME)

        if name:
            if self.taken_names and name not in self.taken_names:
                self.taken_names.append(name)


    def generate_faction(self):
        logAll("generate_faction()")
        
        # choose organization subtype
        orgtype = random.choice(FACTION_TYPES)
        
        # madlibs name generation
        name = random.choice(MADLIBS_NOUNS) + ('-'+random.choice(MADLIBS_NOUNS) if random.random() >= 0.6 else '' )
        suffix = random.choice(MADLIBS_SUFFIXES[orgtype]) if random.random() >= 0.1 else ''
        name += ' '+suffix
        # acronym for quick/short reference (display purposes)
        acronym = ''.join( [ l for l in name if l.isupper() ] )

        # fix this
        faction = generate_simulae_node(FAC, name)
        faction.set_reference('Acronym', acronym)

        return faction


    def generate_policy(self, orgtype=None):
        logAll(f"generate_policy( orgtype: {orgtype} )")

        policies = POLICY_SCALE

        if orgtype:
            policies = PRESET_POLICIES[orgtype]

        policy = {}

        for k,v in policies.items():
            #               position            weight
            stance_index = random.randint(0, len(v)-1)
            strength = random.randint(1,7)
            policy[k] = (stance_index, strength)

        return policy


    def get_new_name(self):
        logAll("get_new_name()")

        name = random.choice( MADLIBS_NOUNS )

        if not self.taken_names:
            self.taken_names = []        

        while name and name in self.taken_names and len(self.taken_names) < len(MADLIBS_NOUNS):
            name = random.choice( MADLIBS_NOUNS )
    
        self.taken_names.append(name)

        return name


    def generate_element( self, nodetype ):
        logAll(f"generate_element( nodetype: {nodetype} )")
        ''' creates a new node with random attributes ''' 

        name = self.get_new_name()
        nodetype = random.choice( PHYSICAL_NODETYPES ) if not nodetype else nodetype
        references = {}
        attributes = {}
        relations  = {}
        checks     = {}
        abilities  = {}

        # id, nodetype, refs, attrs, reltn, checks, abilities
        return SimulaeNode( name, nodetype, references, attributes, relations, checks, abilities )
            

    def nodes_are_adjacent(self, node1, node2):
        logAll(f"nodes_are_adjacent( node1: {node1.summary()}, node2: {node2.summary()} )")

        loc1 = node1.get_reference(LOC)
        loc2 = node2.get_reference(LOC)

        if loc1 == loc2:
            return True

        return False


    def get_actions(self, actor):        
        logAll(f"get_actions( actor: {actor.summary()} )")

        # handle inanimates
        if actor.Nodetype not in SOCIAL_NODE_TYPES:
            return []

        options = []

        # evaluate immediate options:

        # current location / adjacent entities
        actor_loc = actor.get_reference(LOC)

        loc = self.get_simulae_node_by_id(actor_loc, LOC)

        if loc:

            logAll('Current Location:',loc.ID)
            options.append(self.get_actions_for_node(actor, loc, note="current location"))

            # same location?
            adjacents = loc.get_adjacent_locations()

            if adjacents:
                for adj in adjacents:
                    actions = self.get_actions_for_node(actor, adj, note="adjacent entity")
                    options.append(actions)

            # evaluate movement/travel options
            adjacent_locations = loc.get_adjacent_locations()

            if not adjacent_locations:
                logWarning("No adjacent locations found")
                
            if adjacent_locations:
                for adj_node in adjacent_locations:
                    options.append(self.get_actions_for_node(actor, adj_node, note="Travel to", is_adjacent_loc=True))


        return options


    def get_actions_for_node(self, actor, target, note=None, is_adjacent_loc=False):
        logAll(f"get_actions_for_node( actor: {actor.summary()}, target: {target.summary()}, note: {note}, is_adjacent_loc: {is_adjacent_loc} )")

        # handle inanimates
        if actor.Nodetype not in SOCIAL_NODE_TYPES:
            return []

        policy_disposition = "Neutral"

        if target.Nodetype in SOCIAL_NODE_TYPES:
            relationship = actor.determine_relation(target)
            policy_disposition = relationship[POLICY_DISPOSITION]

        if not is_adjacent_loc:
            actions = NGIN_MISSIONS[policy_disposition][target.Nodetype]
        else:
            actions = [['Travel','Overt']]

        return target, actions, note


    def select_action(self, actions, actor: SimulaeNode):
        logAll(f"select_action( actions: {actions}, actor: {actor.summary()} )")

        selection_idx = 0
        selected_action = None
        selected_target: tuple | None = None

        while not selected_action:

            while not selected_target:
                for idx, action in enumerate(actions):
                    target, options, note = action
                    print(f"{idx:3} | [{note:^16}] |{target} ")

                selection_idx = robust_int_entry("Select Target > ", 0, len(actions))

                selected_target = actions[selection_idx]

            target, options, note = selected_target

            logDebug(f"Selected target: {target.summary()} with options: {options} and note: {note}")

            logDebug(f"Actor's relation to target: {actor.get_relation(target)}")

            # display description of target
            print(f"you are {actor.get_relation(target)['Disposition']} towards {target.get_description()}")

            if len(options) > 1:

                for idx, opt in enumerate(options):
                    print(f"{idx:3} | ({opt[1]:^9}) {opt[0]}")

                selection_idx = robust_int_entry("Select Action (or '-1' to revert to target selection) > ",-1,len(options))

                if selection_idx == -1:
                    selected_target = None
                    continue
            else:
                selection_idx = 0

            selected_action = options[selection_idx]
            selected_target = target

        return selected_target, selected_action


    def generate_mission(self, actor, mission):

        target, m = mission
        action, liminality = m

        logAll(f"{actor.summary()} -> ({liminality}) {action} {target.summary()}")


    def resolve_action(self, actor, mission):
        logAll("resolve_action(",actor,mission,")")
        
        target, m = mission
        action, liminality = m

        logAll(f"{actor.summary()} -> ({liminality}) {action} {target.summary()}")

        if target.Nodetype in SOCIAL_NODE_TYPES:
            
            relationship = actor.get_relation(target)
            
            disposition = relationship['Disposition']

            logInfo('disposition:',disposition)

            if action == "Recruit":

                if self.can_perform_action(target, action):

                    relationship = actor.get_relation(target)
                    if relationship['Disposition'] == 'Hostile':
                        logInfo(f'{actor} cannot recruit {target} due to hostile disposition')
                    else:
                        logInfo(f'{actor} recruiting {target}')

                        # update recruitment
                        target.update_relation(actor, interaction="accompany")

            elif action == "Protect":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} protecting {target}')

            elif action == "Liberate":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} liberating {target}')

            elif action == "Escort":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} escorting {target}')

            elif action == "Eliminate":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} eliminating {target}')

            elif action == "Capture":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} capturing {target}')

            elif action == "Surveil":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} surveiling {target}')

            elif action == "Investigate":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} investigating {target}')
            
            elif action == "Mission":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} recieves a mission from {target}')
            
            else:
                logInfo("Unhandled action: ",action)


        elif target.Nodetype in INANIMATE_NODE_TYPES:

            if target.has_relation(actor.ID, FAC):

                relationship = actor.get_relation( target.get_relation(FAC) )

            if action == 'Travel':

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} traveling to {target}')

                    # actor & accompanyment travel to target
                    actor.set_location_by_ID(target.ID)         # set actor loc to target
                    target.add_reference('Occupant', actor.ID) # add actor as occupant to target

                    accompanying_actors = actor.get_accompanyment() # get actor's accompanyment
                    if accompanying_actors: # if any accompanyment
                        for actor_id in accompanying_actors:
                            actor = self.get_simulae_node_by_id(actor_id, POI)

                            if not actor:
                                logWarning(f"Accompanying actor with id '{actor_id}' not found in state!")
                                continue

                            actor.set_location_by_ID(target.ID) # set each accompanyment's loc to target
                            target.add_reference('Occupant', actor.ID) # add accompanyment as occupant to target


            elif action == 'Fortify':

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} fortifying {target}')

                    fortification = target.get_attribute("Fortification")

                    fortification = fortification + 1

                    target.set_attribute("Fortification", fortification)

            elif action == "Protect":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} protecting {target}')

            elif action == "Capture":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} capturing {target}')

            elif action == "Destroy":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} destroying {target}')

            elif action == "Infiltrate":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} infiltrating {target}')

            elif action == "Investigate":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} investigating {target}')

            elif action == "Surveil":

                if self.can_perform_action(target, action):
                    logInfo(f'{actor} surveiling {target}')

                        


    def can_perform_action(self, target, action):
        return True



def try_json_load(filename):

    try:
        return json.load(open(filename))
    except Exception as e:
        logError("Failed to load from JSON : ", filename)
        logError("Error msg:",e)
        return {}


def main():
    logAll("Starting NGIN Simulae Campaign Generator")
    
    # Import NGIN
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    mission_struct = load_json_from_file( "NGIN/NGIN_config/story_struct.json" )
    ngin_settings = load_json_from_file( "NGIN/NGIN_config/ngin_settings.json" )

    save_file = None
    if len(sys.argv) >= 5:
        save_file = load_json_from_file( sys.argv[1] )

    # Setup 
    ngin = NGIN( mission_struct, ngin_settings, save_file )

    # Start

    try:

        ngin.start()

    except Exception as e:
        logError(e)
    finally:
        logInfo('saving...')
        ngin.save_to_file("save_file.json")


if __name__ == '__main__':
    main()

