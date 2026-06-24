from enum import Enum


class ErrorKind(Enum):
    AUTH = "auth"
    CONNECTION = "connection"
    PARSE = "parse"


class WindowKind(Enum):
    SESSION = "session"
    WEEKLY = "weekly"


class Color(Enum):
    GREEN = (46, 160, 67)
    YELLOW = (210, 153, 34)
    RED = (218, 54, 51)
    NEUTRAL = (140, 140, 140)
