# Water-Leak-Detection-for-Munich-IoT-building
UI can be found here: http://hkurtz-nodered-dev.mybluemix.net/ui/#/0
Threshold set to: 50%
Once Threshold is met an email is sent 


#Raspberry Pi setup

### Install dependencies :
1) DHT Library
```
git clone https://github.com/adafruit/Adafruit_Python_DHT.git  
cd Adafruit_Python_DHT  
sudo python setup.py install  
```
2) Watson IoT Client library
```
pip install ibmiotf

```
3) Blink

```
pip install blynk-library-python
```
### Circuit Connection :

### To utilize the systemd service

First copy the service file to /etc/systemd/system/humidity.service then:
```
sudo systemctl enable humidity.service
```
```
sudo systemctl daemon-reload
```
