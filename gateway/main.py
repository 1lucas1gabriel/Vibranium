'''
@1lucas1gabriel - JAN/2021

Programa escaneia e conecta-se a endpoints BLE com o endereco MAC 
cadastrado. Os dados brutos sao recebidos via notificacao e apos um 
tratamento eh enviado a nuvem, por meio de uma requisicao HTTP POST.

- UUID do servico de UART: FFE1
- Handle do servico de UART: 0x0025
'''

from bluepy.btle import Scanner, Peripheral, UUID
from resources.gateway import ScanDelegate, DataHandler, PeriphDelegate, CloudConnection


#####################################################################
# SETUP GATEWAY
#####################################################################
endpointMac     = "c8:df:84:34:ad:c0"
gatewayMac      = "24:f5:aa:66:10:6e"
equipmentID     = "MT01" 
scanner = Scanner().withDelegate(ScanDelegate())
dataMan = DataHandler()
cloud = CloudConnection()

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

                # Turn notifications on
                cDev.writeCharacteristic(uartCharHnd + 1, b"\x01\x00")
                
                # Tells the sensor to send accelerometer data
                cDev.writeCharacteristic(uartCharHnd, b"\x31")

                notificationsCounter = 0
                while True:
                    try:
                        if cDev.waitForNotifications(2.0):
                            notificationsCounter += 1

                            if (notificationsCounter == 342):
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

    response = dataMan.checkNewFeatures()
    if response is False:
        print("Nothing to send! [Scanning again...]")
    else:
        try:
            print(response)
            cloud.connect('ec2.aws.domain.com', 80)
            endID = dataMan.info['endpointID']
            cloud.sendToCLoud(f'/v1/endpoints/{endID}/acquisition', response)
            cloud.disconnect()
        
        except Exception as ex:
            print(str(ex))
#####################################################################
