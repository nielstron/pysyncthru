#!/usr/bin/env python
# -*- coding: utf-8 -*-

# general requirements
import unittest
from pathlib import Path

from .test_structure.server_control import Server
from .test_structure.syncthru_mock_server import SyncThruServer, SyncThruRequestHandler

# For the server in this case
import time

# For the tests
import aiohttp
import asyncio
from pysyncthru import SyncThru, SyncthruState, ConnectionMode, SyncThruAPINotSupported
from .web_raw.web_state import RAW_STATE1, RAW_HTML

ADDRESS = "localhost"


class SyncthruAPITest(unittest.TestCase):
    server = None
    server_control = None  # type: Server
    port = 0
    url = "http://localhost:80"
    syncthru = None  # type: SyncThru

    def setUp(self) -> None:
        # Create an arbitrary subclass of TCP Server as the server to be started
        # Here, it is an Simple HTTP file serving server
        handler = SyncThruRequestHandler

        max_retries = 10
        r = 0
        while not self.server:
            try:
                # Connect to any open port
                self.server = SyncThruServer((ADDRESS, 0), handler)
            except OSError:
                if r < max_retries:
                    r += 1
                else:
                    raise
                time.sleep(1)

        self.server_control = Server(self.server)
        self.port = self.server_control.get_port()
        self.url = "{}:{}".format(ADDRESS, self.port)
        # Start test server before running any tests
        self.server_control.start_server()

        async def fetch():
            async with aiohttp.ClientSession() as session:
                self.syncthru = SyncThru(
                    self.url, session, connection_mode=ConnectionMode.API
                )
                await self.syncthru.update()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())

    def test_online(self) -> None:
        self.assertTrue(self.syncthru.is_online())

    def test_status_normal(self) -> None:
        self.assertEqual(self.syncthru.device_status(), SyncthruState.NORMAL)

    def test_status_details(self) -> None:
        self.assertEqual(self.syncthru.device_status_details(), "Sleeping...")

    def test_model(self) -> None:
        self.assertEqual(self.syncthru.model(), RAW_STATE1["identity"]["model_name"])

    def test_toner_filter(self) -> None:
        self.assertDictEqual(
            self.syncthru.toner_status(True),
            {"black": {"opt": 1, "remaining": 58, "cnt": 229, "newError": ""}},
        )

    def test_toner_no_filter(self) -> None:
        empty = {"opt": 0, "remaining": 0, "cnt": 0, "newError": ""}
        self.assertDictEqual(
            self.syncthru.toner_status(False),
            {
                "yellow": empty,
                "magenta": empty,
                "cyan": empty,
                "black": {"opt": 1, "remaining": 58, "cnt": 229, "newError": ""},
            },
        )

    def test_input_tray_filter(self) -> None:
        self.assertDictEqual(
            self.syncthru.input_tray_status(True),
            {
                "tray_1": {
                    "capa": 150,
                    "newError": "",
                    "opt": 1,
                    "paper_size1": 4,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                }
            },
        )

    def test_input_tray_no_filter(self) -> None:
        self.assertDictEqual(
            self.syncthru.input_tray_status(False),
            {
                "tray_1": {
                    "capa": 150,
                    "newError": "",
                    "opt": 1,
                    "paper_size1": 4,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                },
                "tray_2": {
                    "capa": 0,
                    "newError": "",
                    "opt": 0,
                    "paper_size1": 0,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                },
                "tray_3": {
                    "capa": 0,
                    "newError": "",
                    "opt": 0,
                    "paper_size1": 0,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                },
                "tray_4": {
                    "capa": 0,
                    "newError": "",
                    "opt": 2,
                    "paper_size1": 0,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                },
                "tray_5": {
                    "opt": 0,
                    "paper_size1": 0,
                    "paper_size2": 0,
                    "paper_type1": 0,
                    "paper_type2": 0,
                    "capa": 0,
                    "newError": "0",
                },
                "mp": {
                    "opt": 0,
                    "paper_size1": 0,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                    "capa": 0,
                    "newError": "",
                },
                "manual": {
                    "opt": 0,
                    "paper_size1": 0,
                    "paper_size2": 0,
                    "paper_type1": 2,
                    "paper_type2": 0,
                    "capa": 0,
                    "newError": "",
                },
            },
        )

    def test_output_tray(self) -> None:
        self.assertEqual(
            self.syncthru.output_tray_status(),
            {0: {"capacity": 100, "name": 1, "status": ""}},
        )

    def test_drum_status_filter(self) -> None:
        self.assertEqual(self.syncthru.drum_status(True), {})

    def test_drum_status_no_filter(self) -> None:
        self.assertEqual(
            self.syncthru.drum_status(False),
            {
                "black": {"newError": "", "opt": 0, "remaining": 0},
                "cyan": {"newError": "", "opt": 0, "remaining": 100},
                "magenta": {"newError": "", "opt": 0, "remaining": 100},
                "yellow": {"newError": "", "opt": 0, "remaining": 100},
            },
        )

    def test_location(self) -> None:
        self.assertEqual(self.syncthru.location(), RAW_STATE1["identity"]["location"])

    def test_serial_number(self) -> None:
        self.assertEqual(
            self.syncthru.serial_number(), RAW_STATE1["identity"]["serial_num"]
        )

    def test_hostname(self) -> None:
        self.assertEqual(self.syncthru.hostname(), RAW_STATE1["identity"]["host_name"])

    def test_cap(self) -> None:
        self.assertEqual(self.syncthru.capability(), RAW_STATE1["capability"])

    def tearDown(self) -> None:
        self.server_control.stop_server()


