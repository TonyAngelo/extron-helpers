## Begin ControlScript Import --------------------------------------------------
from extronlib import event, Version
from extronlib.interface import EthernetServerInterfaceEx
from extronlib.system import GetSystemUpTime


class CLI(object):
    def __init__(self, processor, log, callback = None, logRx = False, cliPort = 2001):
        self.Processor = processor
        self._Callback = callback
        self.Log = log
        self.LogRx = logRx
        self.cliPort = cliPort
        self.Server = EthernetServerInterfaceEx(self.cliPort,'TCP',MaxClients=3)
        
        if self.Server.StartListen() != 'Listening':
            self.Log.Entry('IO', "CLI Server didn't start.")    
            raise ResourceWarning('Port unavailable')
    
        @event(self.Server, 'ReceiveData')
        def HandleReceiveData(client, data):
            helpList = [
                'getLibVersion: Gets the extron library version',
                'getUpTime: Gets the Processor uptime, in seconds',
                'getCurrentLoad: Gets the load of 12V DC power supply in watts',
                'getFirmware: Gets the current firmware of the processor',
                'getMACAddress: Gets the MAC address of the processor',
                'getDeviceModel: Gets the model number of the processor',
                'getDevicePart: Gets the part number of the processor',
                'getDeviceSerial: Gets the serial number of the processor',
                'getStorage: Gets the processor hard drive space used, in KB',
            ]
            
            if self.LogRx:
                self.Log.Entry('IO', 'CLI Rx: {}'.format(data.decode()))
            
            if b'getLibVersion' in data:
                self.cliResponse(client, '{}'.format(Version()))
                
            elif b'getUpTime' in data:
                self.cliResponse(client, '{}'.format(GetSystemUpTime()))
                
            elif b'getCurrentLoad' in data:
                self.cliResponse(client, '{}'.format(self.Processor.CurrentLoad))
                
            elif b'getFirmware' in data:
                self.cliResponse(client,'{}'.format(self.Processor.FirmwareVersion))
                
            elif b'getMACAddress' in data:
                self.cliResponse(client, '{}'.format(self.Processor.MACAddress))
                
            elif b'getDeviceModel' in data:
                self.cliResponse(client, '{}'.format(self.Processor.ModelName))
                
            elif b'getDevicePart' in data:
                self.cliResponse(client, '{}'.format(self.Processor.PartNumber))
                
            elif b'getDeviceSerial' in data:
                self.cliResponse(client, '{}'.format(self.Processor.SerialNumber))
                
            elif b'getStorage' in data:
                self.cliResponse(client, 
                                 'Used: {} Total: {}'.format(
                                    self.Processor.UserUsage[0], 
                                    self.Processor.UserUsage[1]))
                                    
            elif b'help' in data:
                client.Send(b'\n')
                for line in helpList:
                    helpStr = '{}'.format(line)
                    helpStr = helpStr.encode()
                    client.Send(helpStr + b'\n\r')
                client.Send(b'\n\r')
                
            elif b'endSession' in data:
                client.Disconnect()
                
            elif self._Callback:
                entry = data.decode().strip()
                res = self._Callback(entry)
                self.cliResponse(client, '"{}" sent to the callback function.\n\rThe callback function {}.'.format(entry, "acknowledged" if res else "did not acknowledge"))
                
            prompt = self.getPrompt()
            client.Send(b'\r' + prompt.encode())
            
        @event(self.Server, 'Connected')
        def HandleClientConnect(client, state):
            self.Log.Entry('IO','CLI Client {} connected.'.format(client.IPAddress))
            prompt = self.getPrompt()
            client.Send(b'*****CLI******\n\r' + prompt.encode())
        
        @event(self.Server, 'Disconnected')
        def HandleClientDisconnect(client, state):
            self.Log.Entry('IO','CLI Client {} disconnected.'.format(client.IPAddress))  
            
    def cliResponse(self, client, msg):
        client.Send(b'\n')
        client.Send(msg.encode() + b'\n\r')
        client.Send(b'\n\r')
        
    def getPrompt(self):
        return '{}>'.format(self.Processor.Hostname)
