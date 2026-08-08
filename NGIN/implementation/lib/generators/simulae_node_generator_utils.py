
import random

from NGIN.config.madlibs import HUMAN_BODY_METRICS
from NGIN.utilities.lib.social_scale_utils import random_bell_curve_value
from NGIN.utilities.lib.ngin_console_log import MAX_ADJACENT_LOCATIONS, logAll
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import *

def generate_simulae_node(node_type=None, node_name=None):
    logAll("generate_simulae_node(",node_type,", ",node_name,")")

    nodetype = random.choice( PHYSICAL_NODETYPES ) if not node_type else node_type

    simulae_node = SimulaeNode( nodetype=nodetype )

    if node_name:
        simulae_node.set_reference(NAME, node_name)

    if nodetype == LOC:
        simulae_node.set_attribute("max_adjacent_locations", random.randrange(1,MAX_ADJACENT_LOCATIONS))

    return simulae_node

def generate_person_simulae_node(node_name=None, include_body: bool = True):
    logAll("generate_person_simulae_node(",node_name,")")
    ''' generate_person_simulae_node() generates a SimulaeNode of type POI with random attributes '''
    
    person = generate_simulae_node(POI, node_name)

    age = int(random_bell_curve_value(
        min_val=6, 
        max_val=80, 
        average=30, 
        std_dev=15))
    person.set_attribute("Age", age) # age

    gender = random.choice(["Male","Female"])
    person.set_reference("Gender", gender)
    #person.set_reference("Race", random.choice(["White", "Black", "Asian", "Hispanic", "Middle-Eastern", "Native American", "South Asian"]))

    # generate height & weight
    total_height = random_bell_curve_value(
        min_val = HUMAN_BODY_METRICS[(gender.lower())]["height"]["min"], 
        max_val = HUMAN_BODY_METRICS[(gender.lower())]["height"]["max"],
        average = HUMAN_BODY_METRICS[(gender.lower())]["height"]["avg"],
        std_dev = HUMAN_BODY_METRICS[(gender.lower())]["height"]["stddev"]) # meters

    total_weight = random_bell_curve_value(
        min_val = HUMAN_BODY_METRICS[(gender.lower())]["weight"]["min"], 
        max_val = HUMAN_BODY_METRICS[(gender.lower())]["weight"]["max"],
        average = HUMAN_BODY_METRICS[(gender.lower())]["weight"]["avg"],
        std_dev = HUMAN_BODY_METRICS[(gender.lower())]["weight"]["stddev"]) # meters

    person.set_attribute("Height", round(total_height, 2))
    person.set_attribute("Weight", round(total_weight, 2))

    if include_body:
        head, torso, left_arm, right_arm, left_leg, right_leg = generate_person_body(
            gender=gender,
            age=age,
            height=total_height,
            weight=total_weight,
            complete=True)
        
        person.Relations[COMPONENTS][OBJ][torso.ID] = torso
        person.Relations[COMPONENTS][OBJ][left_arm.ID] = left_arm
        person.Relations[COMPONENTS][OBJ][right_arm.ID] = right_arm
        person.Relations[COMPONENTS][OBJ][left_leg.ID] = left_leg
        person.Relations[COMPONENTS][OBJ][right_leg.ID] = right_leg
        person.Relations[COMPONENTS][OBJ][head.ID] = head

    return person

