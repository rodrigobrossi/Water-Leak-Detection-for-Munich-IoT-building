# Water Damage Prevention System

Real-time water leak detection and damage prevention system for the **IBM Munich Watson IoT Center**. Monitors humidity via IoT sensors, automatically detects leaks, and triggers multi-channel notifications with a web-based incident response workflow.

<img src="/img/sensor.png" width="200"/> <img src="/img/UI.png" width="400"/>

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          SENSOR LAYER                           │
│                                                                 │
│  Raspberry Pi (humidity.py)          ESP8266 (dhttemp.ino)      │
│  DHT/AM2302 sensor on GPIO pin 4     DHT22 sensor on pin D4     │
│  Publishes every 60 seconds          Publishes every 5 seconds  │
│                 │                                │              │
│                 └──────────────┬─────────────────┘              │
└────────────────────────────────┼────────────────────────────────┘
                                 │ MQTT (port 1883)
                                 ▼
                   IBM Watson IoT Platform
                   Topic: iot-2/evt/status/fmt/json
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────---───┐
│                  CLOUD BACKEND (Flask + Gevent)                   │
│                                                                   │
│  BDPIncident ──► Incident detection by humidity level             │
│       │          < 50% → OK | 50-75% → MODERATE | >75% → CRITICAL │
│       ▼                                                           │
│  BDPNotifier ──► Email (Gmail SMTP)                               │
│                ──► Slack (Webhook)                                │
│                ──► Tririga (FM Service Request)                   │
│                                                                   │
│  BDPRespond  ──► Web UI: /respond?nid=<id>                        │
│                    ├── SNOOZE (defer alert)                       │
│                    └── FIXED (mark as resolved)                   │
│                                                                   │
│  REST APIs                                                        │
│  ├── POST /tenant    ──► Register organization                    │
│  ├── POST /user      ──► Register users                           │
│  └── POST /hardware  ──► Register sensors                         │
│                                                                   │
└───────────────────────────────────────────────────────────────---─┘
                                 │
                                 ▼
                         IBM Db2 Database
              BDP_TENANT | BDP_USER | BDP_HARDWARE
              BDP_INCIDENT | BDP_NOTIFICATION | BDP_RAW_EVENTS
```

---

## Repository Structure

```
.
├── sensors/
│   ├── pi/                   # Raspberry Pi implementation
│   │   ├── humidity.py       # DHT sensor data collection, publishes via MQTT and Blynk
│   │   ├── MarkovModel.py    # Predictive Markov chain model for state transitions (dry/wet)
│   │   └── humidity.service  # systemd service file for auto-start on boot
│   └── dhttemp/              # ESP8266 implementation (Arduino)
│       └── dhttemp.ino       # Firmware: MQTT + Blynk + OLED SSD1306 display
│
└── cloud_app/BuildingDamageProtection/
    ├── Dockerfile
    ├── Procfile              # IBM Cloud Foundry deployment config
    ├── requirements.txt      # Python dependencies
    ├── runtime.txt           # Python 3.11
    └── src/main/python/
        ├── gateway.py              # Flask entry point: defines routes and starts threads
        ├── bdp_incident.py         # IoT event listener + incident detection logic
        ├── bdp_notifier.py         # Notification orchestration (email/Slack/Tririga)
        ├── bdp_respond.py          # Incident response web UI handler
        ├── bdp_hardware.py         # REST API for sensor management
        ├── bdp_tenant.py           # REST API for multi-tenancy
        ├── bdp_user.py             # REST API for user management
        ├── bdp_auth.py             # HTTP Basic Auth
        ├── bdp_property.py         # config.json singleton loader
        ├── bdp_dbutil.py           # Db2 queries + connection pooling
        ├── bdp_util.py             # Gmail, Slack, and Tririga integrations
        ├── bdp_sysinit.py          # Database schema initialization and migrations
        ├── bdp_servicecheck.py     # Periodic DB connection health check
        ├── bdp_email.py            # Email data model
        ├── bdp_tririga_worktask.py # Tririga FM system integration
        ├── bdp_unittest.py         # Unit tests
        ├── templates/              # HTML/text templates for emails and web UI
        └── static/                 # CSS and images for the web interface
