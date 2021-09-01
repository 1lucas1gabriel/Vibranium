'''
@1lucas1gabriel - AGO/2021

Programa escaneia e conecta-se a endpoints BLE com o endereco MAC 
cadastrado. Os dados brutos sao recebidos via notificacao e apos um 
tratamento eh enviado a nuvem, por meio de uma requisicao HTTP POST.

- Bluetooth module: Bolutek HC09 - CC2541 Ti
- UUID   - UART service: FFE1
- Handle - UART service: 0x0025
'''

from bluepy.btle import Scanner, Peripheral, UUID
from gateway.BLE import ScanDelegate, PeriphDelegate
from gateway.DataHandler import DataHandler
from gateway.Cloud import Cloud


#####################################################################
# SETUP GATEWAY
#####################################################################
endpointMac = "c8:df:84:34:ad:c0" 
gatewayMac  = "24:f5:aa:66:10:6e"
equipmentID = "MT01" 
numPackets  = 342 # match with number of packets from acquisition device
scanner     = Scanner().withDelegate(ScanDelegate())
dataMan     = DataHandler(True, 'CSV', 'webService/data')
cloud       = Cloud('ec2-URL.compute-1.amazonaws.com', 80)



#####################################################################
# BLUETOOH LOW ENERGY SCANNER - LOOP
#####################################################################
while True:
    devices = scanner.scan(2.0)
    for dev in devices:
        print(f"Dev: {dev.addr} ({dev.addrType})")

        if (dev.addr == endpointMac):
            try:
                # setup current Device
                cDev = Peripheral(dev.addr)
                cDelegate = PeriphDelegate().setDataHandler(dataMan)
                cDev.setDelegate(cDelegate)
                uartCharHnd = int('0x0025', 0)

                #cDev.writeCharacteristic(uartCharHnd, b"\x30") # ONLY FOR UNBLOCK SENSOR WHEN BLOCKED

                # Turn notifications on
                cDev.writeCharacteristic(uartCharHnd + 1, b"\x01\x00")
                
                # Tells the sensor to send accelerometer data
                cDev.writeCharacteristic(uartCharHnd, b"\x31")

                notificationsCounter = 0
                while True:
                    try:
                        if cDev.waitForNotifications(2.0):
                            notificationsCounter += 1

                            if (notificationsCounter == numPackets):
                                # After send all data, the sensor needs to receive x30 to go to standby
                                cDev.writeCharacteristic(uartCharHnd, b"\x30")
                                cDev.disconnect()
                                dataMan.processRawData()
                                dataMan.setInfo(endpointMac, equipmentID, gatewayMac)
                                break

                    # handles a unexpected disconnection from Peripheral   
                    except Exception as ex:
                        print(str(ex))
                        break
            
            except Exception as ex:
                        print(str(ex))

    ###################################################################
    # CLOUD CONNECTION
    ###################################################################

    response = dataMan.checkNewAcquisition()
    if response is False:
        print("Nothing to send! [Scanning again...]")
    else:
        try:
            print(response)
            endID = dataMan.info['endpointID'] #improve
            cloud.sendToCLoud(f'/v1/endpoints/{endID}/acquisition', response)
        
        except Exception as ex:
            print(str(ex))
#####################################################################
