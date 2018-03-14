'''
Connects to a Samsung printer with SyncThru service


@author: Niels
'''

import requests
import demjson

def test_syncthru(ip):

    '''
    Tests whether an Samsung printer with Synthru answers under
    given ip
    Attributes:
        ip      IP of the printer
    '''

    ip = verify_ip(ip)
    # load json data from delivered ip
    syncthru_json_path = "/sws/app/information/home/home.json"

    # if the below works we can be pretty sure there is a fronius answering
    try:
        # get data by JSON API
        r = requests.get(ip + syncthru_json_path, timeout=5)

        json_dict = demjson.decode(r.text)
        status = json_dict['status']['hrDeviceStatus']

        if status is not None:
            return True
        return False
    except requests.exceptions.RequestException:
        return False
    except KeyError:
        return False

def verify_ip(ip):

    if "http://" not in ip and "https://" not in ip:
        ip = "http://" + ip
    if ip[-1] == '/':
        del ip[-1]
    return ip

class SyncThru(object):

    '''
    Interface to communicate with the Samsung Printer with SyncThru
    over http / JSON
    Attributes:
        ip         The ip/domain of the printer
        data        Received data from the printer
    '''

    COLOR_NAMES = ['black', 'cyan', 'magenta', 'yellow']
    TONER = 'toner'
    DRUM = 'drum'
    TRAY = 'tray'
    OFFLINE = 'Offline'

    def __init__(self, ip):
        '''
        Constructor
        '''
        self.ip = verify_ip(ip)
        self.data = None
        self.update()

    def update(self):
        '''
        Crunch the latest data about the main system
        Returns a dict mapping each key name to value and unit
        And sets the internal attribute "data" to the dict

        Return the data or an empty dictionary on failure
        '''
        # load json data from delivered ip
        # This data sadly is no valid json => use demjson for parsing
        syncthru_json_path = "/sws/app/information/home/home.json"
        # get data by JSON API
        try:
            r = requests.get(self.ip + syncthru_json_path, timeout=5)

            json_dict = demjson.decode(r.text)
        except requests.exceptions.RequestException:
            json_dict = {'status': {'status1': SyncThru.OFFLINE}}
        except Exception:
            json_dict = {}
        # make data accessible from outside
        self.data = json_dict
        return json_dict

    @staticmethod
    def deviceStatusSimplify(status):
        '''
        Convert the status1 field of the device status to a readable String
        '''
        return {
            '  Sleeping...   ': 'Sleeping',
            ' Ready to Copy  ': 'Ready',
            '   Warming Up   ': 'Warming up',
            SyncThru.OFFLINE: 'Offline',
        }.get(status, 'Unknown')

    def isOnline(self):
        return self.deviceStatus() != SyncThru.OFFLINE

    def model(self):
        try:
            return self.data.get('identity').get('model_name')
        except Exception:
            return self.deviceStatusSimplify('')

    def deviceStatus(self):
        '''
        Return the status of the device as string
        '''
        try:
            return self.deviceStatusSimplify(self.data.get('status').get(
                'status1'))
        except Exception:
            return self.deviceStatusSimplify('')

    def systemStatus(self):
        '''
        Return the status of the device system
        '''
        try:
            return self.data.get('capability', {})
        except Exception:
            return {}

    def tonerStatus(self, filter_supported=True):
        '''
        Return status of all toners
        filter_supported    Only return supported toners
        Example:
        'toner_black': {'opt': 1, 'remaining': 81, 'cnt': 98, 'newError': ''}
        '''

        toner_status = {}
        for color in self.COLOR_NAMES:
            try:
                tonerStat = self.data.get(SyncThru.TONER + '_' + color, {})
                if filter_supported and tonerStat.get('opt', 0) == 0:
                    continue
                else:
                    toner_status[color] = tonerStat

            except Exception:
                toner_status[color] = {}
        return toner_status

    def inputTrayStatus(self, filter_supported=True):
        '''
        Return the status of all input trays
        filter_supported    Only return supported trays
        '''
        tray_status = {}
        for i in range(1, 5):
            try:
                trayStat = self.data.get("{}{}".format(SyncThru.TRAY, i), {})
                if filter_supported and trayStat.get('opt', 0) == 0:
                    continue
                else:
                    tray_status[i] = trayStat

            except Exception:
                tray_status[i] = {}
        return tray_status

    def outputTrayStatus(self):
        '''
        Return the status of all output trays
        '''
        tray_status = {}
        try:
            trayStat = self.data.get("outputTray", [])
            # Meaning extracted from /sws/app/information/home/home.js
            # { fields: [ {name: 'name'},
            #  {name: 'capacity'}, {name: 'status'} ] })
            for i in range(0, len(trayStat)):
                tray_status[i] = {}
                tray_status[i]['name'] = trayStat[i][0]
                tray_status[i]['capacity'] = trayStat[i][1]
                tray_status[i]['status'] = trayStat[i][2]

        except Exception:
            tray_status = {}
        return tray_status

    def drumStatus(self, filter_supported=True):
        '''
        Return the status of all drums
        filter_supported    Only return supported drums
        '''
        drum_status = {}
        for color in self.COLOR_NAMES:
            try:
                drumStat = self.data.get(SyncThru.DRUM + '_' + color, {})
                if filter_supported and drumStat.get('opt', 0) == 0:
                    continue
                else:
                    drum_status[color] = drumStat

            except Exception:
                drum_status[color] = {}
        return drum_status
