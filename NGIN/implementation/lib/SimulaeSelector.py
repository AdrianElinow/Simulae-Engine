from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition


class SimulaeSelector:
    """Filters SimulaeNodes or JSON-like objects using SimulaeCondition rules."""

    MATCH_FIRST = "first"
    MATCH_LAST = "last"
    MATCH_ALL = "all"
    MATCH_ANY = "any"
    MATCH_NONE = "none"
    MATCH_MODES = {MATCH_FIRST, MATCH_LAST, MATCH_ALL, MATCH_ANY, MATCH_NONE}

    def __init__(
        self,
        conditions: Iterable[SimulaeCondition] | None = None,
        *,
        match_all: bool = True,
        match_mode: str = MATCH_ALL,
    ):
        self.match_all = match_all
        self.match_mode = self._validate_match_mode(match_mode)
        self.conditions: list[SimulaeCondition] = []

        for condition in conditions or []:
            self.add_condition(condition)

    def add_condition(self, condition: SimulaeCondition) -> None:
        if not isinstance(condition, SimulaeCondition):
            raise ValueError("Selector conditions must be SimulaeCondition instances")

        self.conditions.append(condition)

    def matches(self, candidate: Any, **context: Any) -> bool:
        if not self.conditions:
            return True

        evaluations = (condition.evaluate(candidate, **context) for condition in self.conditions)
        return all(evaluations) if self.match_all else any(evaluations)

    def select(self, candidates: Iterable[Any], match_mode: str | None = None, **context: Any) -> Any:
        mode = self._validate_match_mode(match_mode or self.match_mode)

        if mode == self.MATCH_FIRST:
            return self.first(candidates, **context)
        if mode == self.MATCH_LAST:
            return self.last(candidates, **context)

        selected = [candidate for candidate in candidates if self.matches(candidate, **context)]

        if mode == self.MATCH_ALL:
            return selected
        if mode == self.MATCH_ANY:
            return bool(selected)
        if mode == self.MATCH_NONE:
            return not selected

        raise ValueError(f"Unsupported selector match mode: {mode}")

    def first(self, candidates: Iterable[Any], default: Any = None, **context: Any) -> Any:
        for candidate in candidates:
            if self.matches(candidate, **context):
                return candidate

        return default

    def last(self, candidates: Iterable[Any], default: Any = None, **context: Any) -> Any:
        match = default

        for candidate in candidates:
            if self.matches(candidate, **context):
                match = candidate

        return match

    def _validate_match_mode(self, match_mode: str) -> str:
        if match_mode not in self.MATCH_MODES:
            raise ValueError(f"Selector match mode must be one of {sorted(self.MATCH_MODES)}")

        return match_mode
