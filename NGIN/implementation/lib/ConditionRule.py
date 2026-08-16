from enum import Enum

class ConditionRuleType(Enum):
    EXISTS = 'EXISTS',
    NOT_EXISTS = 'NOT_EXISTS',
    EQUALS = '=',
    NOT_EQUALS = '!=',
    LESS_THAN = '<',
    LESS_THAN_OR_EQUAL = '<=',
    GREATER_THAN = '>',
    GREATER_THAN_OR_EQUAL = '>=',
    WITHIN_RANGE = 'BETWEEN',
    BEYOND_RANGE = 'NOT_BETWEEN',
    STRING_CONTAINS = 'CONTAINS',
    REGEX_MATCHES = 'R_MATCH',
    LIST_CONTAINS = 'IN',
    NOT_LIST_CONTAINS = 'NOT_IN'

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