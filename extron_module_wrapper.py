from extronlib import event
from extronlib.system import File
from ConnectionHandler import GetConnectionHandler
import json

class ExtModWrapper:

    def __init__(self, modName, comType, comInfo, model = '', status = [], 
                                             log = None, fileName = 'settings', 
                                                          pollFrequency = 15.0):
        
        self.Log = log
        self.comType = comType
        self.fileName = fileName
        self.comInfo = comInfo
        self.Model = model
        self.ID = ''
        
        if self.comType == "serial":
            self.Conn = modName.SerialClass
        elif self.comType == "ethernet":
            self.Conn = modName.EthernetClass
        elif self.comType == "sereth":
            self.Conn = modName.SerialOverEthernetClass
        elif self.comType == "ssh":
            self.Conn = modName.SSHClass
        
        if File.Exists('/{}.json'.format(self.fileName)):
            self._print('settings file exists, loading...')
            f = File('/{}.json'.format(self.fileName), 'r')
            settings = json.loads(f.read())
            printMsg = ''
            if 'ip' in settings:
                self.comInfo[0] = settings['ip']
            if 'username' in settings:
                self.user = settings['username']
            if 'password' in settings:
                self.password = settings['password']
            if 'id' in settings:
                self.ID = settings['id']
            
            self._print('{}.json settings file loaded'.format(self.fileName))
        else:
            self._print('{}.json does not exist, using defaults'.format(
                                                                 self.fileName))
        
        self.Dev = GetConnectionHandler(self.Conn(self.comInfo[0], 
                                             self.comInfo[1], Model=self.Model), 
                                 self.comInfo[2], pollFrequency = pollFrequency)
                                        
        self._callback = None
        self._devIndex = 0
        for s in status:
            self.Dev.SubscribeStatus(s, None, self._status)
            
        @event(self.Dev, ['Connected', 'Disconnected'])
        def ConnectionEvent(interface, state):
            self._status('ConnectionEvent', state, None)
            if self.comType == "serial":
                self._print('{} {} {}'.format(interface.Host.DeviceAlias, 
                                                         interface.Port, state))
            else:
                self._print('{} {}'.format(interface.Hostname, state))
            
        #if self.comType != "serial":
            #@event(self.Dev, 'ConnectFailed')
            #def ConnectFailed(interface, reason):
                #self._print('{} Connect failure: {}'.format(interface.Hostname, 
                                                                        #reason))

    def _status(self, command, value, qualifier):
        if self._callback:
            if self._devIndex > 0:
                self._callback(self._devIndex, command, value, qualifier)   
            else:
                self._callback(command, value, qualifier)
                
    def _print(self, msg):
        if self.Log != None:
            self.Log.Entry('Device', msg)
        else:
            print(msg)

    def SetCallback(self, callback, index = 0):
        if index > 0:
            self._devIndex = index
        self._callback = callback
