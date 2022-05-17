from enum import Enum


class HTTP_METHOD:
    GET = 'GET'
    POST = 'POST'


class RULES_CHECK_MODE(Enum):
    SUB_STR = 0
    FULL_PHRASE = 1
