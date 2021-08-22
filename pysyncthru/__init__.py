"""Connect to a Samsung printer with SyncThru service."""

import asyncio
from enum import Enum
from typing import Any, Dict, Optional, cast

import aiohttp
import demjson

from .htmlparsers import HomeParser, VariableParser

ENDPOINT_API = "/sws/app/information/home/home.json"
ENDPOINT_HTML_SUPPLIES_STATUS = "/Information/supplies_status.htm"
ENDPOINT_HTML_HOME = "/home.htm"


class ConnectionMode(Enum):
    AUTO = -1
    API = 1
    HTML = 2


class SyncthruState(Enum):
    INVALID = -1  # invalid state for values returned that are not in [1,5]
    OFFLINE = 0
    UNKNOWN = 1  # not offline but unknown
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

    def __init__(
        self,
        ip: str,
        session: aiohttp.ClientSession,
        connection_mode: ConnectionMode = ConnectionMode.AUTO,
    ) -> None:
        """Initialize the the printer."""
        self.url = construct_url(ip)
        self._session = session
        self.data = {}  # type: Dict[str, Any]
        self.connection_mode = connection_mode

    async def update(self) -> None:
        """
        Retrieve the data from the printer and caches is in the class
        Throws ValueError if host does not support SyncThru
        """
        self.data = await self._current_data()

    async def _current_data(self) -> Dict[str, Any]:
        """
        Retrieve the data from the printer.
        Throws ValueError if host does not support SyncThru
        """
        data = {"status": {"hrDeviceStatus": SyncthruState.OFFLINE.value}}
        if self.connection_mode in [ConnectionMode.AUTO, ConnectionMode.API]:
            url = "{}{}".format(self.url, ENDPOINT_API)

            try:
                async with self._session.get(url) as response:
                    res = demjson.decode(
                        await response.text(), strict=False
                    )  # type: Dict[str, Any]
                    # if we get something back from this endpoint,
                    # we directly return it
                    return res
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
            except demjson.JSONDecodeError:
                if self.connection_mode != ConnectionMode.AUTO:
                    raise ValueError("Invalid host, does not support SyncThru.")

        if self.connection_mode in [ConnectionMode.AUTO, ConnectionMode.HTML]:

            home_url = "{}{}".format(self.url, ENDPOINT_HTML_HOME)
            identity_data: Dict[str, Any] = {}
            try:
                async with self._session.get(home_url) as response:
                    home_res = await response.text()
                HomeParser(identity_data).feed(home_res)
                VariableParser(data).feed(home_res)
                data["identity"] = identity_data
                data["status"]["hrDeviceStatus"] = SyncthruState.UNKNOWN.value
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass

            supplies_url = "{}{}".format(self.url, ENDPOINT_HTML_SUPPLIES_STATUS)
            try:
                async with self._session.get(supplies_url) as response:
                    supplies_res = await response.text()
                VariableParser(data).feed(supplies_res)
                data["status"]["hrDeviceStatus"] = SyncthruState.UNKNOWN.value
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass

        return data

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
            "mp",  # mp = multi-purpose
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