class SyncthruAPITest2(unittest.TestCase):
    server = None
    server_control = None  # type: Server
    port = 0
    url = "http://localhost:80"
    syncthru = None  # type: SyncThru

    def setUp(self) -> None:
        # Create an arbitrary subclass of TCP Server as the server to be started
        # Here, it is an Simple HTTP file serving server
        handler = SyncThruRequestHandler

        max_retries = 10
        r = 0
        while not self.server:
            try:
                # Connect to any open port
                self.server = SyncThruServer((ADDRESS, 0), handler)
            except OSError:
                if r < max_retries:
                    r += 1
                else:
                    raise
                time.sleep(1)

        self.server_control = Server(self.server)
        self.port = self.server_control.get_port()
        self.url = "{}:{}".format(ADDRESS, self.port)
        # Start test server before running any tests
        self.server_control.start_server()
        self.server.server_dir = Path(__file__).parent / "test_structure" / "state2"

        async def fetch():
            async with aiohttp.ClientSession() as session:
                self.syncthru = SyncThru(
                    self.url, session, connection_mode=ConnectionMode.API
                )
                await self.syncthru.update()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())

    def test_newline_unescaped_status(self) -> None:
        self.assertEqual(
            self.syncthru.device_status_details(),
            "Warming Up\r\n Please Wait...",
        )

    def tearDown(self) -> None:
        self.server_control.stop_server()


class SyncthruHTMLTest(unittest.TestCase):
    server = None
    server_control = None  # type: Server
    port = 0
    url = "http://localhost:80"
    syncthru = None  # type: SyncThru

    def setUp(self) -> None:
        # Create an arbitrary subclass of TCP Server as the server to be started
        # Here, it is an Simple HTTP file serving server
        handler = SyncThruRequestHandler

        max_retries = 10
        r = 0
        while not self.server:
            try:
                # Connect to any open port
                self.server = SyncThruServer((ADDRESS, 0), handler)
            except OSError:
                if r < max_retries:
                    r += 1
                else:
                    raise
                time.sleep(1)

        self.server_control = Server(self.server)
        self.port = self.server_control.get_port()
        self.url = "{}:{}".format(ADDRESS, self.port)
        # Start test server before running any tests
        self.server_control.start_server()

        async def fetch():
            async with aiohttp.ClientSession() as session:
                self.syncthru = SyncThru(
                    self.url, session, connection_mode=ConnectionMode.HTML
                )
                await self.syncthru.update()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())

    def test_location(self) -> None:
        self.assertEqual(self.syncthru.location(), RAW_HTML["identity"]["location"])

    def test_model_name(self) -> None:
        self.assertEqual(self.syncthru.model(), RAW_HTML["identity"]["model_name"])

    def test_hostname(self) -> None:
        self.assertEqual(self.syncthru.hostname(), RAW_HTML["identity"]["host_name"])

    def test_mac_address(self) -> None:
        self.assertEqual(self.syncthru.mac_address(), RAW_HTML["identity"]["mac_addr"])

    def test_toner_filter(self) -> None:
        self.assertDictEqual(
            self.syncthru.toner_status(True),
            {"black": {"opt": 1, "remaining": 66, "newError": ""}},
        )

    def test_input_tray_filter(self) -> None:
        self.assertDictEqual(
            self.syncthru.input_tray_status(True),
            {
                "tray_1": {
                    "opt": 1,
                    "newError": "",
                }
            },
        )


class NonSyncthruWebTest(unittest.TestCase):
    server = None
    server_control = None  # type: Server
    port = 0
    url = "http://localhost:80"
    syncthru = None  # type: SyncThru

    def test_no_syncthru(self) -> None:
        """Test that an error is thrown when no syncthru is supported"""
        # Create an arbitrary subclass of TCP Server as the server to be started
        # Here, it is an Simple HTTP file serving server
        handler = SyncThruRequestHandler

        max_retries = 10
        r = 0
        while not self.server:
            try:
                # Connect to any open port
                self.server = SyncThruServer((ADDRESS, 0), handler)
            except OSError:
                if r < max_retries:
                    r += 1
                else:
                    raise
                time.sleep(1)

        self.server_control = Server(self.server)
        self.port = self.server_control.get_port()
        self.url = "{}:{}".format(ADDRESS, self.port)
        # Start test server before running any tests
        self.server_control.start_server()

        # Block server to make sure we get "no support"
        self.server.set_blocked()

        try:

            async def fetch() -> None:
                async with aiohttp.ClientSession() as session:
                    self.syncthru = SyncThru(
                        self.url, session, connection_mode=ConnectionMode.API
                    )
                    await self.syncthru.update()

            loop = asyncio.get_event_loop()
            loop.run_until_complete(fetch())
            self.fail(
                "No error thrown when noticing that the host does not support Syncthru"
            )
        except SyncThruAPINotSupported:
            pass

    def test_offline_unknown(self) -> None:
        """Test that nothing is returned when syncthru is offline"""

        async def fetch() -> None:
            async with aiohttp.ClientSession() as session:
                self.syncthru = SyncThru(
                    self.url, session, connection_mode=ConnectionMode.API
                )
                await self.syncthru.update()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())
        self.assertFalse(self.syncthru.is_online())
        self.assertTrue(self.syncthru.is_unknown_state())


if __name__ == "__main__":
    unittest.main()
