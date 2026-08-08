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
    STRING_MATCHES = 12,
    REGEX_MATCHES = 13,
    LIST_CONTAINS = 14,
    NOT_LIST_CONTAINS = 15

BASIC_RULES = [ConditionRuleType.EXISTS, ConditionRuleType.NOT_EXISTS]
NUMERIC_RULES = [ConditionRuleType.EQUALS, ConditionRuleType.NOT_EQUALS,
                 ConditionRuleType.LESS_THAN, ConditionRuleType.LESS_THAN_OR_EQUAL,
                 ConditionRuleType.GREATER_THAN, ConditionRuleType.GREATER_THAN_OR_EQUAL,
                 ConditionRuleType.WITHIN_RANGE, ConditionRuleType.BEYOND_RANGE]
STRING_RULES = [ConditionRuleType.STRING_CONTAINS,
                ConditionRuleType.STRING_MATCHES,
                ConditionRuleType.REGEX_MATCHES]
LIST_RULES = [ConditionRuleType.LIST_CONTAINS,
              ConditionRuleType.NOT_LIST_CONTAINS]