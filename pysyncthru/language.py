"""
Store key-value pairs for each language

The pairs are stored as dictionaries mapping strings returned by the printer on simplified states
for internal parsing
"""

from enum import Enum


class State(Enum):
    OFFLINE = 1
    SLEEPING = 2
    WARMING_UP = 3
    READY = 4
    UNKNOWN = 5


RAW_TO_INTERNAL = {
    "EN": {
        '  Sleeping...   ': State.SLEEPING,
        ' Ready to Copy  ': State.READY,
        '   Warming Up   ': State.WARMING_UP,
    }
}

INTERNAL_TO_SIMPLE = {
    "EN": {
        State.SLEEPING: 'Sleeping',
        State.WARMING_UP: 'Warming Up',
        State.OFFLINE: 'Offline',
        State.READY: 'Ready',
        State.UNKNOWN: 'Unknown',
    }
}

