"""Connect to a Samsung printer with SyncThru service."""

import demjson

import aiohttp

from typing import Any, Dict, Optional

from . import language as lng

ENDPOINT = "/sws/app/information/home/home.json"


def construct_url(ip_address: str) -> str:
    """Construct the URL with a given IP address."""
    if 'http://' not in ip_address and 'https://' not in ip_address:
        ip_address = '{}{}'.format('http://', ip_address)
    if ip_address[-1] == '/':
        ip_address = ip_address[:-1]
    return ip_address


class SyncThru:
    """Interface to communicate with the Samsung Printer with SyncThru."""
    COLOR_NAMES = ['black', 'cyan', 'magenta', 'yellow']
    TONER = 'toner'
    DRUM = 'drum'
    TRAY = 'tray'
    OFFLINE = 'Offline'

    def __init__(self, ip, session) -> None:
        """Initialize the the printer."""
        self.url = construct_url(ip)
        self._session = session
        self.data = {}  # type: Dict[str, Any]

    async def update(self) -> None:
        """
        Retrieve the data from the printer.
        Throws ValueError if host does not support SyncThru
        """
        url = '{}{}'.format(self.url, ENDPOINT)

        try:
            async with self._session.get(url) as response:
                json_dict = demjson.decode(await response.text(), strict=False)
        except aiohttp.ClientError:
            json_dict = {'status': {'status1': SyncThru.OFFLINE}}
        except demjson.JSONDecodeError:
            raise ValueError("Invalid host, does not support SyncThru.")
        self.data = json_dict

    @staticmethod
    def _device_status_internal(status: str, lang=None) -> lng.State:
        """Convert the status1 field of the device status to a string."""
        if lang:
            try:
                raw_to_internal_dict = lng.RAW_TO_INTERNAL[lang]
            except KeyError:
                raise ValueError(
                    "Language code {} not supported.".format(lang)
                )
        else:
            raw_to_internal_dict = lng.ANY_LANGUAGE
        raw_to_internal_dict[SyncThru.OFFLINE] = lng.State.OFFLINE
        return raw_to_internal_dict.get(status, lng.State.UNKNOWN)

    @staticmethod
    def _device_status_external(status: lng.State, lang="EN") -> str:
        """Convert the status1 field of the device status to a string."""
        try:
            internal_to_simple_dict = lng.INTERNAL_TO_HUMAN[lang]
        except KeyError:
            raise ValueError("Language code {} not supported.".format(lang))
        return internal_to_simple_dict[status]

    def is_online(self) -> bool:
        """Return true if printer is not offline."""
        return self._device_status() != lng.State.OFFLINE

    def is_unknown_state(self) -> bool:
        """Return true if printers exact state is unknow."""
        return (self._device_status() == lng.State.OFFLINE
                or self._device_status() == lng.State.UNKNOWN)

    def model(self) -> Optional[str]:
        """Return the model name of the printer."""
        try:
            return self.data.get('identity').get('model_name')
        except (KeyError, AttributeError):
            return None

    def location(self) -> Optional[str]:
        """Return the location of the printer."""
        try:
            return self.data.get('identity').get('location')
        except (KeyError, AttributeError):
            return None

    def serial_number(self) -> Optional[str]:
        """Return the serial number of the printer."""
        try:
            return self.data.get('identity').get('serial_num')
        except (KeyError, AttributeError):
            return None

    def hostname(self) -> Optional[str]:
        """Return the hostname of the printer."""
        try:
            return self.data.get('identity').get('host_name')
        except (KeyError, AttributeError):
            return None

    def _device_status(self, lang="EN") -> lng.State:
        """Fetch the raw device status converted to internal enum"""
        try:

            return self._device_status_internal(
                self.data.get('status').get('status1'), lang)
        except (KeyError, AttributeError):
            return lng.State.UNKNOWN

    def device_status(self, lang="EN") -> str:
        """Return the status of the device as string."""
        try:
            return self._device_status_external(
                self._device_status(lang), lang)
        except (KeyError, AttributeError):
            return self._device_status_external(lng.State.UNKNOWN, lang)

    def capability(self) -> Dict[str, Any]:
        """Return the capabilities of the printer."""
        try:
            return self.data.get('capability', {})
        except (KeyError, AttributeError):
            return {}

    def raw(self) -> Dict:
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
                toner_stat = self.data.get(
                    '{}_{}'.format(SyncThru.TONER, color), {})
                if filter_supported and toner_stat.get('opt', 0) == 0:
                    continue
                else:
                    toner_status[color] = toner_stat
            except (KeyError, AttributeError):
                toner_status[color] = {}
        return toner_status

    def input_tray_status(self,
                          filter_supported: bool = True) -> Dict[int, Any]:
        """Return the state of all input trays."""
        tray_status = {}
        for i in range(1, 5):
            try:
                tray_stat = self.data.get('{}{}'.format(SyncThru.TRAY, i), {})
                if filter_supported and tray_stat.get('opt', 0) == 0:
                    continue
                else:
                    tray_status[i] = tray_stat
            except (KeyError, AttributeError):
                tray_status[i] = {}
        return tray_status

    def output_tray_status(self) -> Dict[int, Dict[str, str]]:
        """Return the state of all output trays."""
        tray_status = {}
        try:
            tray_stat = self.data.get('outputTray', [])
            for i, stat in enumerate(tray_stat):
                tray_status[i] = {
                    'name': stat[0],
                    'capacity': stat[1],
                    'status': stat[2],
                }
        except (KeyError, AttributeError):
            tray_status = {}
        return tray_status

    def drum_status(self, filter_supported: bool = True) -> Dict[str, Any]:
        """Return the state of all drums."""
        drum_status = {}
        for color in self.COLOR_NAMES:
            try:
                drum_stat = self.data.get('{}_{}'.format(SyncThru.DRUM, color),
                                          {})
                if filter_supported and drum_stat.get('opt', 0) == 0:
                    continue
                else:
                    drum_status[color] = drum_stat
            except (KeyError, AttributeError):
                drum_status[color] = {}
        return drum_status
