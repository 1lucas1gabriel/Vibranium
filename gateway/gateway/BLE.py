from bluepy.btle import DefaultDelegate
from binascii import hexlify


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
        self.dataHandler = None


    def setDataHandler(self, dHandler):
        # It makes notifications visible to DataHandler Class
        self.dataHandler = dHandler
        return self


    def handleNotification(self, cHandle, data):
        rawPacket = hexlify(data).decode('utf-8')
        self.dataHandler.savePacket(rawPacket)
        print(f"Notify from hnd {hex(cHandle)}: {rawPacket}")