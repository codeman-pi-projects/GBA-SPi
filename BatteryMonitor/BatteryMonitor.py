 #!/usr/bin/env python
          
      
import time
import serial
import os
import signal
import ConfigParser
          

config = ConfigParser.ConfigParser()
config.read('/home/pi/GBA-SPi/BatteryMonitor/battery_monitor.config')				#read the contents of the config file
#configfile = open('/home/pi/GBA-SPi/BatteryMonitor/battery_monitor.config', 'w')	#open a file of the same name, for writing back to later
		  
PNGVIEWPATH = "/home/pi/GBA-SPi/BatteryMonitor/Pngview/"
ICONPATH = "/home/pi/GBA-SPi/BatteryMonitor/icons"
XOFFSET = config.get('offset_values', 'X')
YOFFSET = config.get('offset_values', 'Y')
STYLE = config.get('battery_style', 'Style')
CurrentPicture = "Current"
NewPicture = "New"
DISPLAY = "OFF"
BRIGHTNESSXOFFSET = 100
BRIGHTNESSYOFFSET = 180
BrightnessPicture = ""

UP_BCM = 26
DOWN_BCM = 13
LEFT_BCM = 16
RIGHT_BCM = 12
START_BCM = 22
SELECT_BCM = 27
A_BCM = 6
B_BCM = 5
X_BCM = 7
Y_BCM = 23
L_BCM = 17
R_BCM = 4

#put these up here in case the thresholds want to be changed
BATTERYLOW = 10
BATTERY12 = 12
BATTERY25 = 25
BATTERY37 = 37
BATTERY50 = 50
BATTERY62 = 62
BATTERY75 = 75
BATTERY87 = 87
BATTERY100 = 100
BATTERYCHARGING = 101

		  
      
ser = serial.Serial(
	port='/dev/ttyAMA0',
	baudrate = 19200,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
#	timeout=1							#timeout every second, so other things can be serviced if necessary
)

#clean up the serial port, configuration file, and PNGview process when exiting
def cleanup(signalnum=None, handler=None):
	ser.flushInput()  
	ser.close()  #close the serial port
#	config.write(configfile)	#write the configurations back to the file
#	configfile.close()			#close the config file
	KillPNGView()
	exit(0)

#define the function to be called on termination signals 
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

def SetIcon(charge):
	global NewPicture
	global CurrentPicture

	if ord(charge) == 0:
		NewPiture = "LowCharge"
	elif ord(charge) <= BATTERYLOW:
		NewPicture = "LowCharge"	#names of the battery picture files
	elif ord(charge) <= BATTERY12:
		NewPicture = "charge12p5"
	elif ord(charge) <= BATTERY25:
		NewPicture = "charge25"
	elif ord(charge) <= BATTERY37:
		NewPicture = "charge37p5"
	elif ord(charge) <= BATTERY50:
		NewPicture = "charge50"
	elif ord(charge) <= BATTERY62:
		NewPicture = "charge62p5"
	elif ord(charge) <= BATTERY75:
		NewPicture = "charge75"
	elif ord(charge) <= BATTERY87:
		NewPicture = "charge87p5"
	elif ord(charge) <= BATTERY100:
		NewPicture = "charge100"
	else:
		NewPicture = "charging"
		
	
	#if the new picture is different from the current picture, then display it, otherwise do nothing
	if NewPicture != CurrentPicture:
		CurrentPicture = NewPicture		#update the current picture
		
		#only update the display if we want it on
		if DISPLAY == "ON":
			UpdateDisplay()


def UpdateDisplay():
	KillPNGView() #kill them all to remove the battery indicator, causes the icon to flash but i dont' care
				  #  maybe eventually change this to add the new battery icon, then kill just the old ones?
				  #Not sure I care enough about the icon flashing
	os.system(PNGVIEWPATH + "/pngview -b 0 -l 99999 -x " + str(XOFFSET) + " -y " + str(YOFFSET) + " " + ICONPATH + "/" + "Style" + STYLE + "/" + NewPicture + ".png &")
		
	
def SetDisplay(ON_OFF):
	global DISPLAY
#	print ord(ON_OFF)
	if ord(ON_OFF) == 0:
		DISPLAY = "OFF"
		KillPNGView()	#kill all the pngview processes to clear the screen
	else:
		DISPLAY = "ON"
		UpdateDisplay()
	
