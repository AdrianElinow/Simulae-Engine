from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from NGIN.implementation.lib.ConditionRule import ConditionRuleType
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import (
    ABILITIES,
    ATTRIBUTES,
    CHECKS,
    COMPONENTS,
    CONTENTS,
    EFX,
    ID,
    MEMORY,
    NAME,
    NODETYPE,
    OBS,
    REFERENCES,
    RELATIONS,
    SRC,
    TGT,
)


EFFECT_ID_KEY = "effect_id"
EFFECT_NAME_KEY = "effect_name"
TARGET_ID_KEY = "target_id"
TARGET_IDS_KEY = "target_ids"
SOURCE_ID_KEY = "source_id"
SOURCE_IDS_KEY = "source_ids"
OBSERVER_IDS_KEY = "observer_ids"
APPLIED_KEY = "applied"
CONDITIONS_KEY = "conditions"
CONDITION_KEY = "condition"
PASSED_KEY = "passed"
ACTIONS_KEY = "actions"
TARGETS_KEY = "targets"
EVENTS_KEY = "events"
EVENT_KEY = "event"
EVENT_ID_KEY = "event_id"
EVENT_RELATIONS_KEY = "relations"
RESULT_KEY = "result"
ERROR_KEY = "error"
BEFORE_KEY = "before"
AFTER_KEY = "after"
BUCKET_KEY = "bucket"
CATEGORY_KEY = "category"
RELATION_TYPE_KEY = "relation_type"
REMOVED_KEY = "removed"
ADDED_KEY = "added"
ACTION_KEY = "action"
TYPE_KEY = "type"
FIELD_KEY = "field"
KEY_KEY = "key"
VALUE_KEY = "value"
PROPERTY_KEY = "property"
PATH_KEY = "path"
RULE_KEY = "rule"
EFFECT_KEY = "effect"
EVENT_SPECS_KEY = "event_specs"
EVENT_CLASS_KEY = "event_class"
EVENT_TYPE_KEY = "event_type"
EVENT_SUBTYPE_KEY = "event_subtype"
START_TIMESTAMP_KEY = "start_timestamp"
END_TIMESTAMP_KEY = "end_timestamp"
SOURCES_KEY = "sources"
EVENT_TARGETS_KEY = "targets"
OBSERVERS_KEY = "observers"
EFFECTS_KEY = "effects"
NODE_KEY = "node"
NODE_ID_KEY = "node_id"
ACTION_NODETYPE_KEY = "nodetype"
OLD_NODE_ID_KEY = "old_node_id"
OLD_NODETYPE_KEY = "old_nodetype"
EVENT_SPEC_ID_KEY = "id"


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
    "modify": SimulaeEffectActionType.UPDATE,
    "compose": SimulaeEffectActionType.ADD,
    "decompose": SimulaeEffectActionType.REMOVE,
    "effect": SimulaeEffectActionType.TRIGGER_EFFECT,
    "event": SimulaeEffectActionType.CREATE_EVENT,
    "events": SimulaeEffectActionType.CREATE_EVENTS,
}


CONDITION_RULE_ALIASES = {
    "present": ConditionRuleType.EXISTS,
    "missing": ConditionRuleType.NOT_EXISTS,
    "absent": ConditionRuleType.NOT_EXISTS,
    "equal": ConditionRuleType.EQUALS,
    "==": ConditionRuleType.EQUALS,
    "not_equal": ConditionRuleType.NOT_EQUALS,
    "!=": ConditionRuleType.NOT_EQUALS,
    "<": ConditionRuleType.LESS_THAN,
    "<=": ConditionRuleType.LESS_THAN_OR_EQUAL,
    ">": ConditionRuleType.GREATER_THAN,
    ">=": ConditionRuleType.GREATER_THAN_OR_EQUAL,
    "contains": ConditionRuleType.LIST_CONTAINS,
    "not_contains": ConditionRuleType.NOT_LIST_CONTAINS,
}


Action = dict[str, Any] | Callable[..., Any] | "SimulaeEffect"
Condition = dict[str, Any] | Callable[..., bool] | Any


