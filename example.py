"""
Copyright (c) 2017-2018 Fabian Affolter <fabian@affolter-engineering.ch>

Licensed under MIT. All rights reserved.
"""
import asyncio
import pprint
import sys

import aiohttp

from pysyncthru import SyncThru


async def main(ip: str) -> None:
    async with aiohttp.ClientSession() as session:
        printer = SyncThru(ip, session)
        await printer.update()

        # Is printer online?
        print("Printer online?:", printer.is_online())
        # Show the printer status
        print("Printer status:", printer.device_status())
        if printer.is_online():
            # Show details about the printer
            print("Printer model:", printer.model())
            # Get the details of cartridges
            for color, details in printer.toner_status().items():
                print(f"Toner {color} details:", details)
            # Get the details about a tray
            print("Tray 1 Capacity:", printer.input_tray_status()["tray_1"]["capa"])
        # Print all available details from the printer
        print("All data:\n", pprint.pformat(printer.raw()))


if len(sys.argv) != 2:
    print(f"Usage: {__file__} IP-ADDRESS", file=sys.stderr)
    sys.exit(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(sys.argv[1]))
