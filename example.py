"""
Copyright (c) 2017-2018 Fabian Affolter <fabian@affolter-engineering.ch>

Licensed under MIT. All rights reserved.
"""
import asyncio

import aiohttp

from pysyncthru import SyncThru

IP_PRINTER = "192.168.0.25"


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        printer = SyncThru(IP_PRINTER, session)
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


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
