# PySyncThru - a very basic python SyncThru bridge

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
from pysyncthru import SyncThru
syncthru = SyncThru('192.168.1.14')
# Get the devices status
syncthru.deviceStatus()
# Update the data
syncthru.update()
```