class SimulaeEffect(SimulaeNode):
    """Data-driven state transition for SimulaeNodes.

    Effects are optional-condition-gated bundles of actions. They can mutate the target
    node's core state buckets, trigger nested effects, or emit SimulaeEvent
    records for the caller to persist.
    """

    def __init__(
        self,
        given_id: str | None = None,
        *,
        name: str | None = None,
        conditions: list[Condition] | None = None,
        actions: list[Action] | None = None,
        references: dict | None = None,
        attributes: dict | None = None,
        checks: dict | None = None,
        abilities: dict | None = None,
        relations: dict | None = None,
        memory: dict | None = None,
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

        self.Conditions = list(conditions or [])
        self.Actions = list(actions or [])

    def can_apply(
        self,
        target: SimulaeNode | None = None,
        *,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        source: SimulaeNode | str | None = None,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Return True when all configured conditions pass for every target."""

        target_nodes = self._normalize_targets(target, targets)
        source_values = self._normalize_values(source, sources)
        primary_source = self._first_node(source_values)

        return bool(target_nodes) and all(
            all(
                self._evaluate_condition(
                    condition,
                    target_node,
                    source=primary_source,
                    context=context,
                )
                for condition in self.Conditions
            )
            for target_node in target_nodes
        )

    def apply(
        self,
        target: SimulaeNode | None = None,
        *,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None = None,
        source: SimulaeNode | str | None = None,
        sources: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None = None,
        observers: list[SimulaeNode | str] | None = None,
        context: dict[str, Any] | None = None,
        create_event: bool = False,
    ) -> dict[str, Any]:
        """Apply this effect to one or more targets and return a structured report."""

        target_nodes = self._normalize_targets(target, targets)
        if not target_nodes:
            raise ValueError("SimulaeEffect.apply requires at least one target")

        source_values = self._normalize_values(source, sources)
        observer_values = self._normalize_values(None, observers)
        primary_source = self._first_node(source_values)

        report = {
            EFFECT_ID_KEY: self.ID,
            EFFECT_NAME_KEY: self.References.get(NAME),
            TARGET_ID_KEY: getattr(target_nodes[0], "ID", None),
            TARGET_IDS_KEY: [target_node.ID for target_node in target_nodes],
            SOURCE_ID_KEY: self._node_or_id(source_values[0]) if source_values else None,
            SOURCE_IDS_KEY: [self._node_or_id(source_value) for source_value in source_values],
            OBSERVER_IDS_KEY: [self._node_or_id(observer) for observer in observer_values],
            APPLIED_KEY: False,
            CONDITIONS_KEY: [],
            ACTIONS_KEY: [],
            TARGETS_KEY: [],
            EVENTS_KEY: [],
        }

        for target_node in target_nodes:
            target_report = self._apply_to_target(
                target_node,
                source=primary_source,
                sources=source_values,
                observers=observer_values,
                context=context,
            )
            report[TARGETS_KEY].append(target_report)
            report[EVENTS_KEY].extend(target_report[EVENTS_KEY])

        report[APPLIED_KEY] = any(target_report[APPLIED_KEY] for target_report in report[TARGETS_KEY])

        if len(report[TARGETS_KEY]) == 1:
            report[CONDITIONS_KEY] = report[TARGETS_KEY][0][CONDITIONS_KEY]
            report[ACTIONS_KEY] = report[TARGETS_KEY][0][ACTIONS_KEY]
        else:
            report[CONDITIONS_KEY] = [
                condition
                for target_report in report[TARGETS_KEY]
                for condition in target_report[CONDITIONS_KEY]
            ]
            report[ACTIONS_KEY] = [
                action for target_report in report[TARGETS_KEY] for action in target_report[ACTIONS_KEY]
            ]

        if create_event:
            report[EVENTS_KEY].append(
                self._create_event_action(
                    {
                        EVENT_CLASS_KEY: "effect",
                        EVENT_TYPE_KEY: self.References.get(NAME) or "effect_applied",
                        EVENT_SUBTYPE_KEY: "apply",
                    },
                    target_nodes[0],
                    targets=target_nodes,
                    source=primary_source,
                    sources=source_values,
                    observers=observer_values,
                )
            )

        return report

    def _apply_to_target(
        self,
        target: SimulaeNode,
        *,
        source: SimulaeNode | None,
        sources: list[SimulaeNode | str],
        observers: list[SimulaeNode | str],
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        report = {
            TARGET_ID_KEY: target.ID,
            APPLIED_KEY: False,
            CONDITIONS_KEY: [],
            ACTIONS_KEY: [],
            EVENTS_KEY: [],
        }

        for condition in self.Conditions:
            passed = self._evaluate_condition(condition, target, source=source, context=context)
            report[CONDITIONS_KEY].append({CONDITION_KEY: condition, PASSED_KEY: passed})
            if not passed:
                return report

        report[APPLIED_KEY] = True
        for action in self.Actions:
            report[ACTIONS_KEY].append(
                self._apply_action(
                    action,
                    target,
                    source=source,
                    sources=sources,
                    observers=observers,
                    context=context,
                )
            )
            report[EVENTS_KEY].extend(self._collect_events(report[ACTIONS_KEY][-1]))

        return report

    def _evaluate_condition(
        self,
        condition: Condition,
        target: SimulaeNode,
        *,
        source: SimulaeNode | None,
        context: dict[str, Any] | None,
    ) -> bool:
        if callable(condition):
            return bool(condition(target=target, source=source, context=context or {}))

        subject = self._node_subject(target)

        if hasattr(condition, "evaluate"):
            return bool(condition.evaluate(subject))

        if isinstance(condition, dict):
            property_path = condition.get(PROPERTY_KEY) or condition.get(PATH_KEY) or []
            expected = condition.get(VALUE_KEY)
            rule = self._normalize_condition_rule(condition.get(RULE_KEY, ConditionRuleType.EXISTS))
            actual = self._extract_property(subject, property_path)
            return self._evaluate_condition_rule(rule, actual, expected)

        return bool(condition)

    def _normalize_condition_rule(self, rule_value: Any) -> ConditionRuleType:
        if isinstance(rule_value, ConditionRuleType):
            return rule_value

        rule_text = str(rule_value).casefold()
        if rule_text.startswith("conditionruletype."):
            rule_text = rule_text.split(".", 1)[1]

        if rule_text in CONDITION_RULE_ALIASES:
            return CONDITION_RULE_ALIASES[rule_text]

        for rule in ConditionRuleType:
            if rule.name.casefold() == rule_text:
                return rule

        raise ValueError(f"Unsupported effect condition rule: {rule_value}")

    def _evaluate_condition_rule(self, rule: ConditionRuleType, actual: Any, expected: Any) -> bool:
        if rule == ConditionRuleType.EXISTS:
            return actual is not None
        if rule == ConditionRuleType.NOT_EXISTS:
            return actual is None
        if rule == ConditionRuleType.EQUALS:
            return actual == expected
        if rule == ConditionRuleType.NOT_EQUALS:
            return actual != expected
        if rule == ConditionRuleType.LESS_THAN:
            return actual < expected
        if rule == ConditionRuleType.LESS_THAN_OR_EQUAL:
            return actual <= expected
        if rule == ConditionRuleType.GREATER_THAN:
            return actual > expected
        if rule == ConditionRuleType.GREATER_THAN_OR_EQUAL:
            return actual >= expected
        if rule == ConditionRuleType.WITHIN_RANGE:
            return isinstance(expected, (list, tuple)) and len(expected) == 2 and expected[0] <= actual <= expected[1]
        if rule == ConditionRuleType.BEYOND_RANGE:
            return isinstance(expected, (list, tuple)) and len(expected) == 2 and (actual < expected[0] or actual > expected[1])
        if rule in {ConditionRuleType.STRING_CONTAINS, ConditionRuleType.LIST_CONTAINS}:
            return expected in actual
        if rule == ConditionRuleType.STRING_MATCHES:
            return actual == expected
        if rule == ConditionRuleType.REGEX_MATCHES:
            import re

            return bool(re.compile(str(expected), re.IGNORECASE).match(str(actual)))
        if rule == ConditionRuleType.NOT_LIST_CONTAINS:
            return expected not in actual
        raise ValueError(f"Unsupported effect condition rule: {rule}")

    def _apply_action(
        self,
        action: Action,
        target: SimulaeNode,
        *,
        source: SimulaeNode | None,
        sources: list[SimulaeNode | str],
        observers: list[SimulaeNode | str] | None,
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if isinstance(action, SimulaeEffect):
            nested_report = action.apply(
                target,
                source=source,
                sources=sources,
                observers=observers,
                context=context,
            )
            return {
                ACTION_KEY: SimulaeEffectActionType.TRIGGER_EFFECT.value,
                APPLIED_KEY: nested_report[APPLIED_KEY],
                EFFECT_ID_KEY: action.ID,
                RESULT_KEY: nested_report,
            }

        if callable(action):
            return {
                ACTION_KEY: SimulaeEffectActionType.CALLABLE.value,
                APPLIED_KEY: True,
                RESULT_KEY: action(target=target, source=source, context=context or {}),
            }

        if not isinstance(action, dict):
            return {
                ACTION_KEY: SimulaeEffectActionType.UNSUPPORTED.value,
                APPLIED_KEY: False,
                ERROR_KEY: "Unsupported action",
            }

        action_type = self._normalize_action_type(action.get(ACTION_KEY) or action.get(TYPE_KEY))
        bucket = str(action.get(BUCKET_KEY) or action.get(FIELD_KEY) or "").casefold()

        if action_type == SimulaeEffectActionType.TRIGGER_EFFECT:
            nested_effect = action.get(EFFECT_KEY)
            if not isinstance(nested_effect, SimulaeEffect):
                return {
                    ACTION_KEY: action_type.value,
                    APPLIED_KEY: False,
                    ERROR_KEY: "Nested effect action requires a SimulaeEffect",
                }
            return self._apply_action(
                nested_effect,
                target,
                source=source,
                sources=sources,
                observers=observers,
                context=context,
            )

        if action_type == SimulaeEffectActionType.CREATE_EVENTS or (
            action_type == SimulaeEffectActionType.CREATE_EVENT
            and isinstance(action.get(EVENTS_KEY), list)
        ):
            return self._create_events_action(
                action,
                target,
                source=source,
                sources=sources,
                observers=observers,
            )

        if action_type == SimulaeEffectActionType.CREATE_EVENT:
            return self._create_event_action(
                action,
                target,
                source=source,
                sources=sources,
                observers=observers,
            )

        if action_type in {
            SimulaeEffectActionType.ADD,
            SimulaeEffectActionType.SET,
            SimulaeEffectActionType.UPDATE,
            SimulaeEffectActionType.REMOVE,
            SimulaeEffectActionType.DELETE,
            SimulaeEffectActionType.INCREMENT,
            SimulaeEffectActionType.DECREMENT,
            SimulaeEffectActionType.TOGGLE,
            SimulaeEffectActionType.TRANSMUTE,
        }:
            if bucket in {"reference", "references"}:
                return self._apply_mapping_action(target.References, action, action_type, REFERENCES)
            if bucket in {"attribute", "attributes"}:
                return self._apply_mapping_action(target.Attributes, action, action_type, ATTRIBUTES)
            if bucket in {"check", "checks"}:
                return self._apply_mapping_action(target.Checks, action, action_type, CHECKS)
            if bucket in {"ability", "abilities"}:
                return self._apply_mapping_action(target.Abilities, action, action_type, ABILITIES)
            if bucket in {"memory", "memories"}:
                return self._apply_memory_action(target, action, action_type)
            if bucket in {"relation", "relations"}:
                return self._apply_relation_action(target, action, action_type)

        return {
            ACTION_KEY: action_type.value,
            APPLIED_KEY: False,
            ERROR_KEY: "Unsupported action",
        }

    def _normalize_action_type(self, action_type_value: Any) -> SimulaeEffectActionType:
        if isinstance(action_type_value, SimulaeEffectActionType):
            return action_type_value

        action_text = str(action_type_value or "").casefold()
        if action_text.startswith("simulaeeffectactiontype."):
            action_text = action_text.split(".", 1)[1]

        if action_text in ACTION_ALIASES:
            return ACTION_ALIASES[action_text]

        for action_type in SimulaeEffectActionType:
            if action_type.value == action_text or action_type.name.casefold() == action_text:
                return action_type

        return SimulaeEffectActionType.UNSUPPORTED

    def _apply_mapping_action(
        self,
        mapping: dict,
        action: dict[str, Any],
        action_type: SimulaeEffectActionType,
        bucket_name: str,
    ) -> dict[str, Any]:
        key = action.get(KEY_KEY)
        value = action.get(VALUE_KEY)

        if not key:
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: bucket_name,
                APPLIED_KEY: False,
                ERROR_KEY: "Mapping actions require a key",
            }

        before = mapping.get(key)

        if action_type in {SimulaeEffectActionType.REMOVE, SimulaeEffectActionType.DELETE}:
            existed = key in mapping
            if existed:
                del mapping[key]
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: bucket_name,
                KEY_KEY: key,
                BEFORE_KEY: before,
                AFTER_KEY: None,
                APPLIED_KEY: existed,
            }

        if action_type == SimulaeEffectActionType.INCREMENT:
            value = (before or 0) + value
        elif action_type == SimulaeEffectActionType.DECREMENT:
            value = (before or 0) - value
        elif action_type == SimulaeEffectActionType.TOGGLE:
            value = not bool(before)

        mapping[key] = value
        return {
            ACTION_KEY: action_type.value,
            BUCKET_KEY: bucket_name,
            KEY_KEY: key,
            BEFORE_KEY: before,
            AFTER_KEY: mapping.get(key),
            APPLIED_KEY: True,
        }

    def _apply_memory_action(
        self,
        target: SimulaeNode,
        action: dict[str, Any],
        action_type: SimulaeEffectActionType,
    ) -> dict[str, Any]:
        category = action.get(CATEGORY_KEY)
        key = action.get(KEY_KEY)
        value = action.get(VALUE_KEY)

        if not category or not key:
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: MEMORY,
                APPLIED_KEY: False,
                ERROR_KEY: "Memory actions require category and key",
            }

        memory_bucket = target.Memory.setdefault(category, {})
        before = memory_bucket.get(key)

        if action_type in {SimulaeEffectActionType.REMOVE, SimulaeEffectActionType.DELETE}:
            existed = key in memory_bucket
            if existed:
                del memory_bucket[key]
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: MEMORY,
                CATEGORY_KEY: category,
                KEY_KEY: key,
                BEFORE_KEY: before,
                AFTER_KEY: None,
                APPLIED_KEY: existed,
            }

        memory_bucket[key] = value
        return {
            ACTION_KEY: action_type.value,
            BUCKET_KEY: MEMORY,
            CATEGORY_KEY: category,
            KEY_KEY: key,
            BEFORE_KEY: before,
            AFTER_KEY: memory_bucket.get(key),
            APPLIED_KEY: True,
        }

    def _apply_relation_action(
        self,
        target: SimulaeNode,
        action: dict[str, Any],
        action_type: SimulaeEffectActionType,
    ) -> dict[str, Any]:
        relation_type = action.get(RELATION_TYPE_KEY) or CONTENTS
        node = action.get(NODE_KEY)
        node_id = action.get(NODE_ID_KEY) or getattr(node, "ID", None)
        nodetype = action.get(ACTION_NODETYPE_KEY) or getattr(node, "Nodetype", None)

        if action_type == SimulaeEffectActionType.TRANSMUTE:
            remove_report = self._apply_relation_action(
                target,
                {
                    RELATION_TYPE_KEY: relation_type,
                    NODE_ID_KEY: action.get(OLD_NODE_ID_KEY) or node_id,
                    ACTION_NODETYPE_KEY: action.get(OLD_NODETYPE_KEY) or nodetype,
                },
                SimulaeEffectActionType.REMOVE,
            )
            add_report = self._apply_relation_action(target, action, SimulaeEffectActionType.ADD)
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: RELATIONS,
                RELATION_TYPE_KEY: relation_type,
                REMOVED_KEY: remove_report,
                ADDED_KEY: add_report,
                APPLIED_KEY: bool(remove_report.get(APPLIED_KEY) or add_report.get(APPLIED_KEY)),
            }

        if action_type in {
            SimulaeEffectActionType.ADD,
            SimulaeEffectActionType.SET,
            SimulaeEffectActionType.UPDATE,
        }:
            if not isinstance(node, SimulaeNode):
                return {
                    ACTION_KEY: action_type.value,
                    BUCKET_KEY: RELATIONS,
                    APPLIED_KEY: False,
                    ERROR_KEY: "Relation add/set/update actions require a SimulaeNode",
                }
            applied = target.set_relation(node, relation_type=relation_type)
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: RELATIONS,
                RELATION_TYPE_KEY: relation_type,
                NODE_ID_KEY: node.ID,
                ACTION_NODETYPE_KEY: node.Nodetype,
                APPLIED_KEY: applied,
            }

        if action_type in {SimulaeEffectActionType.REMOVE, SimulaeEffectActionType.DELETE}:
            relation_bucket = target.Relations.get(relation_type, {}).get(nodetype, {})
            existed = bool(node_id and node_id in relation_bucket)
            if existed:
                del relation_bucket[node_id]
            return {
                ACTION_KEY: action_type.value,
                BUCKET_KEY: RELATIONS,
                RELATION_TYPE_KEY: relation_type,
                NODE_ID_KEY: node_id,
                ACTION_NODETYPE_KEY: nodetype,
                APPLIED_KEY: existed,
            }

        return {
            ACTION_KEY: action_type.value,
            BUCKET_KEY: RELATIONS,
            APPLIED_KEY: False,
            ERROR_KEY: "Unsupported relation action",
        }

    def _create_event_action(
        self,
        action: dict[str, Any],
        target: SimulaeNode,
        *,
        source: SimulaeNode | None,
        sources: list[SimulaeNode | str] | None,
        targets: list[SimulaeNode] | None = None,
        observers: list[SimulaeNode | str] | None,
    ) -> dict[str, Any]:
        from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent

        event_sources = action.get(SOURCES_KEY)
        if event_sources is None:
            event_sources = [self._node_or_id(source_value) for source_value in sources or []]
            if not event_sources and source:
                event_sources = [source.ID]

        event_observers = action.get(OBSERVERS_KEY)
        if event_observers is None:
            event_observers = [self._node_or_id(observer) for observer in observers or []]

        event_targets = action.get(EVENT_TARGETS_KEY)
        if event_targets is None:
            if targets:
                event_targets = [target_node.ID for target_node in targets]
            else:
                event_targets = [target.ID]

        event = SimulaeEvent(
            action.get(EVENT_SPEC_ID_KEY) or None,
            action.get(EVENT_CLASS_KEY) or "effect",
            action.get(EVENT_TYPE_KEY) or self.References.get(NAME) or "effect",
            action.get(EVENT_SUBTYPE_KEY) or "apply",
            action.get(START_TIMESTAMP_KEY),
            action.get(END_TIMESTAMP_KEY),
            event_sources,
            event_targets,
            event_observers,
            action.get(EFFECTS_KEY) or [self.ID],
        )

        return {
            ACTION_KEY: SimulaeEffectActionType.CREATE_EVENT.value,
            APPLIED_KEY: True,
            EVENT_KEY: event,
            EVENT_ID_KEY: event.ID,
            RELATIONS: {
                SRC: event.source_ids,
                TGT: event.target_ids,
                OBS: event.observer_ids,
            },
        }

    def _create_events_action(
        self,
        action: dict[str, Any],
        target: SimulaeNode,
        *,
        source: SimulaeNode | None,
        sources: list[SimulaeNode | str] | None,
        observers: list[SimulaeNode | str] | None,
    ) -> dict[str, Any]:
        event_specs = action.get(EVENTS_KEY) or action.get(EVENT_SPECS_KEY) or []
        if not isinstance(event_specs, list):
            return {
                ACTION_KEY: SimulaeEffectActionType.CREATE_EVENTS.value,
                APPLIED_KEY: False,
                ERROR_KEY: "create_events actions require an events list",
            }

        common = {
            key: value
            for key, value in action.items()
            if key not in {ACTION_KEY, TYPE_KEY, EVENTS_KEY, EVENT_SPECS_KEY}
        }
        event_reports = []

        for event_spec in event_specs:
            if not isinstance(event_spec, dict):
                event_reports.append(
                    {
                        ACTION_KEY: SimulaeEffectActionType.CREATE_EVENT.value,
                        APPLIED_KEY: False,
                        ERROR_KEY: "Event specs must be dictionaries",
                    }
                )
                continue

            event_action = dict(common)
            event_action.update(event_spec)
            event_reports.append(
                self._create_event_action(
                    event_action,
                    target,
                    source=source,
                    sources=sources,
                    observers=observers,
                )
            )

        return {
            ACTION_KEY: SimulaeEffectActionType.CREATE_EVENTS.value,
            APPLIED_KEY: any(event_report.get(APPLIED_KEY) for event_report in event_reports),
            EVENTS_KEY: event_reports,
        }

    def _collect_events(self, action_report: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        if (
            action_report.get(ACTION_KEY) == SimulaeEffectActionType.CREATE_EVENT.value
            and action_report.get(APPLIED_KEY)
        ):
            events.append(action_report)

        for event_report in action_report.get(EVENTS_KEY, []):
            if isinstance(event_report, dict) and event_report.get(APPLIED_KEY):
                events.append(event_report)

        nested_result = action_report.get(RESULT_KEY)
        if isinstance(nested_result, dict):
            events.extend(nested_result.get(EVENTS_KEY, []))

        return events

    def _node_subject(self, node: SimulaeNode) -> dict[str, Any]:
        return {
            ID: node.ID,
            NODETYPE: node.Nodetype,
            REFERENCES: node.References,
            ATTRIBUTES: node.Attributes,
            RELATIONS: node.Relations,
            CHECKS: node.Checks,
            ABILITIES: node.Abilities,
            MEMORY: node.Memory,
        }

    def _extract_property(self, subject: Any, property_path: list[str] | tuple[str, ...] | str) -> Any:
        if isinstance(property_path, str):
            property_path = property_path.split(".") if property_path else []

        current = subject
        for part in property_path:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _node_or_id(self, value: SimulaeNode | str) -> str:
        return value.ID if isinstance(value, SimulaeNode) else value

    def _normalize_targets(
        self,
        target: SimulaeNode | None,
        targets: list[SimulaeNode] | tuple[SimulaeNode, ...] | None,
    ) -> list[SimulaeNode]:
        target_nodes = []
        if target is not None:
            target_nodes.append(target)
        if targets is not None:
            target_nodes.extend(list(targets))

        deduped = []
        seen_ids = set()
        for target_node in target_nodes:
            if not isinstance(target_node, SimulaeNode):
                raise TypeError("Effect targets must be SimulaeNode instances")
            if target_node.ID in seen_ids:
                continue
            seen_ids.add(target_node.ID)
            deduped.append(target_node)

        return deduped

    def _normalize_values(
        self,
        value: SimulaeNode | str | None,
        values: list[SimulaeNode | str] | tuple[SimulaeNode | str, ...] | None,
    ) -> list[SimulaeNode | str]:
        normalized = []
        if value is not None:
            normalized.append(value)
        if values is not None:
            normalized.extend(list(values))

        deduped = []
        seen_ids = set()
        for item in normalized:
            item_id = self._node_or_id(item)
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            deduped.append(item)

        return deduped

    def _first_node(self, values: list[SimulaeNode | str]) -> SimulaeNode | None:
        for value in values:
            if isinstance(value, SimulaeNode):
                return value
        return None
