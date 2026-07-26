FAC = 'Faction' # Faction
POI = 'Person' # Person (of Interest)
PTY = 'Party' # Party
LOC = 'Location' # Location
OBJ = 'Object' # Object

EVT = 'Event' # Event
CND = 'Condition' # Conditional

SRC = "Source" # source
TGT = "Target" # target
OBS = "Observer" # Observer

NAME = "Name"
ADJACENT = "Adjacent"
STATUS = "Status"
INTERACTIONS = "Interactions"
REPUTATION = "Reputation"

ID = "ID"
REFERENCES = "References"
NODETYPE = "Nodetype"
ATTRIBUTES = "Attributes"

CHECKS = "Checks"
ABILITIES = "Abilities"
MEMORY = "Memory"

SCALES = "Scales"
DISPOSITION_SUFFIX = "Disposition"
POLICY_DISPOSITION = "PolicyDisposition"
SOCIAL_DISPOSITION = "SocialDisposition"

ALL_NODE_TYPES = [FAC,POI,PTY,LOC,OBJ]
PHYSICAL_NODETYPES = [POI,PTY,LOC,OBJ] # person, people, place, thing
SOCIAL_NODE_TYPES = [FAC,POI,PTY]
GROUP_NODE_TYPES = [FAC,PTY]
PEOPLE_NODE_TYPES = [POI,PTY]
INANIMATE_NODE_TYPES = [LOC,OBJ]
META_NODE_TYPES = [EVT, CND]

RELATIONS = "Relations"
CONTENTS = "Contents"
COMPONENTS = "Components"
ATTACHMENTS = "Attachments"
PHYSICAL_RELATIVE_TYPES = [CONTENTS, COMPONENTS, ATTACHMENTS, ADJACENT]
RELATION_TYPES = PHYSICAL_RELATIVE_TYPES + PHYSICAL_NODETYPES

EVENTS = "Events"
TIMELINE = "Timeline"
CLAIMS = "Claims"
COMMITMENTS = "Commitments"
SOCIAL = "Social"
THREADS = "Threads"

MEMORY_CLASSIFICATIONS = [EVENTS, TIMELINE, CLAIMS, COMMITMENTS, SOCIAL, THREADS]
MEMORY_CATEGORIES = MEMORY_CLASSIFICATIONS + ALL_NODE_TYPES

DEFAULT_POLICY_VALUE = 4 # halfway between 1 and 7
DEFAULT_PERSONALITY_VALUE = 3 # halfway between 0 and 6

POLICY_STRENGTH_RANGE = [0, 10] # should match len of SCALE_DEGREE_DESCRIPTORS
PERSONALITY_STRENGTH_RANGE = [0, 10] # should match len of SCALE_DEGREE_DESCRIPTORS

POLICY_DIFFERENTIAL_DESCRIPTORS = [
    "Aligned",             # 0
    "Similar",             # 1
    "Somewhat Similar",    # 2
    "Different",           # 3
    "Very Different",      # 4
    "Near-Opposed",        # 5
    "Opposed",             # 6
]

SOCIAL_DIFFERENTIAL_DESCRIPTORS = [
    "Identical",      # delta 0â€“4
    "Similar",        # delta 5â€“14
    "Comparable",     # delta 15â€“24
    "Distinct",       # delta 25â€“34
    "Different",      # delta 35â€“49
    "Contrasting",    # delta 50â€“64
    "Opposed",        # delta 65â€“79
]

SCALE_DEGREE_DESCRIPTORS = [
    "",                    # 0 â€” effectively aligned / indistinguishable
    "Rather ",             # 1
    "Slightly ",           # 2
    "Mildly ",             # 3
    "Moderately ",         # 4
    "Noticeably ",         # 5
    "Significantly ",      # 6
    "Strongly ",           # 7
    "Extremely ",          # 8
    "Diametrically ",      # 9 â€” categorical divergence
]

STATUS_THRESHOLDS = "status_thresholds"
THREAT = "threat"
HUNGER = "hunger"
THIRST = "thirst"
DRINK = "drink"
SLEEP = "sleep"
SICK = "sick"
TEMPERATURE = "temperature"
COLD = "cold"
HOT = "hot"
EXHAUSTION = "exhaustion"
LONELINESS = "loneliness"
LOW = "low"
HIGH = "high"
MINIMUM = "min"
MAXIMUM = "max"
VALUE = "value"

STATUS_ATTRIBUTES = [HUNGER, THIRST, HOT, COLD, EXHAUSTION, LONELINESS, SICK]

PRIORITY_MODIFIERS = "priority_modifiers"
CRITICAL_PRIORITY = "critical_priority"
HIGH_PRIORITY = "high_priority"
MEDIUM_PRIORITY = "medium_priority"
LOW_PRIORITY = "low_priority"

TASK_PRIORITIES = [CRITICAL_PRIORITY, HIGH_PRIORITY, MEDIUM_PRIORITY, LOW_PRIORITY]
