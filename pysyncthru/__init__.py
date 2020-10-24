"""Connect to a Samsung printer with SyncThru service."""

import demjson

import aiohttp

from typing import Any, Dict, Optional, cast
from enum import Enum

ENDPOINT = "/sws/app/information/home/home.json"


class SyncthruState(Enum):
    INVALID = -1  # invalid state for values returned that are not in [1,5]
    OFFLINE = 0
    UNKNOWN = 1
    NORMAL = 2
    WARNING = 3
    TESTING = 4
    ERROR = 5


def construct_url(ip_address: str) -> str:
    """Construct the URL with a given IP address."""
    if "http://" not in ip_address and "https://" not in ip_address:
        ip_address = "{}{}".format("http://", ip_address)
    if ip_address[-1] == "/":
        ip_address = ip_address[:-1]
    return ip_address


class SyncThru:
    """Interface to communicate with the Samsung Printer with SyncThru."""

    COLOR_NAMES = ["black", "cyan", "magenta", "yellow"]
    TONER = "toner"
    DRUM = "drum"
    TRAY = "tray"

    def __init__(self, ip: str, session: aiohttp.ClientSession) -> None:
        """Initialize the the printer."""
        self.url = construct_url(ip)
        self._session = session
        self.data = {}  # type: Dict[str, Any]

    async def update(self) -> None:
        """
        Retrieve the data from the printer.
        Throws ValueError if host does not support SyncThru
        """
        url = "{}{}".format(self.url, ENDPOINT)

        try:
            async with self._session.get(url) as response:
                json_dict = demjson.decode(await response.text(), strict=False)
        except aiohttp.ClientError:
            json_dict = {"status": {"hrDeviceStatus": SyncthruState.OFFLINE.value}}
        except demjson.JSONDecodeError:
            raise ValueError("Invalid host, does not support SyncThru.")
        self.data = json_dict

    def is_online(self) -> bool:
        """Return true if printer is not offline."""
        return self.device_status() != SyncthruState.OFFLINE

    def is_unknown_state(self) -> bool:
        """
        Return true if printers exact state could not be retreived.
        Note that this is different from the fact that the printer
        itself might return an "unknown" state
        """
        return (
            self.device_status() == SyncthruState.OFFLINE
            or self.device_status() == SyncthruState.INVALID
        )

    def model(self) -> Optional[str]:
        """Return the model name of the printer."""
        try:
            return cast(Dict[str, str], self.data.get("identity", {})).get("model_name")
        except (KeyError, AttributeError):
            return None

    def location(self) -> Optional[str]:
        """Return the location of the printer."""
        try:
            return cast(Dict[str, str], self.data.get("identity", {})).get("location")
        except (KeyError, AttributeError):
            return None

    def serial_number(self) -> Optional[str]:
        """Return the serial number of the printer."""
        try:
            return cast(Dict[str, str], self.data.get("identity", {})).get("serial_num")
        except (KeyError, AttributeError):
            return None

    def hostname(self) -> Optional[str]:
        """Return the hostname of the printer."""
        try:
            return cast(Dict[str, str], self.data.get("identity", {})).get("host_name")
        except (KeyError, AttributeError):
            return None

    def device_status(self) -> SyncthruState:
        """Fetch the raw device status"""
        try:
            return SyncthruState(int(self.data.get("status", {}).get("hrDeviceStatus")))
        except (ValueError, TypeError):
            return SyncthruState.INVALID

    def device_status_details(self) -> str:
        """Return the detailed (display) status of the device as string."""
        head = self.data.get("status", {})
        status_display = [
            head.get("status{}".format(i), "").strip() for i in [1, 2, 3, 4]
        ]
        status_display = [x for x in status_display if x]  # filter out empty lines
        return " ".join(status_display).strip()

    def capability(self) -> Dict[str, Any]:
        """Return the capabilities of the printer."""
        try:
            return self.data.get("capability", {})
        except (KeyError, AttributeError):
            return {}

    def raw(self) -> Dict[str, Any]:
        """Return all details of the printer."""
        try:
            return self.data
        except (KeyError, AttributeError):
            return {}

    def toner_status(self, filter_supported: bool = True) -> Dict[str, Any]:
        """Return the state of all toners cartridges."""
        toner_status = {}
        for color in self.COLOR_NAMES:
            try:
                toner_stat = self.data.get("{}_{}".format(SyncThru.TONER, color), {})
                if filter_supported and toner_stat.get("opt", 0) == 0:
                    continue
                else:
                    toner_status[color] = toner_stat
            except (KeyError, AttributeError):
                toner_status[color] = {}
        return toner_status

    def input_tray_status(self, filter_supported: bool = True) -> Dict[str, Any]:
        """Return the state of all input trays."""
        tray_status = {}
        for tray in (
            *("{}_{}".format(SyncThru.TRAY, i) for i in range(1, 6)),
            "mp",  # TODO what does mp stand for?
            "manual",
        ):
            try:
                tray_stat = self.data.get(tray.replace("_", ""), {})
                if filter_supported and tray_stat.get("opt", 0) != 1:
                    continue
                else:
                    tray_status[tray] = tray_stat
            except (KeyError, AttributeError):
                tray_status[tray] = {}
        return tray_status

    def output_tray_status(self) -> Dict[int, Dict[str, str]]:
        """Return the state of all output trays."""
        tray_status = {}
        try:
            tray_stat = self.data.get("outputTray", [])
            for i, stat in enumerate(tray_stat):
                tray_status[i] = {
                    "name": stat[0],
                    "capacity": stat[1],
                    "status": stat[2],
                }
        except (KeyError, AttributeError):
            tray_status = {}
        return tray_status

    def drum_status(self, filter_supported: bool = True) -> Dict[str, Any]:
        """Return the state of all drums."""
        drum_status = {}
        for color in self.COLOR_NAMES:
            try:
                drum_stat = self.data.get("{}_{}".format(SyncThru.DRUM, color), {})
                if filter_supported and drum_stat.get("opt", 0) == 0:
                    continue
                else:
                    drum_status[color] = drum_stat
            except (KeyError, AttributeError):
                drum_status[color] = {}
        return drum_status
