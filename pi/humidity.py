# Best humidity sensor code
# @Authors = Angelo Danducci
# @Authors = Hari hara prasad Viswanathan
import Adafruit_DHT
import ibmiotf.device
import threading
import BlynkLib
import time
import sys

# iotp and setup
organization = "h9eyui"
deviceType = "waterLeakDetector"
deviceId = "20WestSensor1"
appId = deviceId + "_receiver"
authMethod = "token"
authToken = "watsoniot"
blynkToken = "bb1475ed813446248525d5e9374d32c8"


#CHOP THESE DOWN TO THREE digits
def getData():
    humidity, celsius = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4)

    fahrenheit = (celsius * 1.8) + 32 

    data = { 
        'fahrenheit' : round(fahrenheit,1),
        'humidity' : round(humidity,1),
	 'celsius' : round(celsius,1),
        'temperature' : round(celsius,1)
    }

    return data

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()

    return t

def myOnPublishCallback():
		print("Confirmed event received by IoTF\n" )

def publish():
    deviceCli.publishEvent("WaterData", "json", getData(), qos=0, on_publish=myOnPublishCallback)

# Connect to Blynk and WIOTP
try:
    Blynk = BlynkLib.Blynk(blynkToken)
    deviceOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
    deviceCli = ibmiotf.device.Client(deviceOptions)
except Exception as e:
    print(str(e))
    sys.exit()


# set up blynk defs
@Blynk.VIRTUAL_READ(5)
def V5_read_handler():
    data = getData()
    Blynk.virtual_write(5, data["humidity"])

@Blynk.VIRTUAL_READ(6)
def V6_read_handler():
    data = getData()
    Blynk.virtual_write(6, data["fahrenheit"])

@Blynk.VIRTUAL_READ(7)
def V7_read_handler():
    data = getData()
    Blynk.virtual_write(7, data["celsius"])


deviceCli.connect()
publish()
set_interval(publish,60*1)
Blynk.run()
    
    
