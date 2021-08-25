import re
from html.parser import HTMLParser
from typing import Any, Callable, Dict, List, Tuple, Type

_VARIABLE_DICT = {
    "BlackTonerPer": lambda x: {
        "toner_black": {"opt": 1, "remaining": int(x), "newError": ""}
    },
    "tray1Status": lambda x: {"tray1": {"opt": 1, "newError": ""}},
    "tray2Installed": lambda x: {
        "tray2": {"opt": 1 if x == "Installed" else 0, "newError": ""}
    },
    "tray3Installed": lambda x: {
        "tray3": {"opt": 1 if x == "Installed" else 0, "newError": ""}
    },
    "tray4Installed": lambda x: {
        "tray4": {"opt": 1 if x == "Installed" else 0, "newError": ""}
    },
}  # type: Dict[str, Callable[[str], Dict[str, Any]]]
_KNOWN_VARIABLES = "|".join(_VARIABLE_DICT.keys())
_VARIABLES_REG = (
    r"var\s+(?P<varname>{})\s*=\s*[\"']?(?P<varval>[a-zA-Z0-9]+)[\"']?\s*;".format(
        _KNOWN_VARIABLES
    )
)

ENDPOINT_HTML_SUPPLIES_STATUS = "/Information/supplies_status.htm"
ENDPOINT_HTML_HOME = "/home.htm"
ENDPOINT_HTML_GENERAL_PROTOCOLS = "/Settings/Protocols/general_protocols.htm"


class SyncThruParser(HTMLParser):
    """
    General class of parsers that update a syncthru state dict
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self._data = data


class HomeParser(SyncThruParser):
    """
    Parser for the home.htm endpoint
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        if "identity" not in data:
            data["identity"] = {}

    _first_lcdFont = True
    _model_name = False
    _name_tag = False
    _name_key: str = ""
    _value_tag = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]) -> None:
        if tag == "font" and ("class", "lcdFont") in attrs:
            if self._first_lcdFont:
                self._model_name = True
                self._first_lcdFont = False
            else:
                self._name_tag = "color" not in map(lambda x: x[0], attrs)
                self._value_tag = not self._name_tag

    def handle_data(self, data: str) -> None:
        if self._model_name:
            self._data["identity"]["model_name"] = data.strip()
            self._model_name = False
        if self._name_tag:
            data = data.replace(":", "").strip().replace(" ", "_").lower()
            if data == "name":
                data = "host_name"
            self._name_key = data
            # we assume that the whole tag is read at once
            # (which is not necessarily true)
            self._name_tag = False
        if self._value_tag:
            self._data["identity"][self._name_key] = data.strip()
            # we assume that the whole tag is read at once
            # (which is not necessarily true)
            self._value_tag = False


class VariableParser(SyncThruParser):
    """
    Generic parser for variables declared in javascript
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    _inside_script = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]) -> None:
        if tag == "script" and (
            ("language", "javascript") in attrs or ("type", "text/javascript") in attrs
        ):
            self._inside_script = True

    def handle_data(self, data: str) -> None:
        # parse javascript variable declarations
        if self._inside_script:
            for match in re.finditer(_VARIABLES_REG, data):
                self._data.update(
                    _VARIABLE_DICT[match.group("varname")](match.group("varval"))
                )

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside_script = False


class GeneralProtocolParser(SyncThruParser):
    """
    Parser for the general_protocols.htm website
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        if "identity" not in data:
            data["identity"] = {}

    _name_tag = False
    _name_key: str = ""
    _value_tag = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]) -> None:
        if tag == "td":
            self._name_tag = ("class", "plainFont") in attrs
            self._value_tag = ("class", "valueFont") in attrs
        elif tag == "input" and self._value_tag and ("type", "text") in attrs:
            self._data["identity"][self._name_key] = dict(attrs)["value"]
            self._value_tag = False

    def handle_data(self, data: str) -> None:
        if self._name_tag:
            data = data.replace(":", "").strip().replace(" ", "_").lower()
            if data == "mac_address":
                data = "mac_addr"
            self._name_key = data
            # we assume that the whole tag is read at once
            # (which is not necessarily true)
            self._name_tag = False
        if self._value_tag:
            self._data["identity"][self._name_key] = data.strip()
            # we assume that the whole tag is read at once
            # (which is not necessarily true)
            self._value_tag = False


ENDPOINT_HTML_PARSERS: Dict[str, List[Type[SyncThruParser]]] = {
    ENDPOINT_HTML_HOME: [HomeParser, VariableParser],
    ENDPOINT_HTML_SUPPLIES_STATUS: [VariableParser],
    ENDPOINT_HTML_GENERAL_PROTOCOLS: [GeneralProtocolParser],
}
