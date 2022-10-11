## Begin ControlScript Import --------------------------------------------------
from extronlib import event, Version
from extronlib.device import eBUSDevice, ProcessorDevice, UIDevice
from extronlib.interface import (ContactInterface, DigitalIOInterface,
    EthernetClientInterface, EthernetServerInterfaceEx, FlexIOInterface,
    IRInterface, RelayInterface, SerialInterface, SWPowerInterface,
    VolumeInterface)
from extronlib.ui import Button, Knob, Label, Level
from extronlib.system import Clock, MESet, Wait, File
import json


# for tracking room power timer status
class PowerProgress():
    def __init__(self, room, state, time):
        self.room = room
        self.state = state
        self.timer = Wait(time, self.timerFinished)
        
    def startTimer(self):
        self.timer.Restart()
        
    def timerFinished(self):
        self.__TimerFinished(self)
        
    @property
    def TimerFinished(self):
        return self.__TimerFinished
   
    @TimerFinished.setter
    def TimerFinished(self, handler):
        if callable(handler):
            self.__TimerFinished = handler
        else:
            raise ValueError('handler must be a function')


class CombinedRoom():
    def __init__(self, config, log):
        self.Rooms = {}
        self.Combine = 0
        for r in config:
            self.Rooms[r['RoomName']] = Room(r['RoomName'], 
                  index = config.index(r), onTime = r['OnTime'], 
                  offTime = r['OffTime'], audioTime = r['AudioTime'], Log = log)
    
    def SetCombine(self, state):
        self.Combine = state
        
    def Set(self, cmd, value, qualifier = {}):
        if not self.Combine:
            qualifier['Index'] = self.Rooms[qualifier['Room']].index
            self.Rooms[qualifier['Room']].Set(cmd, value, qualifier)
        else:
            for r in self.Rooms:
                qualifier['Index'] = self.Rooms[r].index
                self.Rooms[r].Set(cmd, value, qualifier)
      

