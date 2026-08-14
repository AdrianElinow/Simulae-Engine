from __future__ import annotations

from enum import Enum
from typing import Any, Callable, TYPE_CHECKING

from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import (
    ABILITIES,
    ACT,
    ATTRIBUTES,
    CHECKS,
    COMPONENTS,
    CONTENTS,
    END,
    EFX,
    EVENTS,
    EVT,
    ID,
    MEMORY,
    NAME,
    NODETYPE,
    OBS,
    REFERENCES,
    RELATIONS,
    SRC,
    START,
    TGT,
)

if TYPE_CHECKING:
    from NGIN.implementation.lib.SimulaeEffect import SimulaeEffect


ACTION_KEY = "action"
ACTION_TYPE_KEY = "type"
ACTIONS_KEY = "actions"
AFTER_KEY = "after"
APPLIED_KEY = "applied"
BEFORE_KEY = "before"
BUCKET_KEY = "bucket"
CALLABLE_REF_KEY = "callable_ref"
CATEGORY_KEY = "category"
EFFECT_ID_KEY = "effect_id"
EFFECT_KEY = "effect"
ERROR_KEY = "error"
EVENT_CLASS_KEY = "event_class"
EVENT_ID_KEY = "event_id"
EVENT_KEY = "event"
EVENT_SPECS_KEY = "event_specs"
EVENT_SUBTYPE_KEY = "event_subtype"
EVENT_TARGETS_KEY = "targets"
EVENT_TYPE_KEY = "event_type"
EVENTS_KEY = "events"
FIELD_KEY = "field"
ID_KEY = "id"
KEY_KEY = "key"
NODE_ID_KEY = "node_id"
NODE_KEY = "node"
OLD_NODE_ID_KEY = "old_node_id"
OLD_NODETYPE_KEY = "old_nodetype"
OBSERVER_IDS_KEY = "observer_ids"
OBSERVERS_KEY = "observers"
RELATION_TYPE_KEY = "relation_type"
RELATIONS_KEY = "relations"
RESULT_KEY = "result"
SOURCE_ID_KEY = "source_id"
SOURCE_IDS_KEY = "source_ids"
SOURCES_KEY = "sources"
TARGET_ID_KEY = "target_id"
TARGET_IDS_KEY = "target_ids"
TARGETS_KEY = "targets"
VALUE_KEY = "value"


class SimulaeEffectActionType(str, Enum):
    ADD = "add"
    SET = "set"
    UPDATE = "update"
    REMOVE = "remove"
    DELETE = "delete"
    INCREMENT = "increment"
    DECREMENT = "decrement"
    TOGGLE = "toggle"
    TRANSMUTE = "transmute"
    TRIGGER_EFFECT = "trigger_effect"
    CREATE_EVENT = "create_event"
    CREATE_EVENTS = "create_events"
    CALLABLE = "callable"
    UNSUPPORTED = "unsupported"


ACTION_ALIASES = {
    "compose": SimulaeEffectActionType.ADD,
    "decompose": SimulaeEffectActionType.REMOVE,
    "effect": SimulaeEffectActionType.TRIGGER_EFFECT,
    "event": SimulaeEffectActionType.CREATE_EVENT,
    "events": SimulaeEffectActionType.CREATE_EVENTS,
    "modify": SimulaeEffectActionType.UPDATE,
}


class SimulaeAction(SimulaeNode):
    """Executable Simulae meta-node.

    The public representation is JSON-safe and lives in References. Runtime-only
    objects are kept on private attributes so relation additions, nested effects,
    and callable actions can still execute after schema serialization.
    """

    def __init__(
        self,
        name: str,
        action_type: SimulaeEffectActionType,
        action: dict = {},
        given_id: str | None = None,
        effect: SimulaeEffect | None = None,
        references: dict = {},
        attributes: dict = {},
        checks: dict = {},
        abilities: dict = {},
        relations: dict = {},
        memory: dict = {},
    ):
        references = dict(references or {})

        if action_type is not None:
            references[ACT] = action_type

        if name:
            references[NAME] = name

        super().__init__(
            given_id=given_id,
            nodetype=ACT,
            references=references,
            attributes=attributes,
            relations=relations,
            checks=checks,
            abilities=abilities,
            memory=memory,
        )

        self.Effect = effect

    def apply(
        self,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
    ) -> list[str]:

        ## 

        return []