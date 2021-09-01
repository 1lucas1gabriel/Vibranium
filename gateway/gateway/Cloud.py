import http.client
import json


#####################################################################
# CLOUD
#####################################################################
class Cloud():
    '''
    This class connects to cloud and sends data to the webservice.
    '''
    def __init__(self, cHost, cPort):
        self.host = cHost
        self.port = cPort
        self.connection = None


    def connect(self):
        self.connection = http.client.HTTPConnection(self.host, self.port, timeout = 5)


    def disconnect(self):
        self.connection.close()
        #self.connection = None


    def sendToCLoud(self, cURL, dataDict):
        self.connect()
        headers = {'Content-type': 'application/json'}
        dataJson = json.dumps(dataDict, indent = 4)
        self.connection.request("POST", cURL, dataJson, headers)

        response = self.connection.getresponse()
        self.disconnect()
        print(f"Sendind data to cloud: {cURL}")
        print(f"Status: {response.status} - reason: {response.reason}")

