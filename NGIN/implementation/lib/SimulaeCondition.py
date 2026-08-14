import re
from typing import Any

from NGIN.implementation.lib.ConditionRule import (
    BASIC_RULES,
    LIST_RULES,
    NUMERIC_RULES,
    RANGE_RULES,
    STRING_RULES,
    ConditionRuleType,
)
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import (
    ABILITIES,
    ATTRIBUTES,
    CHECKS,
    CND,
    ID,
    MEMORY,
    NODETYPE,
    REFERENCES,
    RELATIONS,
)


class SimulaeCondition(SimulaeNode):
    """Condition meta-node that evaluates a rule against a target property."""

    def __init__(
        self,
        id,
        property_path: list[str] | None = None,
        rule: ConditionRuleType = ConditionRuleType.EXISTS,
        value: str | int | float | tuple | list | None = None,
        exclusivity: tuple[bool, bool] | None = None,
    ):
        super().__init__(
            given_id=id,
            nodetype=CND,
        )

        if not self._is_valid_property_path(property_path):
            raise ValueError("Must provide valid property path")
        if not isinstance(rule, ConditionRuleType):
            raise ValueError("Must provide valid rule type")

        self.property_path: list[str] = list(property_path or [])
        self.rule: ConditionRuleType = rule
        self.value: Any = None
        self.exclusivity: tuple[bool, bool] | None = None
        self._initialize_for_rule(value, exclusivity)

    def _initialize_for_rule(
        self,
        value: str | int | float | tuple | list | None,
        exclusivity: tuple[bool, bool] | None,
    ):
        if self.rule in BASIC_RULES:
            self.value = None
            self.exclusivity = None
            return

        if self.rule in RANGE_RULES:
            if not self._is_valid_numeric_range(value):
                raise ValueError("Must have valid tuple value for given numeric range")
            if exclusivity is not None and not self._is_valid_exclusivity(exclusivity):
                raise ValueError("Must have valid exclusivity values for given numeric range")
            self.value = tuple(value)
            self.exclusivity = exclusivity or (False, False)
            return

        if self.rule in {ConditionRuleType.EQUALS, ConditionRuleType.NOT_EQUALS}:
            if value is None:
                raise ValueError("Must have valid value for given equality rule")
            self.value = value
            self.exclusivity = None
            return

        if self.rule in NUMERIC_RULES:
            if not isinstance(value, (int, float)):
                raise ValueError("Must have valid value for given numeric rule")
            self.value = value
            self.exclusivity = None
            return

        if self.rule in STRING_RULES:
            if not isinstance(value, str):
                raise ValueError("Unable to perform string conditional comparison without valid condition value")
            self.value = value
            self.exclusivity = None
            return

        if self.rule in LIST_RULES:
            if value is None:
                raise ValueError("Must have valid value for given list rule")
            self.value = value
            self.exclusivity = None
            return

        raise ValueError(f"Unsupported condition rule: {self.rule}")

    def evaluate(self, target, **_context) -> bool:
        extracted_value = self.extract_property(target, self.property_path)

        if self.rule in BASIC_RULES:
            return self.evaluate_basic(extracted_value)

        if extracted_value is None:
            return False

        if self.rule == ConditionRuleType.EQUALS:
            return extracted_value == self.value
        if self.rule == ConditionRuleType.NOT_EQUALS:
            return extracted_value != self.value
        if self.rule in RANGE_RULES:
            return self.evaluate_numeric_range(extracted_value)
        if self.rule in NUMERIC_RULES:
            return self.evaluate_numeric(extracted_value)
        if self.rule in STRING_RULES:
            return self.evaluate_string(extracted_value)
        if self.rule in LIST_RULES:
            return self.evaluate_list(extracted_value)

        return False

    def extract_property(self, target, property_path: list[str]) -> Any:
        current_value = self._node_subject(target)

        for prop in property_path:
            if isinstance(current_value, dict) and prop in current_value:
                current_value = current_value[prop]
            elif hasattr(current_value, prop):
                current_value = getattr(current_value, prop)
            else:
                return None

        return current_value

    def evaluate_basic(self, target_property_value) -> bool:
        if self.rule == ConditionRuleType.EXISTS:
            return target_property_value is not None
        if self.rule == ConditionRuleType.NOT_EXISTS:
            return target_property_value is None

        raise ValueError(f"Invalid rule for basic evaluation: {self.rule}")

    def evaluate_numeric(self, target_property_value) -> bool:
        if not isinstance(target_property_value, (int, float)):
            raise ValueError(
                f"Target property value must be numeric for numeric evaluation, got: {target_property_value}"
            )

        if self.rule == ConditionRuleType.EQUALS:
            return target_property_value == self.value
        if self.rule == ConditionRuleType.NOT_EQUALS:
            return target_property_value != self.value
        if self.rule == ConditionRuleType.LESS_THAN:
            return target_property_value < self.value
        if self.rule == ConditionRuleType.LESS_THAN_OR_EQUAL:
            return target_property_value <= self.value
        if self.rule == ConditionRuleType.GREATER_THAN:
            return target_property_value > self.value
        if self.rule == ConditionRuleType.GREATER_THAN_OR_EQUAL:
            return target_property_value >= self.value

        raise ValueError(f"Invalid rule for numeric evaluation: {self.rule}")

    def evaluate_numeric_range(self, target_property_value) -> bool:
        if not isinstance(target_property_value, (int, float)):
            raise ValueError(
                f"Target property value must be numeric for numeric range evaluation, got: {target_property_value}"
            )

        low_value, high_value = self.value
        low_exclusive, high_exclusive = self.exclusivity or (False, False)
        above_low = target_property_value > low_value if low_exclusive else target_property_value >= low_value
        below_high = target_property_value < high_value if high_exclusive else target_property_value <= high_value

        if self.rule == ConditionRuleType.WITHIN_RANGE:
            return above_low and below_high
        if self.rule == ConditionRuleType.BEYOND_RANGE:
            return not (above_low and below_high)

        raise ValueError(f"Unhandled numeric range ruletype: {self.rule}")

    def evaluate_string(self, target_property_value) -> bool:
        if not isinstance(target_property_value, str):
            raise ValueError(
                f"Target property value must be a string for string evaluation, got: {target_property_value}"
            )

        if self.rule == ConditionRuleType.STRING_CONTAINS:
            return self.value in target_property_value
        if self.rule == ConditionRuleType.EQUALS:
            return target_property_value == self.value
        if self.rule == ConditionRuleType.NOT_EQUALS:
            return target_property_value != self.value
        if self.rule == ConditionRuleType.REGEX_MATCHES:
            pattern = re.compile(str(self.value), re.IGNORECASE)
            return bool(pattern.match(target_property_value))

        raise ValueError(f"Invalid rule for string evaluation: {self.rule}")

    def evaluate_list(self, target_property_value) -> bool:
        if not isinstance(target_property_value, (list, tuple, set)):
            raise ValueError(
                f"Target property value must be list-like for list evaluation, got: {target_property_value}"
            )

        if self.rule == ConditionRuleType.LIST_CONTAINS:
            return self.value in target_property_value
        if self.rule == ConditionRuleType.NOT_LIST_CONTAINS:
            return self.value not in target_property_value

        raise ValueError(f"Invalid rule for list evaluation: {self.rule}")

    def _node_subject(self, target) -> Any:
        if isinstance(target, SimulaeNode):
            return {
                ID: target.ID,
                NODETYPE: target.Nodetype,
                REFERENCES: target.References,
                ATTRIBUTES: target.Attributes,
                RELATIONS: target.Relations,
                CHECKS: target.Checks,
                ABILITIES: target.Abilities,
                MEMORY: target.Memory,
            }
        return target

    def _is_valid_property_path(self, property_path: list[str] | None) -> bool:
        return (
            isinstance(property_path, list)
            and len(property_path) > 0
            and all(isinstance(prop, str) and prop for prop in property_path)
        )

    def _is_valid_numeric_range(self, value: Any) -> bool:
        return (
            isinstance(value, (list, tuple))
            and len(value) == 2
            and all(isinstance(item, (int, float)) for item in value)
        )

    def _is_valid_exclusivity(self, exclusivity: Any) -> bool:
        return (
            isinstance(exclusivity, tuple)
            and len(exclusivity) == 2
            and all(isinstance(item, bool) for item in exclusivity)
        )
