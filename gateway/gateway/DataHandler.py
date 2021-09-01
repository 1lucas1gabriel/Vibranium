import numpy as np
from datetime import datetime
import json


##################################################################
# MATH PROCESSING
##################################################################
class DataMath():
    def __init__(self):
        pass


    def twos_complement(self, hexstr, bits):
        value = int(hexstr, 16)
        if value & (1 << (bits-1)):
            value -= 1 << bits
        return value


    def removeMean(self, accel_values):
        return (accel_values - np.mean(accel_values))


    def rms(self, accel_values):
        return np.sqrt(np.mean(accel_values**2))


    def crestFactor(aself, accel_values, rms_value):
        return np.max(np.abs(accel_values))/rms_value


    def calculateFeatures(self, axis_values):
        features        = dict()
        axis_values     = self.removeMean(axis_values)
        features["rms"] = round(self.rms(axis_values), 6)
        features["cf"]  = round(self.crestFactor(axis_values, features["rms"]), 6)
        return features



#####################################################################
# DATA_HANDLER
#####################################################################
class DataHandler(DataMath):
    '''
    This class groups data from BLE notifications, applies some math functions 
    and transforms it to JSON or CSV files.
    DataHandler retains data even if the Peripheral is disconnected.
    It also keeps information about specific endpoint, station and equipment.
    '''

    def __init__(self, saveFile=False, dFormat='CSV',  path='/', sFactor=0):
        '''
        @saveFile: save raw samples to File
        @dFormat: Choose between JSON or CSV files to save
        '''
        self.info           = dict.fromkeys(['endpointID','equipID','macStationID','timeStamp'], None)
        self.features       = dict.fromkeys(['x','y','z'], None)
        self.scaleFactor    = self.setScaleFactor(sFactor)
        self.rawData        = list()
        self.newAcquisition = False
        self.acq_counter    = 0
        self.saveFile       = saveFile
        self.dFormat        = dFormat
        self.path           = path


    def checkNewAcquisition(self):
        if (self.newAcquisition == True):
            self.newAcquisition = False

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
        '''
        SFator: Accelerometer sensitivity\n
        Select scale factor from options or input manually\n 
        sFactor options: [0: 16384 (2g), 1: 8192 (4g), 2: 4096 (8g), 3: 2048 (16g)]
        '''
        scale = [16384, 8192, 4096, 2048]
        return sFactor if sFactor > 3 else scale[sFactor]


    def savePacket(self, rawPacket):
        self.rawData.append(rawPacket)

    
    def saveJSON(self, accels):
        '''
        Save acceleration acquisition to JSON file, ordering each file
        '''
        self.acq_counter+=1
        for axis in accels: accels[axis] = accels[axis].tolist() #convert to list to serialize JSON
        with open(f'{self.path}/vibration{self.acq_counter}.json', 'w') as f:
            json.dump(accels, f)
        

    def saveCSV(self, accels):
        '''
        Save acceleration acquisition to CSV file, ordering each file
        '''
        self.acq_counter+=1
        accel_values = np.stack((accels['x'], accels['y'], accels['z'])).T
        np.savetxt(f'{self.path}/vibration{self.acq_counter}.csv', accel_values, fmt='%3.5f', delimiter=',')

    
    def extractData(self, rawData):
        '''
        It extracts raw hexadecimal data and converts to G acceleration force.
        Default (sensitivity) scale factor: 16384 (2g)
        '''
        accels = dict()

        # delete '0d0a' of each packet
        rawData = [line[:-4] for line in rawData]

        # divide each line into a list with samples
        rawData = [[line[0:12], line[12:24], line[24:36]] for line in rawData]
        flatRawData = [item for sublist in rawData for item in sublist]

        # delete empty spaces from list
        rawData = list(filter(None, flatRawData))
        
        # splits and convert each sample line to the respective acceleration axis
        accels['x'] = [self.twos_complement(value[0:4], 16) / self.scaleFactor for value in rawData]
        accels['y'] = [self.twos_complement(value[4:8], 16) / self.scaleFactor for value in rawData]
        accels['z'] = [self.twos_complement(value[8:12],16) / self.scaleFactor for value in rawData]
        return accels


    def processRawData(self):
        accels = self.extractData(self.rawData)
        for (axis, axis_values) in accels.items():
            accels[axis] = np.array(axis_values) # convert to numpy array
            self.features[axis] = self.calculateFeatures(accels[axis])

        # saving raw samples        
        if (self.saveFile and self.dFormat == 'JSON'):
            self.saveJSON(accels)
        elif (self.saveFile and self.dFormat == 'CSV'):
            self.saveCSV(accels)

        # Clear list to new acquisition
        self.rawData.clear()
        self.newAcquisition = True