from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from NGIN.utilities.lib.ngin_utils import logAll

if TYPE_CHECKING:
    from .SimulaeNode import SimulaeNode

class SimulaeNodeStatus(Enum):
    ''' Simulae Node status '''
    ALIVE = 0
    DEAD = 1

    def toJSON(self):
        return self.name