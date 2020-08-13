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
    SCANNING = 7
    CALIBRATING = 8


# Translating all variations of status messages to their meaning
RAW_TO_INTERNAL = {
    "EN": {
        "sleeping...": State.SLEEPING,
        "sleeping....": State.SLEEPING,
        "warming up": State.WARMING_UP,
        "ready to copy": State.READY,
        "replace toner": State.READY,
        "warming up. please wait": State.WARMING_UP,
        "printing": State.PRINTING,
        "scanning": State.SCANNING,
        "calibrating... please wait": State.CALIBRATING,
    },
    "DE": {
        "sparbetrieb...": State.SLEEPING,
        "bereit: kopie": State.READY,
        "wird gedruckt...": State.PRINTING,
    },
    "RU": {
        "oжидaниe...": State.SLEEPING,
        "гoтoв к кoпиp.": State.READY,
        "идeт пeчaть...": State.PRINTING,
    },
    "FR": {
        "veille...": State.SLEEPING,
        "pret a copier": State.READY,
        "chauffage": State.WARMING_UP,
        "impression...": State.PRINTING,
    },
    "IT": {
        "in attesa...": State.SLEEPING,
        "copia pronta": State.READY,
        "riscaldamento": State.WARMING_UP,
        "stampa ...": State.PRINTING,
    },
}


# Adds menue items that are mapped to "Ready" state
_MENUE_ITEMS = {
    "EN": [
        "Basic Copy",
        "Auto Fit Copy",
        "Custom Copy",
        "ID Copy",
        "N-Up Copy",
        "Book Copy",
        "Local PC",
        "Network PC",
        "FTP",
        "SMB",
        "Email",
        "USB",
        "Shared Folder",
        "Memory Send",
        "On Hook Dial",
        "Delayed Send",
        "Redial",
        "Group Dial Send",
        "Speed Dial Send",
        "Edit Home",
        "Machine Setup",
        "Admin Setup",
    ]
}
for lang, items in _MENUE_ITEMS.items():
    for raw in items:
        RAW_TO_INTERNAL[lang][raw] = State.READY


ANY_LANGUAGE = {}
for mapping in RAW_TO_INTERNAL.values():
    ANY_LANGUAGE.update(mapping)

INTERNAL_TO_HUMAN = {
    "EN": {
        State.SLEEPING: "Sleeping",
        State.WARMING_UP: "Warming Up",
        State.OFFLINE: "Offline",
        State.READY: "Ready",
        State.UNKNOWN: "Unknown",
        State.PRINTING: "Printing",
        State.SCANNING: "Scanning",
        State.CALIBRATING: "Calibrating",
    },
    "DE": {
        State.SLEEPING: "Sparbetrieb",
        State.WARMING_UP: "Aufwärmen",
        State.OFFLINE: "Nicht erreichbar",
        State.READY: "Bereit",
        State.UNKNOWN: "Unbekannt",
        State.PRINTING: "Drucken",
        State.SCANNING: "Scannen",
        State.CALIBRATING: "Kalibrieren",
    },
    "RU": {
        State.SLEEPING: "Oжидaниe",
        State.WARMING_UP: "Разогрев",
        State.OFFLINE: "Не в сети",
        State.READY: "Гoтoв",
        State.UNKNOWN: "Неизвестно",
        State.PRINTING: "Идeт пeчaть",
        State.SCANNING: "сканирование",
        State.CALIBRATING: "калибровочный",
    },
}
