from bluepy.btle import DefaultDelegate
from datetime import datetime
from binascii import hexlify
from . import gMath
import http.client
import json

#####################################################################
# SCAN_DELEGATE
#####################################################################
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)


    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print(f"Discovered dev: {dev.addr}")
        elif isNewData: 
            print(f"New data from: {dev.addr}")


#####################################################################
# PERIPH_DELEGATE
#####################################################################
class PeriphDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.dataMan = None


    def setDataHandler(self, dHandle):
        # It makes notifications visible to DataHandler Class
        self.dataMan = dHandle
        return self


    def handleNotification(self, cHandle, data):
        self.dataMan.saveData(data)
        print(f"Notify from hnd {hex(cHandle)}: {hexlify(data)}")


#####################################################################
# DATA_HANDLER
#####################################################################
class DataHandler():
    '''
    This class groups data from BLE notifications, applies some math functions 
    and transforms it to JSON or CSV files.
    DataHandler retains data even if the Peripheral is disconnected.
    It also keeps information about specific endpoint, station and equipment.
    '''

    def __init__(self):
        self.info               = dict.fromkeys(['endpointID','equipID','macStationID','timeStamp'], None)
        self.features           = dict.fromkeys(['x','y','z'], None)
        self.rawData            = list()
        self.scaleFactor        = 16384
        self.newFeaturesToSend  = False


    def checkNewFeatures(self):
        if (self.newFeaturesToSend == True):
            self.newFeaturesToSend = False

            # info dict + features dict : > Python3.5
            data = {**self.info, **self.features}
            return data
        else:
            return False
    

    def simplifyMac(self, mac):
        return mac.replace(':','').upper()


    def setInfo(self, endpointID, equipID, macStationID):
        self.info['endpointID']     = self.simplifyMac(endpointID)
        self.info['macStationID']	= self.simplifyMac(macStationID)
        self.info['equipID']    	= equipID
        self.info['timeStamp']  	= datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    def setScaleFactor(self, sFactor):
        self.scaleFactor = sFactor


    def saveData(self, data):
        rawPacket = hexlify(data).decode('utf-8')
        self.rawData.append(rawPacket)


    def processRawData(self):
        accels = gMath.extractData(self.rawData, self.scaleFactor)
        round2 = lambda x:round(x,2)
        round6 = lambda x:round(x,6)

        for (axis, values) in accels.items():
            axisFeature             = dict()
            values                  = gMath.convertToNumpy(values)
            values                  = gMath.removeMean(values)
            (FFT, f)                = gMath.FFT(values)
            freqs, amps             = gMath.topN_HighestAmps(FFT, f, 3)
            
            axisFeature["rms"]     = round6(gMath.rms(values))
            axisFeature["cf"]      = round6(gMath.crestFactor(values, axisFeature["rms"]))
            axisFeature["freq"]    = round2(gMath.mean(freqs))
            axisFeature["amp"]     = round2(gMath.mean(amps))
            self.features[axis]    = axisFeature

        # Clear list to new acquisition and set newFeatures
        self.rawData.clear()
        self.newFeaturesToSend = True


#####################################################################
# CLOUD_CONNECTION
#####################################################################
class CloudConnection():
    '''
    This class connects to cloud and sends data to the webservice.
    '''
    def __init__(self):
        self.host = None
        self.port = None
        self.connection = None


    def connect(self, cHost, cPort):
        self.host = cHost
        self.port = cPort
        self.connection = http.client.HTTPConnection(self.host, self.port, timeout = 5)


    def disconnect(self):
        self.connection.close()
        self.connection = None


    def sendToCLoud(self, cURL, dataDict):
        headers = {'Content-type': 'application/json'}
        dataJson = json.dumps(dataDict, indent = 4)
        self.connection.request("POST", cURL, dataJson, headers)

        response = self.connection.getresponse()
        print(f"Sendind data to cloud: {cURL}")
        print(f"Status: {response.status} - reason: {response.reason}")
