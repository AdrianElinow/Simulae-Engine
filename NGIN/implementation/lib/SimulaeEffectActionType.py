from enum import Enum

class SimulaeEffectActionType(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    INCREMENT = "increment"
    DECREMENT = "decrement"
    TOGGLE = "toggle"
    TRANSMUTE = "transmute"
    COMPOSE = "compose"
    DECOMPOSE = "decompose"
    TRIGGER = "trigger"
    UNSUPPORTED = "unsupported"
