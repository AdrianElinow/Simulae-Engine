import re
from typing import Any

from .SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import *
from NGIN.implementation.lib.ConditionRule import *

class SimulaeCondition(SimulaeNode):

    def __init__(self,
                 id):
        
        super().__init__(
            given_id=id,
            nodetype=CND,
        )

        self.rule: ConditionRuleType = ConditionRuleType.EXISTS
        self.value: Any = None
        self.property: list[str] = []

    def evaluate(self, subject) -> bool:

        extracted_value = self.extract_property(subject, self.property)

        if self.rule in BASIC_RULES:
            return self.evaluate_basic(extracted_value)
        elif self.rule in NUMERIC_RULES:
            return self.evaluate_numeric(extracted_value)
        elif self.rule in STRING_RULES:
            return self.evaluate_string(extracted_value)
        elif self.rule in LIST_RULES:
            return self.evaluate_list(extracted_value)
        
        return False # Default return if no conditions matched
        
    def extract_property(self, subject, property_path: list[str]) -> Any:
        current_value = subject
        for prop in property_path:
            if isinstance(current_value, dict) and prop in current_value:
                current_value = current_value[prop]
            else:
                return None
        return current_value

    def evaluate_basic(self, subject) -> bool:
        
        if self.rule == ConditionRuleType.EXISTS:
            return subject is not None
        elif self.rule == ConditionRuleType.NOT_EXISTS:
            return subject is None
        else:
            raise ValueError(f"Invalid rule for basic evaluation: {self.rule}")
        
    def evaluate_numeric(self, subject_value) -> bool:
        if not isinstance(subject_value, (int, float)):
            raise ValueError(f"Subject value must be numeric for numeric evaluation, got: {subject_value}")
        
        if self.rule == ConditionRuleType.EQUALS:
            return (subject_value == self.value)
        elif self.rule == ConditionRuleType.NOT_EQUALS:
            return (subject_value != self.value)
        elif self.rule == ConditionRuleType.LESS_THAN:
            return (subject_value < self.value)
        elif self.rule == ConditionRuleType.LESS_THAN_OR_EQUAL:
            return (subject_value <= self.value)
        elif self.rule == ConditionRuleType.GREATER_THAN:
            return (subject_value > self.value)
        elif self.rule == ConditionRuleType.GREATER_THAN_OR_EQUAL:
            return (subject_value >= self.value)
        elif self.rule == ConditionRuleType.WITHIN_RANGE:
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                lower_bound, upper_bound = self.value
                return (lower_bound <= subject_value <= upper_bound)
        elif self.rule == ConditionRuleType.BEYOND_RANGE:
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                lower_bound, upper_bound = self.value
                return ((subject_value < lower_bound) or (subject_value > upper_bound))
        else:
            raise ValueError(f"Invalid rule for numeric evaluation: {self.rule}")
        
        return False # Default return if no conditions matched
    
    def evaluate_string(self, subject_value) -> bool:
        if not isinstance(subject_value, str):
            raise ValueError(f"Subject value must be a string for string evaluation, got: {subject_value}")
        
        if self.rule == ConditionRuleType.STRING_CONTAINS:
            return (self.value in subject_value)
        elif self.rule == ConditionRuleType.STRING_MATCHES:
            return (subject_value == self.value)
        elif self.rule == ConditionRuleType.REGEX_MATCHES:
            pattern = re.compile(str(self.value), re.IGNORECASE)
            return bool(pattern.match(subject_value))
        else:
            raise ValueError(f"Invalid rule for string evaluation: {self.rule}")
        
        return False # Default return if no conditions matched

    def evaluate_list(self, subject_value) -> bool:
        if not isinstance(subject_value, (list, tuple, set)):
            raise ValueError(f"Subject value must be a list-like value for list evaluation, got: {subject_value}")

        return self.value in subject_value
