from __future__ import annotations

from typing import Any

from NGIN.implementation.lib.SimulaeAction import SimulaeAction, SimulaeEffectActionType
from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import *


class SimulaeEffect(SimulaeNode):
    """Condition-gated collection of SimulaeActions that returns events."""

    def __init__(
        self,
        given_id: str | None = None,
        *,
        name: str | None = None,
        conditions: list[SimulaeCondition] | None = None,
        actions: list[SimulaeAction] | None = None,
    ):
        super().__init__(
            given_id=given_id,
            nodetype=EFX,
            references={NAME: name} if name else {},
        )

        self.Conditions: list[SimulaeCondition] = []
        self.Actions: list[SimulaeAction] = []

        for condition in conditions or []:
            if not isinstance(condition, SimulaeCondition):
                raise TypeError("Effect conditions must be SimulaeCondition instances")
            self.Conditions.append(condition)

        for action in actions or []:
            if not isinstance(action, SimulaeAction):
                raise TypeError("Effect actions must be SimulaeAction instances")
            self.Actions.append(action)

    def can_apply(
        self,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        sources: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
    ) -> list[str]:
        if not targets:
            return []

        return [
            target.ID
            for target in targets
            if self._conditions_pass(target)
        ]

    def apply(
        self,
        *,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        effects: list[Any] | tuple[Any, ...] | None = None,
        create_event: bool = False,
    ) -> list[SimulaeEvent]:
        target_list = self._normalize_targets(targets)
        active_effects = [self, *self._effects(effects)]
        events = [
            event
            for active_target in target_list
            if self._conditions_pass(active_target)
            for action in self.Actions
            for event in action.apply(
                targets=[active_target],
                sources=sources,
                observers=observers,
                effects=active_effects,
            )
        ]

        if create_event and events:
            events.append(
                self._summary_event(
                    self._participant_ids(sources),
                    [item.ID for item in target_list],
                    self._participant_ids(observers),
                    [event.ID for event in events],
                )
            )

        return events

    def _conditions_pass(self, target: SimulaeNode) -> bool:
        return all(condition.evaluate(target) for condition in self.Conditions)

    def _summary_event(
        self,
        source_ids: list[str],
        target_ids: list[str],
        observer_ids: list[str],
        event_ids: list[str],
    ) -> SimulaeEvent:
        event = SimulaeEvent(
            f"{self.ID}-event",
            "effect",
            self.References.get(NAME, self.ID),
            "summary",
            None,
            None,
            source_ids,
            target_ids,
            observer_ids,
            [self.ID],
        )
        event.References["effect_occurred"] = True
        event.References["effect_id"] = self.ID
        event.References["created_event_ids"] = event_ids
        return event

    def _normalize_targets(
        self,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None,
    ) -> list[SimulaeNode]:
        return [item for item in targets or [] if isinstance(item, SimulaeNode)]

    def _effects(self, effects: list[Any] | tuple[Any, ...] | None) -> list[Any]:
        return [
            effect
            for effect in effects or []
            if getattr(effect, "ID", None) and effect.ID != self.ID
        ]

    def _participant_ids(
        self,
        values: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        fallback: SimulaeNode | str | None = None,
    ) -> list[str]:
        ids = []
        items = list(values or [])

        if fallback is not None:
            items.append(fallback)

        for item in items:
            item_id = item.ID if isinstance(item, SimulaeNode) else item
            if item_id and item_id not in ids:
                ids.append(str(item_id))

        return ids


__all__ = ["SimulaeEffect", "SimulaeEffectActionType"]
