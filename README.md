# Notification system: BuildingDamageProtection
To start the application locally with docker:
```
docker build -t building-damage-protection .
docker run building-damage-protection
```

To start the application locally without docker:
```
pip install -r requiremets.txt
gunicorn -w 3 --pythonpath src/main/python/ --log-level debug gateway:application 
```
To run the unittests:
```
python src/main/python/bdp_unittest.py
```

To run the unittests with docker:
```
docker ps
docker exec -it {{ container id }} /bin/sh
python src/main/python/bdp_unittest.py
```
Documentations: docs/build/index.html


# Raspberry Pi setup
### Clone the Repo :
```
git clone git@github.ibm.com:Watson-IoT/Water-Leak-Detection-for-Munich-IoT-building.git
```
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
(recommended 4.7k or 10k ohm resistor)
![alt diag](https://raw.github.ibm.com/Watson-IoT/Water-Leak-Detection-for-Munich-IoT-building/master/pi/connection.png?token=AAA7dqBb2AgPHmazQfMl0czwWfqgH8gSks5cB_IRwA%3D%3D)

### Run

```
cd pi

python humidity.py

```
### To utilize the systemd service

First copy the service file to /etc/systemd/system/humidity.service then:
```
sudo systemctl enable humidity.service
```
```
sudo systemctl daemon-reload
```