class Room():
    def __init__(self, name, index = 0, onTime = 10, offTime = 10, 
                                                     audioTime = 1, Log = None):
        self.Log = Log
        self._callback = None
        self.index = index
        self.name = name
        self.power = 0
        self.audioPower = 0
        self.videoPower = 0
        self.sourcePower = 0
        self.activity = 0
        self.volume = [0,0,0,0,0,0,0,0,0,0]
        self.mute = [0,0,0,0,0,0,0,0,0,0]
        self.vwPreset = [1,1]
        self.turnOnTime = onTime
        self.turnOffTime = offTime
        self.audioTime = audioTime
        self.restart = 0
        self.combine = 0
        self.combineRooms = []
        self.onTimer = None
        self.offTimer = None
        
        self.ALL_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 
                                                           'Saturday', 'Sunday']
        self.WEEK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday','Friday']
        self.WEEKEND_DAYS = ['Sunday', 'Saturday']
        
        self.TimerSettings = {
            'On': {
                'Enable': 0, 
                'Time': ['7:00:00'], 
                'Days': self.WEEK_DAYS,
            },
            'Off': {
                'Enable': 1, 
                'Time': ['18:00:00'], 
                'Days': self.ALL_DAYS,
            },
        }
        
        ## try to load scheduling info from files        
        if File.Exists('/{}TimerSettings.json'.format(self.name)):
            self.Log.Entry('IO', '{} Timer file exists, loading...'.format(
                                                                    self.name))
            f = File('/{}TimerSettings.json'.format(self.name), 'r')
            self.TimerSettings = json.load(f)
            self.Log.Entry('IO', '{} Timer file loaded.'.format(self.name))
        else:
            self.Log.Entry('IO', '{} Timer default loaded.'.format(
                                                                    self.name))
    
        self.onClock = Clock(self.TimerSettings['On']['Time'], 
                         self.TimerSettings['On']['Days'], self.StartupFunction)
        self.offClock = Clock(self.TimerSettings['Off']['Time'], 
                       self.TimerSettings['Off']['Days'], self.ShutdownFunction)
                       
        self.SetStartupConfig(self.TimerSettings['On'])
        self.SetShutdownConfig(self.TimerSettings['Off'])
        
    ############################################################################
    ## room methods
    
    # helpers
    #def SetCombine(self, value, qualifier = None):
        #self.combine = value
        #if value:
            #self.combineRooms = qualifier['Rooms']
            #
        #else:
            #self.combineRooms = []
    
    def SetCallback(self, value, qualifier = None):
        self._callback = value
        self.WriteStatus('StartupConfig',self.TimerSettings,{'Room': self.name})
        
    def _print(self, msg):
        if self.Log:
            self.Log.Entry('IO', msg)
        else:
            print(msg)
            
            
    # shartup/shutdown timers
    def SetStartupConfig(self, settings):
        self.TimerSettings['On'] = settings
        self.onClock.SetDays(settings['Days'])
        self.onClock.SetTimes(settings['Time'])
        if settings['Enable']:
            self.onClock.Enable()
        else:
            self.onClock.Disable()
        #try:
        f = File('/{}TimerSettings.json'.format(self.name), 'w+')
        msg = json.dumps(self.TimerSettings)
        self.Log.Entry('IO', msg)
        f.write(msg)
        f.close()
        #except:
            #self.Log.Entry('IO', 'Filed to write Timer file')
        self.WriteStatus('StartupConfig',self.TimerSettings,{'Room': self.name})
        
    def SetShutdownConfig(self, settings):
        self.TimerSettings['Off'] = settings
        self.offClock.SetDays(settings['Days'])
        self.offClock.SetTimes(settings['Time'])
        if settings['Enable']:
            self.offClock.Enable()
        else:
            self.offClock.Disable()
        #try:
        f = File('/{}TimerSettings.json'.format(self.name), 'w+')
        msg = json.dumps(self.TimerSettings)
        self.Log.Entry('IO', msg)
        f.write(msg)
        f.close()
        #except:
            #self.Log.Entry('IO', 'Filed to write Timer file')
        self.WriteStatus('ShutdownConfig',self.TimerSettings,{'Room':self.name})
      
    def StartupFunction(self, clock, dt):
        self.WriteStatus('Timer', 'Startup', {'Room': self.name}) 
        
    def ShutdownFunction(self, clock, dt):
        self.WriteStatus('Timer', 'Shutdown', {'Room': self.name}) 
    
    
    # room methods
    def ActivitySelect(self):
        # if room is off, turn on
        if self.power == 0:
            self.Set('Power', 1)   
        # if room is powering off update gui
        elif self.power == 2:   
            # set restart flag to true
            self.Set('Restart', 1)       
        # if room is already on, switch sources
        else:
            self.Set('Source', self.activity)
        
    def PowerOff(self):
        # initiate room off
        self.Set('VideoPower', 0)
        self.Set('AudioPower', 0)
        self.Set('SourcePower', 0)
        
        # start the room off timer, inits restart if needed when timer done
        self.Set('OffTimer', 0)
        
    def PowerOn(self):
        # initiate room on
        self.Set('VideoPower', 1)
        self.Set('SourcePower', 1)
        self.Set('Source', self.activity)
        # start the room on timer, audio powers on and source switches when done
        self.Set('OnTimer', self.audioTime)
        
    def SetMute(self, value, qualifier):
        self.mute[qualifier['Channel']-1] = value
        self.WriteStatus('Mute', self.mute[qualifier['Channel']-1], 
                           {'Room': self.name, 'Channel': qualifier['Channel']}) 
    
    def SetVolume(self, value, qualifier):
        self.volume[qualifier['Channel']-1] = value
        self.WriteStatus('Volume', self.volume[qualifier['Channel']-1], 
                           {'Room': self.name, 'Channel': qualifier['Channel']})
                
    def SetPower(self, value, qualifier = None):
        self.power = value
        if value == 2:
            self.PowerOff()
        elif value == 1:
            self.PowerOn()
        self.WriteStatus('Power', value, {'Room': self.name})
        
    def SetLayout(self, value, qualifier = None):
        self.layout = value
        self.WriteStatus('Layout', self.layout, {'Room': self.name}) 

    def SetVideoPower(self, value, qualifier = None):
        self.videoPower = value
        self.WriteStatus('VideoPower', value, {'Room': self.name})
        
    def SetAudioPower(self, value, qualifier = None):
        self.audioPower = value
        self.WriteStatus('AudioPower', self.audioPower, {'Room': self.name})
        
    def SetSourcePower(self, value, qualifier = None):
        self.sourcePower = value
        self.WriteStatus('SourcePower', self.sourcePower, {'Room': self.name})
        
    def SetSource(self, value, qualifier):
        self.source = value
        self.WriteStatus('Source', value, {'Room': self.name})
        
    def SetActivity(self, value, qualifier = None):
        self.activity = int(value)
        self.ActivitySelect()
        self.WriteStatus('Activity', self.activity, {'Room': self.name})
                
    def SetRestart(self, value, qualifier = None):
        self.restart = value
        if self.restart == 0:
            self.Set('Power', 1)
        self.WriteStatus('Restart', self.restart, {'Room': self.name})
        
    def SetOffTimer(self, value, qualifier = None):
        self.offTimer = PowerProgress(self.index, 0, self.turnOffTime - value)
        
        @event(self.offTimer, 'TimerFinished')
        def timerFinishedEvent(timer):
            # set the room power state
            self.Set('Power', timer.state)
            # if restart is true
            if self.restart:
                # reset the restart flag
                self.Set('Restart', 0)
        
    def SetOnTimer(self, value, qualifier = None):
        self.onTimer = PowerProgress(self.index, 1, self.turnOnTime - value)
        
        @event(self.onTimer, 'TimerFinished')
        def timerFinishedEvent(timer):
            # turn on audio power and switch sources
            self.Set('AudioPower', 1)
            #self.Set('Source', self.activity)
    
    def Set(self, command, value, qualifier=None):
        method = 'Set%s' % command
        if hasattr(self, method) and callable(getattr(self, method)):
            getattr(self, method)(value, qualifier)
        else:
            self._print('{} does not support Set.'.format(command))
            
    def WriteStatus(self, command, value, qualifier=None):
        if self._callback:
            self._callback(command, value, qualifier)
        else:
            self._print('Room Status: {} {} {}'.format(command, value, qualifier))        
   