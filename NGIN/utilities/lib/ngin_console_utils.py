
import random
import sys
from .ngin_console_log import log, logError, logWarning, logDebug, logInfo, logAll

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

            while not choice:
                choice = input(' / '.join(user_options)+'> ')

                for i, opt in enumerate(user_options):
                    if choice in opt:
                        if not chosen:
                            chosen = opt
                        else:
                            print('Multiple choice selected. Invalid')
                            choice = None
                            break
                if chosen:
                    return chosen
                choice = None
                print('Invalid')
        
        else:
            ''' Standard operation '''

            # preset options
            for i, opt in enumerate(user_options):
                # account for lists / tuples
                if type(opt) in [ type( (0,0) ), type( [1,1] ) ]: 
                    node_name, mission_type_tuple = opt
                    readable_description = "{0} {2} ({1})".format(mission_type_tuple[0], mission_type_tuple[1], node_name)

                    print('({0}) {1}'.format(i, readable_description))
                else: # simple items
                    print('({0}) {1}'.format(i, str(opt) ))
            if random_opt:
                print('({0}) {1}'.format(len(user_options), 'random'))

            # take user selection
            while not choice:
                try:
                    choice = input('(Choice) > ')
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


def prompt_mission( options ):

    entry = ""

    while not entry:

        print('Options: ')
        for idx, opt in enumerate(options):
            simnode, act = opt
            action, vis = act

            print('{0} | ({1}) {2} {3}'.format(idx, vis, action, simnode.summary()))

        try:
            entry = input("Select Mission:").strip()
            if options:
                if ',' in entry:
                    entries = entry.split(',')
                    selected = []

                    for e in entries:
                        if e not in options:
                            try:
                                e = options[int(e)]
                                selected.append(e)
                            except ValueError as ve:
                                log(ve)
                        else:
                            selected.append(e)
                    
                    if selected:
                        return selected
                    else:
                        entry = None
                        selected = None
                        print("Invalid")

                if entry not in options:
                    entry_value = int(entry) if entry else None # try to interpret as numeric choice

                    if not entry_value or entry_value not in range(len(options)):
                        entry = None
                        print('Invalid')
                        continue

                    entry = options[int(entry)] # try to interpret as numeric choice

                    if entry not in options: # still not valid
                        entry = None
                        print('Invalid')
        
        except ValueError as ve: # handle numeric choice conversion error
            log(ve)
            entry = None
            print('Invalid')
        except KeyboardInterrupt as ki:
            log(ki)
            sys.exit(0)

    return entry


def robust_int_entry(prompt=None, low: int | None = None, high: int | None = None):

    if not prompt:
        prompt = ">"

    entry = ""

    while not entry:

        try:
            entry = input(prompt).strip()

            value = int(entry)

            if low and high:
                if value < low or value > high:
                    entry=None
                    print("Out-of-bounds value")
                    continue

            return value

        except ValueError as ve:
            entry=None
            print("Invalid")
        except KeyboardInterrupt as ki:
            sys.exit(0)


def robust_str_entry(prompt, options=[]):
    '''  '''

    if type(options) == type({}):
        log("Converting dict keys to list of options")
        options = list(options.keys())

    entry = ""

    while not entry:

        if options:
            print('Options: ')
            for idx, opt in enumerate(options):
                print('{0} | {1}'.format(idx, opt))

        try:
            entry = input(prompt).strip()

            if not entry:
                print("Entry cannot be empty")
                continue

            if options:
                if ',' in entry:
                    entries = entry.split(',')
                    selected = []

                    for e in entries:
                        if e not in options:
                            try:
                                e = options[int(e)]
                                selected.append(e)
                            except ValueError as ve:
                                log(ve)
                        else:
                            selected.append(e)
                    
                    if selected:
                        return selected
                    else:
                        entry = None
                        selected = None
                        print("Invalid")

                if entry not in options:
                    entry_value = int(entry) if entry else None # try to interpret as numeric choice

                    if not entry_value or entry_value not in range(len(options)):
                        entry = None
                        print('Invalid')
                        continue

                    log(options)
                    log(entry, entry_value)

                    entry = options[entry_value] # try to interpret as numeric choice

                    if entry not in options: # still not valid
                        entry = None
                        print('Invalid')
        
        except ValueError as ve: # handle numeric choice conversion error
            log(ve)
            entry = None
            print('Invalid')
        except KeyboardInterrupt as ki:
            log(ki)
            sys.exit(0)

    return entry

