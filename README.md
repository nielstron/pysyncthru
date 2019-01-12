# PySyncThru - a very basic python SyncThru bridge
[![Build Status](https://travis-ci.com/nielstron/pysyncthru.svg?branch=master)](https://travis-ci.com/nielstron/pysyncthru)
[![Coverage Status](https://coveralls.io/repos/github/nielstron/pysyncthru/badge.svg?branch=master)](https://coveralls.io/github/nielstron/pysyncthru?branch=master)
[![Python Versions](https://img.shields.io/pypi/pyversions/pysyncthru.svg)](https://pypi.org/project/PySyncThru/)

A package that connects to a Samsung printer in the local network that
makes use of the SyncThru web service and provides data
that is provided via the JSON API of the device.
It is able to read the system, toner and tray status and provides method 
wrappers to access them.

The package supports the following data provided by the printers:

- Device / System status
- Drum / Toner status
- Model name
- Tray status

Sadly it seems like there is no official API, so fixes are welcome and likely 
needed!

## Usage

```python
import aiohttp
import asyncio
from pysyncthru import SyncThru

async def main():
    async with aiohttp.ClientSession() as session:
        printer = SyncThru(IP_PRINTER, loop, session)
        await printer.update()

        # Is printer online?
        print("Printer online?:", printer.is_online())
        # Show the printer status
        print("Printer status:", printer.device_status())
        if printer.is_online():
            # Show details about the printer
            print("Printer model:", printer.model())
            # Get the details of a cartridge
            print("Toner Cyan details:", printer.toner_status()['cyan'])
            # Get the details about a tray
            print("Tray 1 Capacity:", printer.input_tray_status()[1]['capa'])
        # Print all available details from the printer
        print("All data:\n", printer.raw())
        
loop = asyncio.get_event_loop()
loop.run_until_complete(method())
```