```

---

## Components in Detail

### 1. Sensors (`sensors/`)

#### Raspberry Pi — `humidity.py`
- Reads temperature and humidity from a **DHT/AM2302** sensor on GPIO pin 4
- Publishes readings every **60 seconds** via MQTT to IBM Watson IoT Platform
- Exposes data to the **Blynk** mobile app (virtual pins V5=humidity, V6=fahrenheit, V7=celsius)
- Can run as a systemd service (`humidity.service` included)

#### ESP8266 — `dhttemp.ino`
- Reads temperature and humidity from a **DHT22** sensor on pin D4
- Displays readings on an **OLED SSD1306** display (I2C)
- Publishes via MQTT to IBM Watson IoT Platform every **5 seconds**
- Integrates with **Blynk** on the same virtual pins

#### Predictive Model — `MarkovModel.py`
- Implements a **Markov Chain** to predict state transitions (dry → wet)
- Uses maximum likelihood estimation for parameter fitting

---

### 2. Cloud Backend (`cloud_app/`)

#### `gateway.py` — Entry Point
- Initializes the Flask app with Gevent WSGI for async request handling
- Registers all REST routes
- Starts a background thread for periodic health checks
- Connects to IBM Watson IoT Platform to listen for sensor events
- Server modes: `flask` (dev), `cli` (no HTTP server), or WSGI with SSL

#### `bdp_incident.py` — Incident Detection
- Listens for MQTT events from device types: `waterLeakDetector` and `waterSensorsDemo`
- Stores raw readings in `BDP_RAW_EVENTS` (7-day retention)
- **Detection logic:**
  - Humidity < 50% → No incident
  - Humidity 50–75% → **MODERATE** incident
  - Humidity > 75% → **CRITICAL** incident
- Prevents duplicate active incidents per tenant + sensor

#### `bdp_notifier.py` — Notification Orchestration
- Determines which users to notify based on **time of day** (business hours vs. off-hours)
- Manages notification lifecycle: **ALARM → SNOOZE → FIXED**
- Renders Mustache templates for emails and Slack messages
- Creates service requests in **Tririga** (facilities management system)

#### `bdp_respond.py` — Response Interface
- Route `GET /respond?nid=<notification_id>`: renders UI with incident details
- Displays humidity history chart, urgency level, and current status
- Allows the user to:
  - **SNOOZE**: Defer the alert for N hours (configurable)
  - **FIXED**: Mark the incident as resolved

#### `bdp_dbutil.py` — Data Layer
Manages a singleton connection to **IBM Db2**. Main tables:

| Table                | Description                                     |
|----------------------|-------------------------------------------------|
| `BDP_TENANT`         | Organizations / system clients                  |
| `BDP_USER`           | Users with contact info and availability hours  |
| `BDP_HARDWARE`       | Sensors with physical location details          |
| `BDP_INCIDENT`       | Detected water incidents                        |
| `BDP_NOTIFICATION`   | Individual per-user notifications               |
| `BDP_RAW_EVENTS`     | Raw sensor readings (7-day rolling retention)   |
| `BDP_DBCHANGELOG`    | Database schema version tracking               |

---

## Prerequisites

### Cloud Backend
- Python 3.11
- IBM Db2 (local or IBM Cloud)
- IBM Watson IoT Platform (IBM Cloud account)
- Gmail account with App Password enabled
- Slack Bot Token (optional)
- Tririga API credentials (optional)

### Raspberry Pi Sensor
- Raspberry Pi (any model with GPIO)
- DHT11, DHT22, or AM2302 sensor
- Python 3.x

### ESP8266 Sensor
- ESP8266 board (NodeMCU, Wemos D1 Mini, etc.)
- DHT22 sensor
- OLED SSD1306 display (optional)
- Arduino IDE 1.8+

---

## Local Setup — Backend

### 1. Configuration

Copy the example config and fill in your credentials:

```bash
cp cloud_app/BuildingDamageProtection/resources/config/config.example.json \
   cloud_app/BuildingDamageProtection/resources/config/config.json
