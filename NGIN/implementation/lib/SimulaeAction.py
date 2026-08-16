from __future__ import annotations

from enum import Enum
from typing import Any

from NGIN.implementation.lib.SimulaeCondition import SimulaeCondition
from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.implementation.lib.SimulaeSelector import SimulaeSelector
from NGIN.utilities.lib.SimulaeConstants import *


class SimulaeEffectActionType(str, Enum):
    SET = "set"
    UPDATE = "update"
    ADD = "add"
    REMOVE = "remove"
    INCREMENT = "increment"
    DECREMENT = "decrement"
    TRANSMUTE = "transmute"
    COMPOSE = "compose"
    DECOMPOSE = "decompose"
    TRIGGER_EFFECT = "trigger_effect"
    CREATE_EVENT = "create_event"
    CREATE_EVENTS = "create_events"


class SimulaeAction(SimulaeNode):
    """A small, loose action description that returns SimulaeEvents.

    Actions mutate accepted targets, then return event objects describing what
    happened. Callers should use those events as the observable result of action
    execution.
    """

    NODE_ROOTS = {
        ID: "ID",
        NODETYPE: "Nodetype",
        REFERENCES: "References",
        ATTRIBUTES: "Attributes",
        CHECKS: "Checks",
        ABILITIES: "Abilities",
        SCALES: "Scales",
        RELATIONS: "Relations",
        MEMORY: "Memory",
    }

    def __init__(
        self,
        action_type: SimulaeEffectActionType | str,
        *,
        conditions: list[SimulaeCondition] | tuple[SimulaeCondition, ...] | None = None,
        selectors: list[SimulaeSelector] | tuple[SimulaeSelector, ...] | None = None,
        acceptance_selector: SimulaeSelector | None = None,
        output_templates: Any = None,
        output_nodes: Any = None,
        values: Any = None,
        calculations: Any = None,
        given_id: str | None = None,
        name: str | None = None,
    ):
        super().__init__(given_id=given_id, nodetype=ACT, references={NAME: name} if name else {})

        self.action_type = self._action_type(action_type)
        self.conditions = self._typed_list(conditions, SimulaeCondition, "conditions")
        self.selectors = self._typed_list(selectors, SimulaeSelector, "selectors")
        self.acceptance_selector = self._optional_type(acceptance_selector, SimulaeSelector, "acceptance_selector")
        self.output_templates = self._list(output_templates)
        self.output_nodes = self._list(output_nodes)
        self.values = values
        self.calculations = calculations

        self.References[ACT] = self.action_type.value

    def act(
        self,
        *,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        effects: list[Any] | tuple[Any, ...] | None = None,
    ) -> list[SimulaeEvent]:
        return [
            event
            for node in self._targets(targets)
            if self._accepts(node)
            for event in self._act_on_node(
                node,
                sources=sources,
                observers=observers,
                effects=effects,
            )
        ]

    def apply(self, *args: Any, **kwargs: Any) -> list[SimulaeEvent]:
        return self.act(*args, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "action": self.action_type.value,
            "conditions": [condition.ID for condition in self.conditions],
            "selectors": len(self.selectors),
            "acceptance_selector": self.acceptance_selector is not None,
        }
        for key in ("output_templates", "output_nodes", "values", "calculations"):
            value = getattr(self, key)
            if value:
                data[key] = self._json_value(value)
        return data

    def _act_on_node(
        self,
        node: SimulaeNode,
        *,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        effects: list[Any] | tuple[Any, ...] | None,
    ) -> list[SimulaeEvent]:
        if self.action_type == SimulaeEffectActionType.TRIGGER_EFFECT:
            nested_events = [
                event
                for output in self._output_effects()
                for event in output.apply(
                    targets=[node],
                    sources=sources,
                    observers=observers,
                    effects=effects,
                )
            ]
            return [
                self._action_event(
                    "trigger_effect",
                    node,
                    sources=sources,
                    observers=observers,
                    effects=effects,
                    details={"nested_event_ids": [event.ID for event in nested_events]},
                ),
                *nested_events,
            ]

        if self.action_type in {SimulaeEffectActionType.CREATE_EVENT, SimulaeEffectActionType.CREATE_EVENTS}:
            return self._create_events(node, sources=sources, observers=observers, effects=effects)

        changes: list[dict[str, Any]] = []
        self._apply_state(node, changes)
        if not changes:
            return []
        return [
            self._action_event(
                "state_change",
                node,
                sources=sources,
                observers=observers,
                effects=effects,
                details={"changes": changes},
            )
        ]

    def _accepts(self, node: SimulaeNode) -> bool:
        if self.acceptance_selector and not self.acceptance_selector.matches(node):
            return False
        if any(not selector.matches(node) for selector in self.selectors):
            return False
        return all(condition.evaluate(node) for condition in self.conditions)

    def _apply_state(self, node: SimulaeNode, changes: list[dict[str, Any]]) -> None:
        for item in self._entries(self.values, self.action_type.value):
            if item["op"] == "remove":
                self._remove(node, item["path"], changes)
            else:
                self._set(node, item, changes)

        for item in self._entries(self.calculations, self.action_type.value):
            self._set(node, item, changes)

        for output in self.output_nodes:
            output_node, path = self._output_node(output)
            if not isinstance(output_node, SimulaeNode):
                continue
            operation = self._output_operation(output)
            if operation == "remove" or self.action_type in {SimulaeEffectActionType.REMOVE, SimulaeEffectActionType.DECOMPOSE}:
                self._remove_output_node(node, output_node, path, changes)
            else:
                self._add_output_node(node, output_node, path, changes)

        for template in self.output_templates:
            if isinstance(template, dict) and "path" in template and "value" in template:
                self._set(node, self._entry(template, self.action_type.value), changes)

    def _set(self, node: SimulaeNode, item: dict[str, Any], changes: list[dict[str, Any]]) -> None:
        parent, key, path = self._parent(node, item["path"], create=True)
        before = self._get(parent, key)
        after = item.get("value")
        op = item["op"]

        if op in {"increment", "increase", "decrement", "decrease", "add"} and self._number(before) and self._number(after):
            after = before - after if op in {"decrement", "decrease"} else before + after
        elif op == "add" and isinstance(before, list):
            after = [*before, after]
        elif op == "add" and isinstance(before, set):
            after = {*before, after}

        self._put(parent, key, after)
        changes.append(
            {
                "path": path,
                "operation": op,
                "before": self._json_value(before),
                "after": self._json_value(after),
            }
        )

    def _remove(self, node: SimulaeNode, path: Any, changes: list[dict[str, Any]]) -> None:
        parent, key, parsed = self._parent(node, path, create=False)
        before = self._get(parent, key)
        applied = isinstance(parent, dict) and key in parent
        if applied:
            parent.pop(key)
            changes.append(
                {
                    "path": parsed,
                    "operation": "remove",
                    "before": self._json_value(before),
                }
            )

    def _add_output_node(
        self,
        target: SimulaeNode,
        node: SimulaeNode,
        path: Any,
        changes: list[dict[str, Any]],
    ) -> None:
        relation = self._relation(path)
        if target.set_relation(node, relation_type=relation):
            changes.append(
                {
                    "path": [RELATIONS, relation, node.Nodetype, node.ID],
                    "operation": "output_node",
                    "after": self._json_value(node),
                }
            )

    def _remove_output_node(
        self,
        target: SimulaeNode,
        node: SimulaeNode,
        path: Any,
        changes: list[dict[str, Any]],
    ) -> None:
        relations = [self._relation(path)] if path else list(target.Relations.keys())
        applied = False
        for relation in relations:
            bucket = target.Relations.get(relation, {}).get(node.Nodetype, {})
            applied = bucket.pop(node.ID, None) is not None or applied
        if applied:
            changes.append(
                {
                    "path": [RELATIONS, node.Nodetype, node.ID],
                    "operation": "remove_output_node",
                    "before": self._json_value(node),
                }
            )

    def _create_events(
        self,
        target: SimulaeNode,
        *,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        effects: list[Any] | tuple[Any, ...] | None,
    ) -> list[SimulaeEvent]:
        templates = self.output_templates or [{}]
        if self.action_type == SimulaeEffectActionType.CREATE_EVENT:
            templates = templates[:1]
        return [
            self._event(template, target, sources=sources, observers=observers, effects=effects)
            for template in templates
            if isinstance(template, dict)
        ]

    def _event(
        self,
        template: dict[str, Any],
        target: SimulaeNode,
        *,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        effects: list[Any] | tuple[Any, ...] | None,
    ) -> SimulaeEvent:
        event = SimulaeEvent(
            template.get("id") or template.get("event_id") or f"{self.ID}-event",
            template.get("class") or template.get("event_class", "action"),
            template.get("type") or template.get("event_type", self.action_type.value),
            template.get("subtype") or template.get("event_subtype", "created"),
            template.get("start_timestamp"),
            template.get("end_timestamp"),
            self._event_sources(template, sources),
            self._participants(template.get("targets"), None if "targets" in template else target),
            self._participants(template["observers"] if "observers" in template else observers),
            self._effect_ids(effects),
        )
        self._annotate_event(event, template.get("details"))
        return event

    def _action_event(
        self,
        subtype: str,
        target: SimulaeNode,
        *,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        observers: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
        effects: list[Any] | tuple[Any, ...] | None,
        details: dict[str, Any] | None = None,
    ) -> SimulaeEvent:
        event = SimulaeEvent(
            f"{self.ID}-{target.ID}-{self.action_type.value}",
            "action",
            self.action_type.value,
            subtype,
            None,
            None,
            self._participants(sources),
            self._participants(None, target),
            self._participants(observers),
            self._effect_ids(effects),
        )
        self._annotate_event(event, details)
        return event

    def _annotate_event(self, event: SimulaeEvent, details: Any = None) -> None:
        event.References["action_occurred"] = True
        event.References["action_id"] = self.ID
        event.References["action_type"] = self.action_type.value
        if details:
            event.References["details"] = self._json_value(details)

    def _event_sources(
        self,
        template: dict[str, Any],
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
    ) -> list[str]:
        return self._participants(
            template["sources"] if "sources" in template else sources,
        )

    def _effect_ids(self, effects: list[Any] | tuple[Any, ...] | None) -> list[str]:
        return [
            effect.ID
            for effect in effects or []
            if getattr(effect, "ID", None)
        ]

    def _parent(self, node: SimulaeNode, path: Any, create: bool) -> tuple[Any, Any, list[Any]]:
        parsed = self._path(path)
        parent = getattr(node, self.NODE_ROOTS.get(str(parsed[0]), str(parsed[0])), None) if parsed else None
        for segment in parsed[1:-1]:
            child = parent.get(segment) if isinstance(parent, dict) else None
            if child is None and create and isinstance(parent, dict):
                child = parent[segment] = {}
            parent = child
        return parent, parsed[-1] if parsed else None, parsed

    def _entries(self, values: Any, default_op: str) -> list[dict[str, Any]]:
        if values is None:
            return []
        if isinstance(values, dict) and "path" in values:
            return [self._entry(values, default_op)]
        if isinstance(values, dict):
            return [self._entry({"path": path, "value": value}, default_op) for path, value in values.items()]
        if isinstance(values, (list, tuple)):
            return [self._entry(value if isinstance(value, dict) else {"path": value}, default_op) for value in values]
        return []

    def _entry(self, value: dict[str, Any], default_op: str) -> dict[str, Any]:
        return {
            "path": value.get("path"),
            "value": value.get("value", value.get("amount")),
            "op": value.get("operation") or value.get("operator") or value.get("op") or default_op,
        }

    def _output_effects(self) -> list[Any]:
        outputs = [item for item in [*self.output_templates, *self.output_nodes] if hasattr(item, "apply")]
        outputs.extend(item["effect"] for item in self.output_templates if isinstance(item, dict) and hasattr(item.get("effect"), "apply"))
        return outputs

    def _targets(self, targets: Any) -> list[SimulaeNode]:
        values = [] if targets is None else (list(targets) if isinstance(targets, (list, tuple, set)) else [targets])
        return [value for value in values if isinstance(value, SimulaeNode)]

    def _participants(self, values: Any = None, fallback: Any = None) -> list[str]:
        values = [] if values is None else (list(values) if isinstance(values, (list, tuple, set)) else [values])
        if fallback is not None:
            values.append(fallback)
        ids = []
        for value in values:
            value_id = value.ID if isinstance(value, SimulaeNode) else value
            if value_id and str(value_id) not in ids:
                ids.append(str(value_id))
        return ids

    def _path(self, path: Any) -> list[Any]:
        if isinstance(path, str):
            return [part for part in path.split(".") if part]
        return list(path) if isinstance(path, (list, tuple)) else []

    def _relation(self, path: Any) -> str:
        parsed = self._path(path)
        return str(parsed[1] if parsed and parsed[0] == RELATIONS and len(parsed) > 1 else parsed[0]) if parsed else CONTENTS

    def _output_node(self, output: Any) -> tuple[Any, Any]:
        return (output.get("node"), output.get("path")) if isinstance(output, dict) else (output, None)

    def _output_operation(self, output: Any) -> str | None:
        if not isinstance(output, dict):
            return None
        return output.get("operation") or output.get("op")

    def _get(self, parent: Any, key: Any) -> Any:
        return parent.get(key) if isinstance(parent, dict) else None

    def _put(self, parent: Any, key: Any, value: Any) -> None:
        if isinstance(parent, dict):
            parent[key] = value

    def _json_value(self, value: Any) -> Any:
        if hasattr(value, "ID") and hasattr(value, "Actions"):
            return {"effect_id": value.ID}
        if isinstance(value, SimulaeNode):
            return {"node_id": value.ID, "nodetype": value.Nodetype}
        if isinstance(value, dict):
            return {key: self._json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_value(item) for item in value]
        return value

    def _action_type(self, value: SimulaeEffectActionType | str) -> SimulaeEffectActionType:
        return value if isinstance(value, SimulaeEffectActionType) else SimulaeEffectActionType(str(value).strip().lower())

    def _typed_list(self, values: Any, expected_type: type, name: str) -> list[Any]:
        values = self._list(values)
        if any(not isinstance(value, expected_type) for value in values):
            raise TypeError(f"Action {name} must be {expected_type.__name__} instances")
        return values

    def _optional_type(self, value: Any, expected_type: type, name: str) -> Any:
        if value is not None and not isinstance(value, expected_type):
            raise TypeError(f"Action {name} must be a {expected_type.__name__} instance")
        return value

    def _list(self, value: Any) -> list[Any]:
        if value is None:
            return []
        return value if isinstance(value, list) else list(value) if isinstance(value, tuple) else [value]

    def _number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
