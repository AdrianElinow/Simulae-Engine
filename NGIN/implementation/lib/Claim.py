
from dataclasses import dataclass, field
from typing import Any, Literal


TruthStatus = Literal["unverified", "believed", "disbelieved", "unknown"]

@dataclass
class Claim:
    """A belief about the world, together with its confidence and provenance."""

    id: str
    subject: str
    predicate: str
    obj: Any
    t_first: int = 0
    t_last: int = 0
    provenance: list[str] = field(default_factory=list)
    sources: set[str] = field(default_factory=set)
    confidence: float = 0.5
    status: TruthStatus = "unverified"
    volatility: float = 0.5
    sensitivity: float = 0.5
    decay_rate: float = 0.01