```

Edit `config.json` with your credentials (see the [Configuration](#configuration) section for details).

### 2. Install Dependencies

```bash
cd cloud_app/BuildingDamageProtection
pip install -r requirements.txt
```

> **Note:** The `ibm_db` package requires the IBM Db2 Client to be installed on the system.
> See: [ibm-db on PyPI](https://pypi.org/project/ibm-db/)

### 3. Run

```bash
# Development mode (Flask)
cd cloud_app/BuildingDamageProtection/src/main/python
python gateway.py

# Production mode (Gunicorn)
cd cloud_app/BuildingDamageProtection
gunicorn -w 3 --pythonpath src/main/python --log-level debug gateway:application
```

### 4. Docker

```bash
cd cloud_app/BuildingDamageProtection
docker build -t building-damage-protection .
docker run -p 5000:5000 building-damage-protection
```

### 5. Tests

```bash
python src/main/python/bdp_unittest.py
```

---

## Local Setup — Raspberry Pi Sensor

```bash
# 1. Install the DHT sensor library
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python setup.py install

# 2. Install IoT and Blynk dependencies
pip install paho-mqtt
pip install blynk-library-python

# 3. Set credentials via environment variables
cp sensors/pi/.env.example sensors/pi/.env
# Edit .env with your IOT_ORG, IOT_DEVICE_ID, IOT_TOKEN, BLYNK_TOKEN

# 4. Run
source sensors/pi/.env
cd sensors/pi
python humidity.py

# 5. (Optional) Install as a systemd service
sudo cp humidity.service /etc/systemd/system/
sudo systemctl enable humidity.service
sudo systemctl daemon-reload
sudo systemctl start humidity.service
```

---

## Setup — ESP8266 Sensor

1. Open `sensors/dhttemp/dhttemp.ino` in the **Arduino IDE**
2. Install required libraries via Library Manager:
   - `PubSubClient` (MQTT)
   - `ESP8266WiFi`
   - `Blynk`
   - `Adafruit GFX Library`
   - `Adafruit SSD1306`
   - `DHT sensor library` (Adafruit)
3. Copy the credentials template and fill in your values:
   ```bash
   cp sensors/dhttemp/credentials.h.example sensors/dhttemp/credentials.h
   # Edit credentials.h with your WiFi, Blynk, and IoT credentials
   ```
4. Select the correct board (e.g. `NodeMCU 1.0`) and upload the sketch

---

## Configuration

The config file must be placed at:
`cloud_app/BuildingDamageProtection/resources/config/config.json`

```json
{
  "ver": "1.0",
  "server_type": "flask",
  "server_port": "5000",
  "https_key": "",
  "https_cert": "",
  "gateway_user": "admin",
  "gateway_password": "change_me",
  "db_dbname": "BLUDB",
  "db_dbhost": "localhost",
  "db_dbport": "50000",
  "db_admin_user": "db2admin",
  "db_admin_password": "change_me",
  "iotplatform_options": {
    "org": "YOUR_ORG_ID",
    "id": "cloud-app",
    "auth-method": "apikey",
    "auth-key": "YOUR_API_KEY",
    "auth-token": "YOUR_AUTH_TOKEN"
  },
  "gmail_user": "your@gmail.com",
  "gmail_password": "your_app_password",
  "slack_auth": "xoxb-your-slack-bot-token",
  "tririga_api": "https://your-instance.tririga.com/api/",
  "tririga_user": "tririga_username",
  "tririga_password": "change_me",
  "alarm_interval_hr": "1",
  "snooze_hr": "2",
  "check_status_interval": "24"
}
```

### Configuration Parameters

| Parameter              | Description                                                          |
|------------------------|----------------------------------------------------------------------|
| `server_type`          | `flask` (dev), `cli` (no HTTP server), or any other value (WSGI/SSL) |
| `server_port`          | HTTP server port                                                     |
| `gateway_user/password`| HTTP Basic Auth credentials for REST API endpoints                   |
| `db_*`                 | IBM Db2 connection credentials                                       |
| `iotplatform_options`  | IBM Watson IoT Platform application credentials                      |
| `gmail_user/password`  | Gmail account used to send alert emails                              |
| `slack_auth`           | Slack bot token for message delivery                                 |
| `tririga_*`            | Tririga FM system API credentials                                    |
| `alarm_interval_hr`    | Minimum interval between repeated alarms (hours)                     |
| `snooze_hr`            | Duration of a notification snooze (hours)                            |
| `check_status_interval`| Frequency of DB connection health checks (hours)                     |

---

## How It Works

```
1. Sensor detects humidity above threshold
        ↓
