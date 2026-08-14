from enum import Enum

class ConditionRuleType(Enum):
    EXISTS = 1,
    NOT_EXISTS = 2,
    EQUALS = 3,
    NOT_EQUALS = 4,
    LESS_THAN = 5,
    LESS_THAN_OR_EQUAL = 6,
    GREATER_THAN = 7,
    GREATER_THAN_OR_EQUAL = 8,
    WITHIN_RANGE = 9,
    BEYOND_RANGE = 10,
    STRING_CONTAINS = 11,
    REGEX_MATCHES = 13,
    LIST_CONTAINS = 14,
    NOT_LIST_CONTAINS = 15

BASIC_RULES = [ConditionRuleType.EXISTS, ConditionRuleType.NOT_EXISTS]

RANGE_RULES = [ConditionRuleType.WITHIN_RANGE, ConditionRuleType.BEYOND_RANGE]

NUMERIC_RULES = [ConditionRuleType.EQUALS, ConditionRuleType.NOT_EQUALS,
                 ConditionRuleType.LESS_THAN, ConditionRuleType.LESS_THAN_OR_EQUAL,
                 ConditionRuleType.GREATER_THAN, ConditionRuleType.GREATER_THAN_OR_EQUAL] + RANGE_RULES

STRING_RULES = [ConditionRuleType.EQUALS,
                ConditionRuleType.NOT_EQUALS,
                ConditionRuleType.STRING_CONTAINS,
                ConditionRuleType.REGEX_MATCHES]

LIST_RULES = [ConditionRuleType.LIST_CONTAINS,
              ConditionRuleType.NOT_LIST_CONTAINS]

CONDITION_RULE_ALIASES = {
    "exists": ConditionRuleType.EXISTS,
    "not-exists": ConditionRuleType.NOT_EXISTS,
    "equal": ConditionRuleType.EQUALS,
    "==": ConditionRuleType.EQUALS,
    "not-equal": ConditionRuleType.NOT_EQUALS,
    "!=": ConditionRuleType.NOT_EQUALS,
    "<": ConditionRuleType.LESS_THAN,
    "<=": ConditionRuleType.LESS_THAN_OR_EQUAL,
    ">": ConditionRuleType.GREATER_THAN,
    ">=": ConditionRuleType.GREATER_THAN_OR_EQUAL,
    "contains": ConditionRuleType.LIST_CONTAINS,
    "not-contains": ConditionRuleType.NOT_LIST_CONTAINS,
    "in": ConditionRuleType.LIST_CONTAINS,
    "not-in": ConditionRuleType.NOT_LIST_CONTAINS,
}