

import json, sys, random, os
from pprint import pprint

from NGIN.implementation.lib.SimulaeNode import SimulaeNode

''' 

Simulae
    References
    Attributes
    Assembly
    Memory
    Checks


SimulaeNode    
    # id, ntype, refs, attrs, reltn, checks, abilities

'''

class NGIN:

    def __init__(self, mission_struct, madlibs ):
        self.mission_struct = mission_struct
        self.madlibs = madlibs
        self.state = state = SimulaeNode(
                        "state",
                        "",
                        {},
                        {},
                        {
                            "FAC":{},
                            "PTY":{},
                            "POI":{},
                            "OBJ":{},
                            "LOC":{}
                        },
                        {},
                        {}
                    )
        
        nodes = self.generate_state(4) # generate start state with 4 initial nodes

        for n in nodes:
            self.state.relations[n.nodetype][n.id] = n

    def generate_element( self ):
        ''' creates a new node with random attributes ''' 

        name = random.choice( [ m for m in self.madlibs ] )

        ntype = random.choice( ['POI','PTY','OBJ','LOC'] )
        references = {}
        attributes = {}
        relations  = {}
        checks     = {}
        abilities  = {}

        # id, ntype, refs, attrs, reltn, checks, abilities
        return SimulaeNode( name, ntype, references, attributes, relations, checks, abilities )


    def generate_state( self, num_nodes ):
        ''' generates multiple new random nodes to (re)populate the game-state '''

        n_state = []
        for i in range(num_nodes):
            n_state.append(self.generate_element())
        return n_state


    def choose_mission(self, actor_node, num_opts=3 ):
        ''' To add more interractivity and user-control
                this function will give several available options to allow
                the player to 'control' their actions and interract
                with other nodes in a manner of their choice.
        '''

        options = []

        while len(options) < 3:

            subj = random.choice(self.state.relations[ random.choice(["POI","PTY","OBJ","LOC"]) ])

            if subj.nodetype in ["POI","PTY"]:
                actor_node.update_relation( subj, reciprocate=True )
                disposition = actor_node.relations[subj.ntype][subj.id]["Disposition"]
            else:
                disposition = "Neutral"

            opt = ( subj, random.choice( self.mission_struct[disposition][subj.ntype] ) )

            options.append(opt)


        choice = self.user_choice( options, random_opt=True )
        print('Chose', choice)
        return subj, choice[1], self.state




    def start(self):

        ''' Iterates through the game state generating missions based on
                available nodes in the state.
        '''

        while True:

            os.system('clear') # clear screen
            

            print('\nNodes:')
            for node in [ node for nid, node in nodes for ntype, nodes in self.state ]:
                print('\t',str(node))


            if not self.state:
                self.state = self.generate_state(5)

            #subject, mission, self.state = self.generate_mission()

            subject, mission, self.state = self.choose_mission( num_ops=5 )

            print(  '\n(',mission[1],') [',
                    mission[0],subject.name,'] {',
                    subject.disposition,subject.ntype,'}')


            success = self.user_choice( ['yes','no'], literal=True )

            if success == 'yes':

                if mission[0] in ['Eliminate','Destroy']:
                    # find and remove subject
                    self.state.remove(subject)

                elif mission[0] in ['Capture']:

                    if subject.ntype in ['LOC','OBJ']:

                        self.state.remove(subject)
                        # find and modify subject
                        subject.disposition = "Friendly"

                        self.state.append(subject)

                    else:
                        # find and remove subject
                        self.state.remove(subject)


            if random.random() <= 0.5:
                # generate new element to keep sim going
                print('\nNew Intel')
                intel = self.generate_element()
                pprint(('discovered '+intel.__str__()))
                self.state.append(intel)

            if random.random() <= 0.4:
                # generate random event to keep things interesting
                subject, mission, self.state = self.generate_event()

                if mission:
                    print(  '\n(',mission[1],') [',
                            mission[0],subject.name,'] {',
                            subject.disposition,subject.ntype,'}')

                    if mission[0] in ['Eliminate','Destroy']:
                        # find and remove subject in game-state
                        self.state.remove(subject)

            cmd = input('> ')
            if cmd in ['q','quit']:
                sys.exit(0)


    def generate_event( self ):
        ''' Selects a node as event basis, then generates an event based on 
                the node's type. Events are similar to missions, but are
                essentially the mission outcomes of other entities
        '''
        
        # choose node as event basis
        subj = random.choice(self.state)
        name, disp, objective, interractions = subj.unpack()

        # avoid modifying hostile nodes to maintain tension
        if disp in ['Neutral','Friendly']:
            roll = int(random.random() * 100)

            if roll < 25:
                print(name,'has', \
                    ('been captured by opfor' if objective in ['LOC','OBJ'] \
                    else "defected to the opfor"))

                subject_index = self.state.index(subj)

                # find and modify subject in game-state
                subj.disposition = "Hostile"
                subj.interractions += 1

                if subject_index:
                    self.state[subject_index] = subj

            elif roll < 50:
                print(name, 'has been', \
                    ('Destroyed' if objective in ['LOC','OBJ'] \
                    else 'Killed'))

                # find and remove subject in game-state
                self.state.remove(subj)

            # no mission for these types of random events
            return subj, None, self.state

        # 
        return  subj, \
                random.choice(self.mission_struct[disp][objective]), \
                self.state


    def user_choice(user_options, literal=False, random_opt=False ):
        ''' Present user with available options, and allow them to pick
                an option to proceed. 

            literal : does the user need to type out the option explicitly?
                True -> user must enter the explicit option as typed.
                False -> user will instead enter the option's presented index
            random_opt : allow the user to select 'random' which will randomly
                select an option instead?
        '''

        choice = None
        chosen = None

        if literal:
            print(user_options)
            print( ' / '.join(user_options) )

            while not choice:
                choice = input('> ')

                for i, opt in enumerate(user_options):
                    if choice in opt:
                        if not chosen:
                            chosen = opt
                        else:
                            print('Multiple choice selected. Invalid')
                            choice = None
                            break
                if chosen:
                    print(chosen)
                    return chosen
                choice = None
                print('Invalid')
        
        else:
            ''' Standard operation '''

            # preset options
            for i, opt in enumerate(user_options):
                # account for lists / tuples
                if type(opt) in [ type( (0,0) ), type( [1,1] ) ]: 
                    print('({0}) {1}'.format(i, ' '.join([ str(e) for e in opt ])))
                else: # simple items
                    print('({0}) {1}'.format(i, str(opt) ))
            if random_opt:
                print('({0}) {1}'.format(len(user_options), 'random'))

            # take user selection
            while not choice:
                try:
                    choice = input('> ')
                    if choice in ['q','quit']:
                        raise KeyboardInterrupt

                    choice = int(choice)
                    if choice in range(len(user_options) + (1 if random_opt else 0)):
                        if choice == len(user_options):
                            chosen = random.choice(user_options)

                            return chosen
                            
                        return user_options[choice]
                except ValueError as ve:
                    pass
                except KeyboardInterrupt as ki:
                    sys.exit(0) # account for Control-C exit
                choice = None
                print('Invalid')

        return choice


