"""Connect to a Samsung printer with SyncThru service."""

import asyncio
from enum import Enum
from typing import Any, Dict, Optional, cast

import aiohttp
import demjson3

from .htmlparsers import ENDPOINT_HTML_PARSERS

ENDPOINT_API = "/sws/app/information"
PRINTER_ENDPOINT = "/home/home.json"
COUNTER_ENDPOINT = "/counters/counters.json"



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

class DataType(Enum):
    PRINTER = 1
    COUNTER = 2

def construct_url(ip_address: str) -> str:
    """Construct the URL with a given IP address."""
    if "http://" not in ip_address and "https://" not in ip_address:
        ip_address = f'http://{ip_address}'
    if ip_address[-1] == "/":
        ip_address = ip_address[:-1]
    return ip_address


class SyncThruAPINotSupported(Exception):
    """Error raised when a printer does not provide access to a JSON based API."""
class SyncThruHTMLNotSupported(Exception):
    """Error raised when API does not provide access to a HTML scraping."""
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
        self.data_printer_status = {}  # type: Dict[str, Any]
        self.data_counter_status = {}  # type: Dict[str, Any]
        self.connection_mode = connection_mode

    async def update(self) -> None:
        """
        Retrieve the data from the printer and caches is in the class
        Throws ValueError if host does not support SyncThru
        """
        self.data_printer_status = await self._current_data(DataType.PRINTER)
        self.data_counter_status = await self._current_data(DataType.COUNTER)


    async def _current_data(self, datatype: Any) -> Dict[str, Any]:
        """
        Retrieve the data from the printer.
        Throws ValueError if host does not support SyncThru
        """
        if datatype is DataType.PRINTER:
            data = {"status": {"hrDeviceStatus": SyncthruState.OFFLINE.value}}
            if self.connection_mode in [ConnectionMode.AUTO, ConnectionMode.API]:
                url = f'{self.url}{ENDPOINT_API}{PRINTER_ENDPOINT}'
                try:
                    async with self._session.get(url) as response:
                        res = demjson3.decode(
                            await response.text(), strict=False
                        )  # type: Dict[str, Any]
                        # if we get something back from this endpoint,
                        # we directly return it
                        return res
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass
                except demjson3.JSONDecodeError:
                    # If no JSON data is provided but we want to only connect
                    # in this mode, raise an Exception
                    if self.connection_mode != ConnectionMode.AUTO:
                        raise SyncThruAPINotSupported(
                            "Invalid host, does not support SyncThru JSON API."
                        )

            if self.connection_mode in [ConnectionMode.AUTO, ConnectionMode.HTML]:

                any_connection_successful = False
                for endpoint_url, parsers in ENDPOINT_HTML_PARSERS.items():
                    html_url = "{}{}".format(self.url, endpoint_url)
                    try:
                        async with self._session.get(html_url) as response:
                            html_res = await response.text()
                        any_connection_successful = True
                        for parser in parsers:
                            parser(data).feed(html_res)
                        # if successful, set device status to unknown
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        pass
                if (
                    any_connection_successful
                    and data["status"]["hrDeviceStatus"] == SyncthruState.OFFLINE.value
                ):
                    data["status"]["hrDeviceStatus"] = SyncthruState.UNKNOWN.value
        elif datatype is DataType.COUNTER:
            if self.connection_mode in [ConnectionMode.AUTO, ConnectionMode.API]:
                url = f'{self.url}{ENDPOINT_API}{COUNTER_ENDPOINT}'
                print (f'In counter section with url {url}')
                try:
                    async with self._session.get(url) as response:
                        res_count = demjson3.decode(
                            await response.text(), strict=False
                        )  # type: Dict[str, Any]
                        # if we get something back from this endpoint,
                        # we directly return it
                        return res_count
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass
                except demjson3.JSONDecodeError:
                    # If no JSON data is provided but we want to only connect
                    # in this mode, raise an Exception
                    if self.connection_mode != ConnectionMode.AUTO:
                        raise SyncThruAPINotSupported(
                            "Invalid host, does not support SyncThru JSON API."
                        )
            #TODO Handle HTML Connection Mode. For the moment raise an exception
            else:
                raise SyncThruHTMLNotSupported("HTML scrapping not supported for counter data")

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

    def _identity_data(self, key: str) -> Optional[str]:
        try:
            return cast(Dict[str, str], self.data_printer_status.get("identity", {})).get(key)
        except (KeyError, AttributeError):
            return None

    def model(self) -> Optional[str]:
        """Return the model name of the printer."""
        return self._identity_data("model_name")

    def location(self) -> Optional[str]:
        """Return the location of the printer."""
        return self._identity_data("location")

    def serial_number(self) -> Optional[str]:
        """Return the serial number of the printer."""
        return self._identity_data("serial_num")

    def hostname(self) -> Optional[str]:
        """Return the hostname of the printer."""
        return self._identity_data("host_name")

    def mac_address(self) -> Optional[str]:
        """Return the MAC address of the printer."""
        return self._identity_data("mac_addr")

    def ip_address(self) -> Optional[str]:
        """Return the IP address of the printer."""
        return self._identity_data("ip_addr")

    def device_status(self) -> SyncthruState:
        """Fetch the raw device status"""
        try:
            return SyncthruState(int(self.data_printer_status.get("status", {}).get("hrDeviceStatus")))
        except (ValueError, TypeError):
            return SyncthruState.INVALID

    def device_status_details(self) -> str:
        """Return the detailed (display) status of the device as string."""
        head = self.data_printer_status.get("status", {})
        status_display = [
            head.get("status{}".format(i), "").strip() for i in [1, 2, 3, 4]
        ]
        status_display = [x for x in status_display if x]  # filter out empty lines
        return " ".join(status_display).strip()

    def capability(self) -> Dict[str, Any]:
        """Return the capabilities of the printer."""
        try:
            return self.data_printer_status.get("capability", {})
        except (KeyError, AttributeError):
            return {}

    def raw(self) -> Dict[str, Any]:
        """Return all details of the printer."""
        try:
            return self.data_printer_status
        except (KeyError, AttributeError):
            return {}

    def raw_counter(self) -> Dict[str, Any]:
        """Return all details of the printer."""
        try:
            return self.data_counter_status
        except (KeyError, AttributeError):
            return {}

    def toner_status(self, filter_supported: bool = True) -> Dict[str, Any]:
        """Return the state of all toners cartridges."""
        toner_status = {}
        for color in self.COLOR_NAMES:
            try:
                toner_stat = self.data_printer_status.get("{}_{}".format(SyncThru.TONER, color), {})
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
                tray_stat = self.data_printer_status.get(tray.replace("_", ""), {})
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
            tray_stat = self.data_printer_status.get("outputTray", [])
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
                drum_stat = self.data_printer_status.get("{}_{}".format(SyncThru.DRUM, color), {})
                if filter_supported and drum_stat.get("opt", 0) == 0:
                    continue
                else:
                    drum_status[color] = drum_stat
            except (KeyError, AttributeError):
                drum_status[color] = {}
        return drum_status

    def print_count(self) -> Optional[str]:
        """Return number of prints"""
        return self.data_counter_status.get("GXI_BILLING_PRINT_TOTAL_IMP_CNT")

    def copy_count(self) -> Optional[str]:
        """Return number of copies"""
        return self.data_counter_status.get("GXI_BILLING_COPY_TOTAL_IMP_CNT")