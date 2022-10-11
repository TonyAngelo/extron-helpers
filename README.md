# extron-helpers

## CLI

A command line interface for scripter programs.

Available commands:

- getLibVersion: Gets the extron library version
- getUpTime: Gets the Processor uptime, in seconds
- getCurrentLoad: Gets the load of 12V DC power supply in watts
- getFirmware: Gets the current firmware of the processor
- getMACAddress: Gets the MAC address of the processor
- getDeviceModel: Gets the model number of the processor
- getDevicePart: Gets the part number of the processor
- getDeviceSerial: Gets the serial number of the processor
- getStorage: Gets the processor hard drive space used, in KB
- help: will return the above list of functions
- endSession: will end the session

If the string entered in the CLI doesn't match any of the above commands, it will get sent along to a callback function if it has been defined. Use can use this callback function to test elements of code. 

Example:

```
def cliCallback(entry):
    if entry.find('TVOn') > -1:
        # do some test
        Display.Set('Power', 'On')
        
        Logger.Entry('IO', 'Do CLI action: TVOn')
        return True
        
    elif entry.find('TVOff') > -1:
        # do some test
        Display.Set('Power', 'Off')
        
        Logger.Entry('IO', 'Do CLI action: TVOff')
        return True
        
    Logger.Entry('Func', 'cliCallback({})'.format(entry))
    return False
    
CommandLine = CLI(Processor, Logger, callback = cliCallback)
```

In the above example, entering "TVOn" in the CLI would trigger the `Display.Set('Power', 'On')` method.


## extron_module_wrapper

Handles most of the logistics of defining a device using an Extron device module and the Extron Connection Handler module.

Examples:

```
Device = ExtModWrapper(ModuleName, 
					  'connection method', 
					  ['parameter 1', 'parameter 2', 'parameter 3'], 
					  'Device Model', 
					  ['List of status to Subscribe to'], 
					  LoggerModuleName)

Display = ExtModWrapper(LGTV, 
	                   'serial', 
	                   [Processor, 'COM1', 'Power'], 
	                   '86UH5C',
	                   ['Power'], 
	                   Logger)

Switcher = ExtModWrapper(DTP,
				   'ethernet', 
				   ['192.168.254.250',  23, 'Temperature'], 
				   'DTP CrossPoint 108 4K', 
				   ['OutputTieStatus', 'InputSignalStatus'], 
				   Logger) 

DSP = ExtModWrapper(DMP,
				   'ssh', 
				   ['192.168.254.251',  22023, 'PartNumber'], 
				   'DMP 128 Plus C AT', 
				   ['GroupMute', 'GroupVirtualReturnGain'], 
				   Logger)  


def Display_Status(cmd, state, qualifier):
    if cmd == 'Power':
        pass

Display.SetCallback(Display_Status)


def Switch_Status(cmd, state, qualifier):
    if cmd == 'OutputTieStatus':
        pass
        
    elif cmd == 'InputTieStatus':
        pass
        
    elif cmd == 'Temperature':
        pass
    
    elif cmd == 'ConnectionEvent':
        if state == 'Connected':
            Switcher.Dev.Update('InputTieStatus')
            Switcher.Dev.Update('OutputTieStatus')

Switcher.SetCallback(Switch_Status)


def DSP_Status(cmd, state, qualifier):
    if cmd == 'GroupMute':
        pass
        
    elif cmd == 'GroupVirtualReturnGain':
        pass
        
    elif cmd == 'ConnectionEvent':
        if state == 'Connected':
            DSP.Dev.Update('GroupMute', {'Group': '33'})
            DSP.Dev.Update('GroupMute', {'Group': '34'})
            DSP.Dev.Update('GroupMute', {'Group': '35'})
            DSP.Dev.Update('GroupMute', {'Group': '36'})
            DSP.Dev.Update('GroupMute', {'Group': '37'})
            DSP.Dev.Update('GroupMute', {'Group': '38'})
            DSP.Dev.Update('GroupVirtualReturnGain', {'Group': '1'})
            DSP.Dev.Update('GroupVirtualReturnGain', {'Group': '2'})
            DSP.Dev.Update('GroupVirtualReturnGain', {'Group': '3'})
            DSP.Dev.Update('GroupVirtualReturnGain', {'Group': '4'})
            DSP.Dev.Update('GroupVirtualReturnGain', {'Group': '5'})
            DSP.Dev.Update('GroupVirtualReturnGain', {'Group': '6'})

DSP.SetCallback(DSP_Status)



def Initialize():
	
	DSP.Dev.Connect()
    Switcher.Dev.Connect()


Initialize()

```



## room

Manages the room on/off/restart/activity status of a room as well as system on and off scheduling. Works for single rooms or systems with room combine.

```
Control = Room('Conference Room', 
               0, 
               onTime = 5, 
               offTime = 10, 
               audioTime = 1, 
               Log = Logger)


def Room_Status(command, value, qualifier):
    if command == 'Power':
        if value == 1:
            pass
        elif value == 2:
            pass
    
    elif command == 'VideoPower':
        videoPower(qualifier['Room'], value)
    
    elif command == 'AudioPower':
        audioPower(qualifier['Room'], value)
    
    elif command == 'SourcePower':
        sourcePower(qualifier['Room'], value)
    
    elif command == 'Source':
        switchSources(qualifier['Room'], value)
    
    elif command == 'Activity':
    	pass
    
    elif command == 'Restart':
        pass
    
    elif command == 'Volume':
        pass
    
    elif command == 'Mute':
        pass
    
Control.SetCallback(Room_Status)

```
Examples of using the Room.

```
Control.Set('Activity', 1)
Control.Set('Power', 2)
```