def main():
    
    ''' required import(s) '''
    mission_struct = json.load( open( sys.argv[1] ) )
    madlibs = [
        "Alpha",
        "Beta",
        "Delta",
        "Zeta",
        "Omicron",
        "Omega",
        "Lambda",
        "Tau",
        "Gamma",
        "Sigma",
        "Eagle",
        "Wolf",
        "Spider",
        "Siege",
        "Sanguine",
        "Bear",
        "Hound",
        "Phoenix",
        "Dragon",
        "Lion",
        "Gorilla",
        "Rhino",
        "Storm",
        "Shadow",
        "Nocturn",
        "Prime",
        "Zeus",
        "Essence",
        "Banshee",
        "Specter",
        "Typhoon",
        "Pinnacle",
        "Odin",
        "Silver",
        "Platinum",
        "Titan",
        "Heart",
        "Karma",
        "Angel",
        "Demon",
        "Arcane",
        "Mystic",
        "Jupiter",
        "Mars",
        "Meridian",
        "Atlas",
        "Raptor",
        "Void",
        "Hurricane",
        "Harbor",
        "Cold",
        "Jet",
        "Global",
        "Green",
        "Red",
        "Blue",
        "Tap",
        "Soul",
        "Slick",
        "Omen",
        "Arm",
        "Revelation",
        "November",
        "Reach",
        "Winter",
        "Twilight",
        "Quad",
        "Tri",
        "Saturn",
        "Ward",
        "Violet",
        "Steel",
        "Granite",
        "Stone",
        "Slate",
        "First",
        "Federal",
        "Statement",
        "Macguffin",
        "United",
        "King",
        "Queen",
        "Sultan",
        "Atom",
        "Cellular",
        "Spruce",
        "Black",
        "Executive",
        "Admin",
        "Diesel"
    ]

    ngin = NGIN( mission_struct, madlibs )

    ngin.start()



if __name__ == '__main__':
    main()

