
from __future__ import annotations

from dataclasses import dataclass, field
from NGIN.utilities.lib.ngin_utils import get_unique_strs, normalize_str
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent

class SocialEvent(SimulaeEvent):
    
    def __init__(self, 
                event_type: str, 
                event_subtype: str | None = None, 
                **kwargs):

        event_type = normalize_str(event_type)
        event_subtype = normalize_str(event_subtype)

        super().__init__(
            event_class='social',
            event_type=event_type,
            event_subtype=event_subtype,
            **kwargs
        )
