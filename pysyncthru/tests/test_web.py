#!/usr/bin/env python
# -*- coding: utf-8 -*-

# general requirements
import unittest
from .test_structure.server_control import Server
from .test_structure.syncthru_mock_server import SyncThruServer, SyncThruRequestHandler

# For the server in this case
import time

# For the tests
import aiohttp
import asyncio
from pysyncthru import SyncThru
from .web_raw.web_state import RAW

ADDRESS = 'localhost'


class SyncthruWebTest(unittest.TestCase):

    server = None
    server_control = None
    port = 0
    url = 'http://localhost:80'
    syncthru = None

    def setUp(self):
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
                self.syncthru = SyncThru(self.url, session)
                await self.syncthru.update()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())

    def test_online(self):
        self.assertTrue(self.syncthru.is_online())

    def test_status_sleeping(self):
        self.assertEqual(self.syncthru.device_status(), 'Sleeping')

    def test_model(self):
        self.assertEqual(self.syncthru.model(), RAW['identity']['model_name'])

    def test_toner_filter(self):
        self.assertEqual(
            self.syncthru.toner_status(True),
            {'black': {
                'opt': 1,
                'remaining': 58,
                'cnt': 229,
                'newError': ''
            }})

    def test_toner_no_filter(self):
        empty = {'opt': 0, 'remaining': 0, 'cnt': 0, 'newError': ''}
        self.assertEqual(
            self.syncthru.toner_status(False), {
                'yellow': empty,
                'magenta': empty,
                'cyan': empty,
                'black': {
                    'opt': 1,
                    'remaining': 58,
                    'cnt': 229,
                    'newError': ''
                }
            })

    def test_input_tray_filter(self):
        self.assertEqual(
            self.syncthru.input_tray_status(True), {
                1: {
                    'capa': 150,
                    'newError': '',
                    'opt': 1,
                    'paper_size1': 4,
                    'paper_size2': 0,
                    'paper_type1': 2,
                    'paper_type2': 0
                }
            })

    def test_input_tray_no_filter(self):
        self.assertEqual(
            self.syncthru.input_tray_status(False), {
                1: {
                    'capa': 150,
                    'newError': '',
                    'opt': 1,
                    'paper_size1': 4,
                    'paper_size2': 0,
                    'paper_type1': 2,
                    'paper_type2': 0
                },
                2: {
                    'capa': 0,
                    'newError': '',
                    'opt': 0,
                    'paper_size1': 0,
                    'paper_size2': 0,
                    'paper_type1': 2,
                    'paper_type2': 0
                },
                3: {
                    'capa': 0,
                    'newError': '',
                    'opt': 0,
                    'paper_size1': 0,
                    'paper_size2': 0,
                    'paper_type1': 2,
                    'paper_type2': 0
                },
                4: {
                    'capa': 0,
                    'newError': '',
                    'opt': 0,
                    'paper_size1': 0,
                    'paper_size2': 0,
                    'paper_type1': 2,
                    'paper_type2': 0
                }
            })

    def test_output_tray(self):
        self.assertEqual(self.syncthru.output_tray_status(),
                         {0: {
                             'capacity': 100,
                             'name': 1,
                             'status': ''
                         }})

    def test_drum_status_filter(self):
        self.assertEqual(self.syncthru.drum_status(True), {})

    def test_drum_status_no_filter(self):
        self.assertEqual(
            self.syncthru.drum_status(False), {
                'black': {
                    'newError': '',
                    'opt': 0,
                    'remaining': 0
                },
                'cyan': {
                    'newError': '',
                    'opt': 0,
                    'remaining': 100
                },
                'magenta': {
                    'newError': '',
                    'opt': 0,
                    'remaining': 100
                },
                'yellow': {
                    'newError': '',
                    'opt': 0,
                    'remaining': 100
                }
            })

    def test_location(self):
        self.assertEqual(self.syncthru.location(), RAW['identity']['location'])

    def test_serial_number(self):
        self.assertEqual(self.syncthru.serial_number(),
                         RAW['identity']['serial_num'])

    def test_hostname(self):
        self.assertEqual(self.syncthru.hostname(),
                         RAW['identity']['host_name'])

    def test_cap(self):
        self.assertEqual(self.syncthru.capability(), RAW['capability'])

    def tearDown(self):
        self.server_control.stop_server()
        pass


class NonSyncthruWebTest(unittest.TestCase):

    server = None
    server_control = None
    port = 0
    url = 'http://localhost:80'
    syncthru = None

    def test_no_syncthru(self):
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
            async def fetch():
                async with aiohttp.ClientSession() as session:
                    self.syncthru = SyncThru(self.url, session)
                    await self.syncthru.update()

            loop = asyncio.get_event_loop()
            loop.run_until_complete(fetch())
            self.fail("No error thrown when noticing that the host does not support Syncthru")
        except ValueError:
            pass

    def test_offline_unknown(self):
        """Test that nothing is returned when syncthru is offline"""

        async def fetch():
            async with aiohttp.ClientSession() as session:
                self.syncthru = SyncThru(self.url, session)
                await self.syncthru.update()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())
        self.assertFalse(self.syncthru.is_online())
        self.assertTrue(self.syncthru.is_unknown_state())


if __name__ == "__main__":
    unittest.main()