2. Publishes reading via MQTT to IBM Watson IoT Platform
        ↓
3. BDPIncident receives the event and evaluates urgency level
        ↓
4. Creates an incident record in the database (BDP_INCIDENT)
        ↓
5. BDPNotifier identifies responsible users
   (business hours vs. off-hours groups)
        ↓
6. Sends notifications: Email + Slack + Tririga (Service Request)
   The email contains a response link: /respond?nid=<id>
        ↓
7. User opens the link → views incident details, history, and chart
        ↓
8. User takes action:
   ├── SNOOZE: silence the alert for N hours
   └── FIXED: mark the incident as resolved
```

---

## REST Endpoints

All endpoints require **HTTP Basic Auth** (`gateway_user` / `gateway_password`).

| Method     | Endpoint    | Description                              |
|------------|-------------|------------------------------------------|
| `GET`      | `/`         | Health check — returns version and status |
| `GET/POST` | `/respond`  | Incident response web UI                 |
| `POST`     | `/tenant`   | Register a tenant / organization         |
| `POST`     | `/user`     | Register a user with availability hours  |
| `POST`     | `/hardware` | Register a sensor / detector             |

---

## Security Notice

> **IMPORTANT:** Sensor source files previously contained hardcoded credentials (IoT tokens, Blynk tokens, WiFi passwords). These have been moved to environment variables and a gitignored `credentials.h` file. Before deploying:
>
> - Generate new tokens on IBM Watson IoT Platform
> - Generate a new Blynk token
> - Never commit `config.json` or `credentials.h` with real credentials

---

## Suggested Improvements

- [ ] Create a `docker-compose.yml` with Db2 + App for a one-command local setup
- [ ] Add support for multiple sensor types and protocols beyond IBM Watson IoT
- [ ] Build a real-time web dashboard for live humidity visualization
- [ ] Replace HTTP Basic Auth with JWT on REST endpoints

---

## Tech Stack

| Layer        | Technology                                              |
|--------------|---------------------------------------------------------|
| Sensor (Pi)  | Python, Adafruit DHT, paho-mqtt, BlynkLib               |
| Sensor (ESP) | C++/Arduino, PubSubClient, ESP8266WiFi, Blynk           |
| Backend      | Python 3.11, Flask 3.0, Gevent, Flask-RESTful           |
| Database     | IBM Db2                                                 |
| IoT Platform | IBM Watson IoT Platform (MQTT)                          |
| Notifications| Gmail SMTP, Slack API, IBM Tririga                      |
| Deployment   | IBM Cloud Foundry, Docker                               |

---

## Authors

- Rodrigo Brossi — IBM
- Angelo Danducci — IBM
- Hari Hara Prasad Viswanathan — IBM

Developed for the **IBM Munich Watson IoT Center** — 2018/2019.
