from math import e
from enum import Enum
from pprint import pprint

class DEBUG_LEVEL(Enum):
    ''' DEBUG level '''
    ERROR = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3
    # ...
    ALL = 10
    
CURRENT_DEBUG_LEVEL = DEBUG_LEVEL.DEBUG

MAX_ADJACENT_LOCATIONS = 6
WORLD_GEN_STICKINESS = 0.4
WORLD_GEN_SUBLOCATION_CHANCE = 0.3
WORLD_GEN_POPULATION_GROUP_CHANCE = 0.25

def logInfo(*args):
    log(*args, newline=True, level=DEBUG_LEVEL.INFO)

def logAll(*args):
    log(*args, newline=True, level=DEBUG_LEVEL.ALL)

def logDebug(*args):
    log(*args, newline=True, level=DEBUG_LEVEL.DEBUG)

def logError(*args):
    log(*args, newline=True, level=DEBUG_LEVEL.ERROR)

def logWarning(*args):
    log(*args, newline=True, level=DEBUG_LEVEL.WARNING)

def log(*args, newline=True, level: DEBUG_LEVEL = DEBUG_LEVEL.ALL):
    if level.value > CURRENT_DEBUG_LEVEL.value:
        return
    
    if not args:
        return
    
    msg = ' '.join(str(arg) for arg in args)
    print(f"[{level.name}] {msg}", end='\n' if newline else '')