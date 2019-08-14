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
    PRINTING = 6


RAW_TO_INTERNAL = {
    "EN": {
        '  Sleeping...   ': State.SLEEPING,
        ' Ready to Copy  ': State.READY,
        '   Warming Up   ': State.WARMING_UP,
    },
    "DE": {
        ' Sparbetrieb... ': State.SLEEPING,
        ' Bereit: Kopie ': State.READY,
        'Wird gedruckt...': State.PRINTING,
    },
    "RU": {
        ' Oжидaниe... ': State.SLEEPING,
        ' Гoтoв к кoпиp. ': State.READY,
        ' Идeт пeчaть... ': State.PRINTING,
    }
}

ANY_LANGUAGE = {}
for _, mapping in RAW_TO_INTERNAL:
    ANY_LANGUAGE.update(mapping)

INTERNAL_TO_SIMPLE = {
    "EN": {
        State.SLEEPING: 'Sleeping',
        State.WARMING_UP: 'Warming Up',
        State.OFFLINE: 'Offline',
        State.READY: 'Ready',
        State.UNKNOWN: 'Unknown',
        State.PRINTING: 'Printing',
    },
    "DE": {
        State.SLEEPING: 'Sparbetrieb',
        State.WARMING_UP: 'Aufwärmen',
        State.OFFLINE: 'Nicht erreichbar',
        State.READY: 'Bereit',
        State.UNKNOWN: 'Unbekannt',
        State.PRINTING: 'Drucken',
    },
    "RU": {
        State.SLEEPING: 'Oжидaниe',
        State.WARMING_UP: 'прогревается',
        State.OFFLINE: 'отсутствует',
        State.READY: 'Гoтoв',
        State.UNKNOWN: 'неизвестно',
        State.PRINTING: 'Идeт пeчaть',
    },
}
