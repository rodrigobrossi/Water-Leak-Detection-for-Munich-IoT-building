# Best humidity sensor code
# @Authors = Angelo Danducci
# @Authors = Hari hara prasad Viswanathan
import os
import json
import Adafruit_DHT
import paho.mqtt.client as mqtt
import threading
import BlynkLib
import time
import sys

# Credentials loaded from environment variables
# Copy sensors/pi/.env.example to sensors/pi/.env and fill in your values,
# then run: source .env && python humidity.py
organization = os.environ.get("IOT_ORG")
deviceType   = os.environ.get("IOT_DEVICE_TYPE", "waterLeakDetector")
deviceId     = os.environ.get("IOT_DEVICE_ID")
authToken    = os.environ.get("IOT_TOKEN")
blynkToken   = os.environ.get("BLYNK_TOKEN")

if not all([organization, deviceId, authToken, blynkToken]):
    print("[ERROR] Missing required environment variables. See sensors/pi/.env.example")
    sys.exit(1)

broker    = "{}.messaging.internetofthings.ibmcloud.com".format(organization)
client_id = "d:{}:{}:{}".format(organization, deviceType, deviceId)
topic     = "iot-2/evt/status/fmt/json"


def getData():
    humidity, celsius = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4)
    fahrenheit = (celsius * 1.8) + 32
    return {
        'fahrenheit' : round(fahrenheit, 1),
        'humidity'   : round(humidity, 1),
        'celsius'    : round(celsius, 1),
        'temperature': round(celsius, 1)
    }

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def publish():
    data = getData()
    payload = json.dumps(data)
    result = mqtt_client.publish(topic, payload, qos=0)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("Published: {}".format(payload))
    else:
        print("[ERROR] Publish failed with code {}".format(result.rc))

# --- MQTT setup ---
mqtt_client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
mqtt_client.username_pw_set("use-token-auth", authToken)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to IBM Watson IoT Platform")
    else:
        print("[ERROR] MQTT connection failed with code {}".format(rc))
        sys.exit(1)

mqtt_client.on_connect = on_connect

try:
    mqtt_client.connect(broker, 1883, keepalive=60)
    mqtt_client.loop_start()
except Exception as e:
    print("[ERROR] Could not connect to broker: {}".format(e))
    sys.exit(1)

# --- Blynk setup ---
try:
    Blynk = BlynkLib.Blynk(blynkToken)
except Exception as e:
    print("[ERROR] Blynk connection failed: {}".format(e))
    sys.exit(1)

@Blynk.VIRTUAL_READ(5)
def V5_read_handler():
    Blynk.virtual_write(5, getData()["humidity"])

@Blynk.VIRTUAL_READ(6)
def V6_read_handler():
    Blynk.virtual_write(6, getData()["fahrenheit"])

@Blynk.VIRTUAL_READ(7)
def V7_read_handler():
    Blynk.virtual_write(7, getData()["celsius"])

publish()
set_interval(publish, 60)
Blynk.run()