def generate_person_body(gender: str, age: int, height: float, weight: float, complete: bool = True):
    logAll("generate_person_body()")

    leg_height = height * HUMAN_BODY_METRICS["limbs"]["leg_height"]
    torso_height = height * HUMAN_BODY_METRICS["limbs"]["torso_height"]
    head_height = height * HUMAN_BODY_METRICS["limbs"]["head_height"]
    #feet_height = total_height * HUMAN_BODY_METRICS["limbs"]["foot_height"]
    arm_height = height * HUMAN_BODY_METRICS["limbs"]["arm_height"]

    head_weight = weight * HUMAN_BODY_METRICS["limbs"]["head_height"]        # 7%
    leg_weight = weight * HUMAN_BODY_METRICS["limbs"]["leg_height"]        # 35%
    torso_weight = weight * HUMAN_BODY_METRICS["limbs"]["torso_height"]        # 40%
    arm_weight = weight * HUMAN_BODY_METRICS["limbs"]["arm_height"]        # 15%
    hand_weight = weight * HUMAN_BODY_METRICS["limbs"]["hand_weight"]       # 1%
    foot_weight = weight * HUMAN_BODY_METRICS["limbs"]["foot_height"]        # 2%  

    # add standard things like limbs and organs

    torso = SimulaeNode( nodetype=OBJ, references={ NAME:"Torso" }, attributes={"height": torso_height, "weight": torso_weight} )
    skull = SimulaeNode( nodetype=OBJ, references={ NAME:"Skull" } )
    left_arm = SimulaeNode( nodetype=OBJ, references={ NAME:"Left Arm" }, attributes={"height": arm_height, "weight": arm_weight} )
    right_arm = SimulaeNode( nodetype=OBJ, references={ NAME:"Right Arm" }, attributes={"height": arm_height, "weight": arm_weight} )
    left_leg = SimulaeNode( nodetype=OBJ, references={ NAME:"Left Leg" }, attributes={"height": leg_height, "weight": leg_weight} )
    right_leg = SimulaeNode( nodetype=OBJ, references={ NAME:"Right Leg" }, attributes={"height": leg_height, "weight": leg_weight} )
    left_hand = SimulaeNode( nodetype=OBJ, references={ NAME:"Left Hand" }, attributes={"weight": hand_weight} )
    right_hand = SimulaeNode( nodetype=OBJ, references={ NAME:"Right Hand" }, attributes={"weight": hand_weight} )
    head = SimulaeNode( nodetype=OBJ, references={ NAME:"Head" }, attributes={"height": head_height, "weight": head_weight} )

    # add organs
    heart = SimulaeNode( nodetype=OBJ, references={ NAME:"Heart" } )
    lungs = SimulaeNode( nodetype=OBJ, references={ NAME:"Lungs" } )
    brain = SimulaeNode( nodetype=OBJ, references={ NAME:"Brain" } )
    liver = SimulaeNode( nodetype=OBJ, references={ NAME:"Liver" } )
    kidneys = SimulaeNode( nodetype=OBJ, references={ NAME:"Kidneys" } )
    stomach = SimulaeNode( nodetype=OBJ, references={ NAME:"Stomach" } )
    intestines = SimulaeNode( nodetype=OBJ, references={ NAME:"Intestines" } )
    eyes = SimulaeNode( nodetype=OBJ, references={ NAME:"Eyes" } )
    ears = SimulaeNode( nodetype=OBJ, references={ NAME:"Ears" } )
    nose = SimulaeNode( nodetype=OBJ, references={ NAME:"Nose" } )
    mouth = SimulaeNode( nodetype=OBJ, references={ NAME:"Mouth" } )
    hair = SimulaeNode( nodetype=OBJ, references={ NAME:"Hair" } )
    teeth = SimulaeNode( nodetype=OBJ, references={ NAME:"Teeth" } )

    torso.Relations[CONTENTS][OBJ][heart.ID] = heart
    torso.Relations[CONTENTS][OBJ][lungs.ID] = lungs
    
    torso.Relations[CONTENTS][OBJ][liver.ID] = liver
    torso.Relations[CONTENTS][OBJ][kidneys.ID] = kidneys
    torso.Relations[CONTENTS][OBJ][stomach.ID] = stomach
    torso.Relations[CONTENTS][OBJ][intestines.ID] = intestines
    ### etc...

    head.Relations[COMPONENTS][OBJ][skull.ID] = skull
    head.Relations[CONTENTS][OBJ][brain.ID] = brain
    head.Relations[CONTENTS][OBJ][eyes.ID] = eyes
    head.Relations[CONTENTS][OBJ][ears.ID] = ears
    head.Relations[CONTENTS][OBJ][nose.ID] = nose
    head.Relations[CONTENTS][OBJ][mouth.ID] = mouth
    head.Relations[CONTENTS][OBJ][hair.ID] = hair
    head.Relations[CONTENTS][OBJ][teeth.ID] = teeth

    left_arm.Relations[COMPONENTS][OBJ][left_hand.ID] = left_hand
    right_arm.Relations[COMPONENTS][OBJ][right_hand.ID] = right_hand

    return head, torso, left_arm, right_arm, left_leg, right_leg
