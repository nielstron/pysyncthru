"""
Copyright (c) 2017-2018 Fabian Affolter <fabian@affolter-engineering.ch>

Licensed under MIT. All rights reserved.
"""
import asyncio
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
            # Get the details of a cartridge
            print("Toner Cyan details:", printer.toner_status()["cyan"])
            # Get the details about a tray
            print("Tray 1 Capacity:", printer.input_tray_status()["tray_1"]["capa"])
        # Print all available details from the printer
        print("All data:\n", printer.raw())

if len(sys.argv) != 2:
    print(f"Usage: {__file__} IP-ADDRESS", file=sys.stderr)
    sys.exit(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(sys.argv[1]))
