"""Connect to a Samsung printer with SyncThru service."""

import demjson

import asyncio
import aiohttp
import async_timeout

from typing import Any, Dict

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

    def __init__(self, ip, loop, session) -> None:
        """Initialize the the printer."""
        self.url = construct_url(ip)
        self._loop = loop
        self._session = session
        self.data = {}  # type: Dict[str, Any]

    async def update(self) -> None:
        """
        Retrieve the data from the printer.
        Throws ValueError if host does not support SyncThru
        """
        url = '{}{}'.format(self.url, ENDPOINT)

        try:
            async with async_timeout.timeout(5, loop=self._loop):
                response = await self._session.get(url)
            json_dict = demjson.decode(await response.text(), strict=False)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            json_dict = {'status': {'status1': SyncThru.OFFLINE}}
        except demjson.JSONDecodeError:
            raise ValueError("Invalid host, does not support SyncThru.")
        except (KeyError, ValueError):
            json_dict = {}
        self.data = json_dict

    @staticmethod
    def device_status_simple(status: str) -> str:
        """Convert the status1 field of the device status to a string."""
        return {
            '  Sleeping...   ': 'Sleeping',
            ' Ready to Copy  ': 'Ready',
            '   Warming Up   ': 'Warming up',
            SyncThru.OFFLINE: 'Offline',
        }.get(status, 'Unknown')

    def is_online(self) -> bool:
        """Return true if printer is online."""
        return (self.device_status() != SyncThru.OFFLINE
                and self.device_status() != 'Unknown')

    def model(self):
        """Return the model name of the printer."""
        try:
            return self.data.get('identity').get('model_name')
        except (KeyError, AttributeError):
            return self.device_status_simple('')

    def location(self):
        """Return the location of the printer."""
        try:
            return self.data.get('identity').get('location')
        except (KeyError, AttributeError):
            return self.device_status_simple('')

    def serial_number(self):
        """Return the serial number of the printer."""
        try:
            return self.data.get('identity').get('serial_num')
        except (KeyError, AttributeError):
            return self.device_status_simple('')

    def hostname(self):
        """Return the hostname of the printer."""
        try:
            return self.data.get('identity').get('host_name')
        except (KeyError, AttributeError):
            return self.device_status_simple('')

    def device_status(self):
        """Return the status of the device as string."""
        try:
            return self.device_status_simple(
                self.data.get('status').get('status1'))
        except (KeyError, AttributeError):
            return self.device_status_simple('')

    def capability(self) -> Dict[str, Any]:
        """Return the capabilities of the printer."""
        try:
            return self.data.get('capability', {})
        except (KeyError, AttributeError):
            return {}

    def raw(self):
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
