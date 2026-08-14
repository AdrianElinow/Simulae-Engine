from __future__ import annotations

from typing import Any

from NGIN.implementation.lib.SimulaeAction import *
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode, StringKeyDict
from NGIN.utilities.lib.SimulaeConstants import *

CONDITION_KEY = "condition"
CONDITIONS_KEY = "conditions"
EFFECT_NAME_KEY = "effect_name"
PASSED_KEY = "passed"

class SimulaeEffect(SimulaeNode):
    """Condition-gated bundle of SimulaeActions.

    Effects describe how SimulaeNodes interact: they can change references,
    attributes, checks, abilities, memories, relations, trigger nested effects,
    and emit SimulaeEvents for callers to persist.
    """

    def __init__(
        self,
        given_id: str | None = None,
        *,
        name: str | None = None,
        conditions: list[SimulaeCondition] | None = None,
        actions: list[SimulaeAction] | None = None,
        references: StringKeyDict | None = None,
        attributes: StringKeyDict | None = None,
        checks: StringKeyDict | None = None,
        abilities: StringKeyDict | None = None,
        relations: StringKeyDict | None = None,
        memory: StringKeyDict | None = None,
    ):
        effect_references = dict(references or {})
        if name:
            effect_references[NAME] = name

        super().__init__(
            given_id=given_id,
            nodetype=EFX,
            references=effect_references,
            attributes=attributes,
            relations=relations,
            checks=checks,
            abilities=abilities,
            memory=memory,
        )

        self.Conditions = conditions or []
        self.Actions = actions or []

    def can_apply(
        self,
        targets: list[SimulaeNode] | None = None,
        sources: list[SimulaeNode] | tuple[SimulaeNode] | None = None,
    ) -> bool:

        if not targets:
            return self._evaluate_condition(targets = )
        
    def apply(
        self,
        target: SimulaeNode | None = None,
        *,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        source: SimulaeNode | str | None = None,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        context: dict[str, Any] | None = None,
        create_event: bool = False,
    ) -> dict[str, Any]:
        pass


    def _evaluate_conditions(self, targets: list[SimulaeNode] | None = None, sources: list[SimulaeNode] | None = None) -> bool:
        if not self.Conditions:
            return True

        for condition in self.Conditions:
            for target in targets or []:
                for source in sources or []:
                    if not self._evaluate_condition(condition, target=target, source=source):
                        return False

        return True

    def _evaluate_condition(self, condition: SimulaeCondition, target: SimulaeNode | None = None, source: SimulaeNode | None = None) -> bool:

        if not condition or not target: 
            return False

        return condition.evaluate(target=target, source=source)