def BrightnessUpdate(brightness_high, brightness_low):
	global DISPLAY
	#If the battery display is on, then turn it off for brightness adjustment
	if DISPLAY == "ON":
		SetDisplay(0)
	
	BrightnessValue = (brightness_high * 256) + brightness_low
	
	#Uncomment and use this when I have all the brightness pictures available
	BrightnessPicture = "percent" + str(myround(BrightnessValue))
	
	#for now just use this hardcoded value:
	#BrightnessPicture = "percent" + str(95)
	
	#First set the new brightness on screen icon, then kill any other pngview processes
	#  This should give a smooth update without things flashing?
	i = 0
        killid = 0
        os.system(PNGVIEWPATH + "/pngview -b 0 -l 99999 -x " + str(BRIGHTNESSXOFFSET) + " -y " + str(BRIGHTNESSYOFFSET) + " " + ICONPATH + "/" + "Brightness" + "/" + BrightnessPicture + ".png &")
        out = check_output("ps aux | grep pngview | awk '{ print $2 }'", shell=True)
        nums = out.split('\n')
        for num in nums:
            i += 1
            if i == 1:
                killid = num
		os.system("sudo kill " + killid)

		
def myround(x, base=5):
    return int(base * round(float(x)/base))

	
def KillPNGView():
	#print("killed all")
	os.system("sudo killall -q pngview")
	

#only an 8-bit bus, but offsets can be higher than 255, so
# split the high and low bits of the offset for transmitting,
# and stitch the full number back together here
def	SetXOFFSET(offset_high, offset_low):
	global XOFFSET
	XOFFSET = (ord(offset_high)*256) + ord(offset_low)
#	config.set('offset_values', 'X', XOFFSET)	#update the config with the new value
	UpdateDisplay()
#	print XOFFSET

def	SetYOFFSET(offset_high, offset_low):
	global YOFFSET
	YOFFSET = (ord(offset_high)*256) + ord(offset_low)
#	config.set('offset_values', 'Y', YOFFSET)	#update the config with the new value
	UpdateDisplay()
	
	
def SendButtonValue(channel):
	ser.write(str(channel).encode())
	
	
def ButtonMonitor():
	GPIO.setup(UP_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(DOWN_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(LEFT_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(RIGHT_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(START_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(SELECT_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(A_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(B_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(X_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(Y_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(L_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(R_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	GPIO.add_event_detect(UP_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(DOWN_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(LEFT_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(RIGHT_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(START_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(SELECT_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(A_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(B_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(X_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(Y_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(L_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	GPIO.add_event_detect(R_BCM, GPIO.FALLING, callback = SendButtonValue, bouncetime = 200)
	
	while (ser.read() != 'Q'):
		time.sleep(0.05)
	
	


ser.flushInput()	#flush the input of everything
while (ser.read() != 'E'):  #wait here for the echo, use this to sync with the microcontroller 
	pass
	
#Run this forever basically

#The serial port will read string commands coming from the microcontroller
#The commands follow this syntax:
#Command Arg1 Arg2
#but all values are just integers, or ASCII characters only
while 1:
	commands = []	#create and clear my array for reading in the commands
	i = 0			#index counter
	
	#need to do an initial serial read, then keep checking if the
	#  read value is 'Q', for Quit.  Otherwise keep reading.  'Q' ends the command array
	commands.append(ser.read())		#need to just keep appending to the array
	
	while commands[i] != 'Q':
#		print commands		#here for debug
		commands.append(ser.read())	
		i+=1		#because i++ doesn't exist...?! dumb


	#'S' for shutdown
	if commands[0] == 'S':
		cleanup()
	#'I' for icon change, the next value is the battery value integer
	# greater than 100 means plugged in
	elif commands[0] == 'I':
		SetIcon(commands[1])	#sets the proper battery icon based off the number sent
	#'D' for display setting, next value is 'Y' or 'N', followed by battery value
	elif commands[0] == 'D':
		#the command must be ['D', 'Y']
		SetDisplay(commands[1])	#turns the battery display on or off
	#'X' for setting the X offset, next value is pixel offset
	elif commands[0] == 'X':
		SetXOFFSET(commands[1], commands[2])
	#'Y' for setting the Y offset, next value is pixel offset
	elif commands[0] == 'Y':
		SetYOFFSET(commands[1], commands[2])
	#'E' for echo, to check if the Pi is alive
	elif commands[0] == 'E':	
		ser.write('e')
	#'V' for visualizing the brightness on screen
	elif commands[0] == 'V':	
		BrightnessUpdate(commands[1], commands[2])
	#'B' for button monitor, used for board testing only!
	elif commands[0] == 'B':	
		ButtonMonitor()
#	else:
		#do nothing in the else case, that means the read timed out because nothing was sent
