

import sys, random, json
from pprint import pprint

from NGIN.config import madlibs

def generate_policy():
    ''' Selects one of each option for each policy 'scale'
            also generates a random weight value to convey the
            importance of that policy to the faction's agenda/members
    '''
    policies = {
        "Economy":          ["Communist", "Socialist", "Indifferent", "Capitalist", "Free-Capitalist"],
        "Liberty":          ["Authoritarian", "Statist", "Indifferent", "Libertarian", "Anarchist"],
        "Culture":          ["Traditionalist", "Conservative", "Indifferent", "Progressive", "Accelerationist"],
        "Diplomacy":        ["Globalist", "Diplomatic", "Indifferent", "Patriotic", "Nationalist"],
        "Militancy":        ["Militarist", "Strategic", "Indifferent", "Diplomatic", "Pacifist"],
        "Diversity":        ["Homogenous", "Preservationist", "Indifferent", "Heterogeneous", "Multiculturalist"],
        "Secularity":       ["Apostate", "Secularist", "Indifferent", "Religious", "Devout"],
        "Justice":          ["Retributionist", "Punitive", "Indifferent", "Correctivist", "Rehabilitative"],
        "Natural-Balance":  ["Ecologist", "Naturalist", "Indifferent", "Productivist", "Industrialist"],
        "Government":       ["Democratic", "Republican", "Indifferent", "Oligarchic", "Autocratic"]
    }

    policy = {}

    for k,v in policies.items():
        #               position            weight
        policy[k] = [ random.choice(v), random.random() ]

    return policy



def politic_diff( alpha, beta ):
    ''' Gives policy differential score and summary '''

    score = 0 # total ideological difference
    summary = {}

    # includes a difference-descriptor for easy understanding
    descriptors = {
        0:"Agreement",
        1:"Civil",
        2:"Contentious",
        3:"Opposition",
        4:"Diametrically Opposed"
    }

    for f in self.politics['Policies'].keys():
        a_pol, a_weight = alpha.policy[f]
        b_pol, b_weight =  beta.policy[f]

        dist = abs( self.politics['Policies'][f].index(a_pol) - self.politics['Policies'][f].index(b_pol) )
        
        summary[f] = str(int((dist/4)*100))+'%' # (quick and dirty) round to 3 decimal places
        score += dist

    # show the difference score (rounded to 3 digits) and more detailed summary
    return str(int((score/40)*100))+'%', summary 



def generate_faction():

    # choose organization subtype
    orgtype = random.choice(madlibs['Entities'])
    
    # madlibs name generation
    name = random.choice(madlibs['Nouns']) + ('-'+random.choice(madlibs['Nouns']) if random.random() >= 0.6 else '' )
    suffix = random.choice(madlibs['Suffixes'][orgtype]) if random.random() >= 0.1 else ''
    name += ' '+suffix
    # acronym for quick/short reference (display purposes)
    acronym = ''.join( [ l for l in name if l.isupper() ] )

    # randomize policy
    policy = generate_policy()

    return orgtype, acronym, name, policy



def main():

    madlibs = json.load( open(sys.argv[1]) )

    print('Press [k]+[Enter] to keep a displayed faction')
    picked = []

    while True:

        # attribute generation

        # choose organization subtype
        orgtype, acronym, name, policy = generate_faction()

        # display to user
        print( '[',orgtype,'](',acronym,')',name, end='\n')

        # check user opinion
        cmd = input('> ')
        if cmd == 'k':
            picked.append( {'nodetype':orgtype, "name":name, 'acronym':acronym,'policy':policy} )
        elif cmd in ['q','quit']:
            break

    # write to save file in a readable format
    if picked:
        with open(sys.argv[2],'w') as savefile:
            savefile.write( json.dumps(picked, indent=4) )

if __name__ == '__main__':
    main()



