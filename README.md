# Water Damage Prevention System

Real-time water leak detection and damage prevention system for the **IBM Munich Watson IoT Center**. Monitors humidity via IoT sensors, automatically detects leaks, and triggers multi-channel notifications with a web-based incident response workflow.

---

## Screenshots

### Web Dashboard — `http://localhost:5001/dashboard`

![Dashboard](docs/images/dashboard.png)

Live view of all registered sensors, active incidents, and humidity status. Auto-refreshes every 30 seconds.

### 3D Building Map — `http://localhost:5001/map3d`

![3D Map](docs/images/map3d.png)

Interactive 3D building visualization with sensors placed at their physical locations. Click any sensor to inspect its latest readings.

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
┌──────────────────────────────────────────────────────────────────┐
│                  CLOUD BACKEND (Flask + Gevent)                  │
│                                                                  │
│  BDPIncident ──► Incident detection by humidity level            │
│       │          < 50% → OK | 50-75% → MODERATE | >75% → CRITICAL│
│       ▼                                                          │
│  BDPNotifier ──► Email (Gmail SMTP)                              │
│                ──► Slack (Webhook)                               │
│                ──► Tririga (FM Service Request)                  │
│                                                                  │
│  BDPRespond  ──► Web UI: /respond?nid=<id>                       │
│                    ├── SNOOZE (defer alert)                      │
│                    └── FIXED  (mark as resolved)                 │
│                                                                  │
│  REST APIs  (Basic Auth required)                                │
│  ├── POST /tenant    ──► Register organization                   │
│  ├── POST /user      ──► Register users                          │
│  ├── POST /hardware  ──► Register sensors                        │
│  ├── GET  /api/tenants   ──► List tenants                        │
│  ├── GET  /api/hardware  ──► List sensors + latest readings      │
│  ├── GET  /api/incidents ──► List recent incidents               │
│  └── GET  /api/events/<uid> ──► Raw events for a sensor          │
│                                                                  │
│  Web UI                                                          │
│  ├── GET /dashboard  ──► Live sensor dashboard                   │
│  └── GET /map3d      ──► Interactive 3D building map             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
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
│   │   ├── humidity.py       # DHT sensor reader, publishes via paho-mqtt and Blynk
│   │   ├── .env.example      # Credentials template (copy to .env)
│   │   ├── MarkovModel.py    # Predictive Markov chain model (dry/wet state transitions)
│   │   └── humidity.service  # systemd service file for auto-start on boot
│   └── dhttemp/              # ESP8266 implementation (Arduino)
│       ├── dhttemp.ino       # Firmware: MQTT + Blynk + OLED SSD1306 display
│       └── credentials.h.example  # Credentials template (copy to credentials.h)
│
└── cloud_app/BuildingDamageProtection/
    ├── Dockerfile                        # python:3.11-slim image
    ├── docker-compose.yml                # Db2 + App — one-command local setup
    ├── requirements.txt                  # Python dependencies (Python 3.11)
    ├── runtime.txt                       # Python 3.11
    ├── resources/
    │   ├── config/
    │   │   ├── config.example.json       # Credentials template (copy to config.json)
    │   │   └── config.json               # Active config — gitignored, never commit
    │   └── db/db2/
    │       ├── init.sql                  # Creates BDP_DBCHANGELOG (migration tracking)
    │       ├── db.changelog.xml          # Migration manifest
    │       └── 001_create_tables.sql     # Full schema: all 6 application tables
    └── src/main/python/
        ├── gateway.py              # Flask entry point: routes, threads, startup
        ├── bdp_incident.py         # IoT MQTT listener + humidity threshold detection
        ├── bdp_notifier.py         # Notification orchestration (email/Slack/Tririga)
        ├── bdp_respond.py          # Incident response web UI (SNOOZE / FIXED)
        ├── bdp_dashboard.py        # REST API for dashboard (GET endpoints)
        ├── bdp_hardware.py         # POST /hardware — register sensors
        ├── bdp_tenant.py           # POST /tenant  — register organizations
        ├── bdp_user.py             # POST /user    — register users
        ├── bdp_auth.py             # HTTP Basic Auth helper
        ├── bdp_property.py         # config.json singleton loader
        ├── bdp_dbutil.py           # Db2 connection + all query functions
        ├── bdp_util.py             # Gmail, Slack, and Tririga integrations
        ├── bdp_sysinit.py          # DB schema init + migration runner on startup
        ├── bdp_servicecheck.py     # Periodic DB health check (background thread)
        ├── bdp_email.py            # Email data model
        ├── bdp_tririga_worktask.py # Tririga FM system integration
        ├── bdp_unittest.py         # Unit tests
        ├── templates/
        │   ├── dashboard.html      # Live sensor dashboard (dark UI, Chart.js)
        │   ├── map3d.html          # Interactive 3D building map (Three.js)
        │   ├── respond.html        # Incident response page (links from emails)
        │   ├── alarm_email.html/txt
        │   ├── fixed_email.html/txt
        │   └── snooze_email.html/txt
        └── static/                 # CSS and images for the web interface
```

---

## Components in Detail

### 1. Sensors (`sensors/`)

#### Raspberry Pi — `humidity.py`
- Reads temperature and humidity from a **DHT/AM2302** sensor on GPIO pin 4
- Publishes readings every **60 seconds** via MQTT to IBM Watson IoT Platform
- Topic: `iot-2/evt/status/fmt/json`
- Payload: `{"humidity": 42.5, "temperature": 22.1}`
- Exposes data to the **Blynk** mobile app (virtual pins V5=humidity, V6=fahrenheit, V7=celsius)
- All credentials loaded from environment variables — never hardcoded

#### ESP8266 — `dhttemp.ino`
- Reads temperature and humidity from a **DHT22** sensor on pin D4
- Displays readings on an **OLED SSD1306** display (I2C)
- Publishes via MQTT to IBM Watson IoT Platform every **5 seconds**
- Integrates with **Blynk** on the same virtual pins
- All credentials loaded from `credentials.h` — gitignored

#### Predictive Model — `MarkovModel.py`
- Implements a **Markov Chain** to predict state transitions (dry → wet)
- Uses maximum likelihood estimation for parameter fitting

---

### 2. Cloud Backend (`cloud_app/`)

#### `gateway.py` — Entry Point
- Initializes Flask app with Gevent WSGI for async request handling
- Registers all REST and UI routes
- Starts a background thread for periodic health checks (`BDPServiceCheck`)
- Subscribes to IoT MQTT events via `BDPIncident.start()`
- **Database schema** is auto-initialized and migrated on every startup via `BDPSysInit`
- Server modes: `flask` (dev), `cli` (no HTTP server), or Gevent WSGI with optional SSL

#### `bdp_incident.py` — Incident Detection
- Subscribes to MQTT topics:
  - `iot-2/type/waterLeakDetector/id/+/evt/+/fmt/json`
  - `iot-2/type/waterSensorsDemo/id/+/evt/+/fmt/json`
- Stores every reading in `BDP_RAW_EVENTS`
- **Detection thresholds:**
  - Humidity < 50% → No incident
  - Humidity 50–75% → **MODERATE** incident
  - Humidity > 75% → **CRITICAL** incident
- Prevents duplicate active incidents per tenant + sensor combination

#### `bdp_notifier.py` — Notification Orchestration
- Determines which users to notify based on **time of day** (business hours vs. off-hours)
- Manages notification lifecycle: **ALARM → SNOOZE → FIXED**
- Renders Mustache templates for emails and Slack messages
- Creates service requests in **Tririga** (facilities management system)

#### `bdp_respond.py` — Response Interface
- `GET /respond?nid=<notification_id>` — renders UI with incident details, sensor chart, urgency level
- `POST /respond` — handles user action:
  - **SNOOZE**: Defer the alert for `snooze_hr` hours (configurable)
  - **FIXED**: Mark the incident as resolved

#### `bdp_dashboard.py` — Web Dashboard API
New GET endpoints that power the live dashboard and 3D map:

| Endpoint | Returns |
|---|---|
| `GET /api/tenants` | All registered tenants |
| `GET /api/hardware` | All sensors with last reading + timestamp |
| `GET /api/incidents` | Last 100 incidents with sensor details |
| `GET /api/events/<uid>` | Last 120 raw events for a specific sensor |

#### `bdp_sysinit.py` — Auto Schema Migration
- On startup, checks if DB tables exist
- If the DB is empty: runs `init.sql` (creates `BDP_DBCHANGELOG`)
- Reads `db.changelog.xml` and applies any pending migration scripts
- Tracks applied migrations by ID in `BDP_DBCHANGELOG`

#### `bdp_dbutil.py` — Data Layer
Singleton Db2 connection with all query functions. Tables:

| Table              | Description                                     |
|--------------------|-------------------------------------------------|
| `BDP_TENANT`       | Organizations / system clients                  |
| `BDP_USER`         | Users with contact info and availability hours  |
| `BDP_HARDWARE`     | Sensors with type, ID, and location             |
| `BDP_INCIDENT`     | Detected water incidents with status            |
| `BDP_NOTIFICATION` | Per-user notifications with response tracking  |
| `BDP_RAW_EVENTS`   | Raw sensor readings (rolling retention)         |
| `BDP_DBCHANGELOG`  | Applied database migration tracking             |

---

## Prerequisites

### Cloud Backend
- Docker + Docker Compose (recommended — one-command setup)
- **Or:** Python 3.11, IBM Db2, IBM Watson IoT Platform credentials

### Raspberry Pi Sensor
- Raspberry Pi (any model with GPIO)
- DHT11, DHT22, or AM2302 sensor on GPIO pin 4
- Python 3.x

### ESP8266 Sensor
- ESP8266 board (NodeMCU, Wemos D1 Mini, etc.)
- DHT22 sensor wired to pin D4
- OLED SSD1306 display (optional, I2C)
- Arduino IDE 1.8+

---

## Local Setup — Docker (Recommended)

The fastest way to run the full stack locally. Requires only Docker.

### 1. Configure

```bash
cp cloud_app/BuildingDamageProtection/resources/config/config.example.json \
   cloud_app/BuildingDamageProtection/resources/config/config.json
```

For Docker, the Db2 connection is pre-configured. Only edit the fields you actually need (IoT, email, Slack):

```json
{
  "db_dbhost": "db2",
  "db_admin_user": "db2inst1",
  "db_admin_password": "bdppassword"
}
```

> The remaining DB fields are set to match the `docker-compose.yml` defaults above — **do not change them** unless you're running Db2 separately.

### 2. Start

```bash
cd cloud_app/BuildingDamageProtection
docker compose up
```

The first run downloads the IBM Db2 community image (~1 GB) and takes 3–5 minutes to initialize. Subsequent starts are fast. The `app` container waits for `db2` to pass its healthcheck before starting.

On startup, `bdp_sysinit.py` automatically creates all 7 tables if they don't exist.

```
bdp-db2  → localhost:50000   (IBM Db2)
bdp-app  → localhost:5001    (Flask API + Web UI)
```

### 3. Verify

```bash
curl http://localhost:5001/
# → {"Building Damage Protection": "alive", "ver": "1.0"}
```

### 4. Register a Tenant and Sensors

```bash
# Create a tenant (organization)
curl -u admin:change_me -X POST http://localhost:5001/tenant \
  -H "Content-Type: application/json" \
  -d '{"TENANT": "munich", "TENANT_NAME": "Munich IoT Center"}'

# Register sensors
curl -u admin:change_me -X POST http://localhost:5001/hardware \
  -H "Content-Type: application/json" \
  -d '{"HARDWARE_ID":"sensor-01","HARDWARE_TYPE":"waterLeakDetector","HARDWARE_DETAIL":"Server Room B2","TENANT":"munich"}'

curl -u admin:change_me -X POST http://localhost:5001/hardware \
  -H "Content-Type: application/json" \
  -d '{"HARDWARE_ID":"sensor-02","HARDWARE_TYPE":"waterLeakDetector","HARDWARE_DETAIL":"Basement Storage","TENANT":"munich"}'

curl -u admin:change_me -X POST http://localhost:5001/hardware \
  -H "Content-Type: application/json" \
  -d '{"HARDWARE_ID":"sensor-03","HARDWARE_TYPE":"waterSensorsDemo","HARDWARE_DETAIL":"Rooftop HVAC Unit","TENANT":"munich"}'
```

### 5. Open the Web Interface

| URL | Description |
|-----|-------------|
| `http://localhost:5001/dashboard` | Live sensor dashboard |
| `http://localhost:5001/map3d`     | Interactive 3D building map |

Login: `admin` / `change_me` (configurable via `gateway_user` / `gateway_password` in `config.json`).

### 6. Stop

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers + wipe DB volume
```

---

## Local Setup — Without Docker

### 1. Install Dependencies

```bash
cd cloud_app/BuildingDamageProtection
pip install -r requirements.txt
```

> `ibm_db` requires the IBM Db2 Client libraries. On macOS they are not available natively — use Docker instead, or deploy to a Linux environment.

### 2. Configure

```bash
cp resources/config/config.example.json resources/config/config.json
# Edit config.json — set db_dbhost, db_admin_user, db_admin_password to your Db2 instance
```

### 3. Run

```bash
# Development server
cd src/main/python
python gateway.py

# Production (Gunicorn)
cd cloud_app/BuildingDamageProtection
gunicorn -w 3 --pythonpath src/main/python --log-level debug gateway:application
```

### 4. Tests

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

# 2. Install MQTT and Blynk dependencies
pip install paho-mqtt blynk-library-python

# 3. Set credentials
cp sensors/pi/.env.example sensors/pi/.env
# Edit .env with your IOT_ORG, IOT_DEVICE_TYPE, IOT_DEVICE_ID, IOT_TOKEN, BLYNK_TOKEN

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

`.env` variables:

| Variable         | Description                                   |
|------------------|-----------------------------------------------|
| `IOT_ORG`        | IBM Watson IoT Platform organization ID       |
| `IOT_DEVICE_TYPE`| Device type registered in Watson IoT          |
| `IOT_DEVICE_ID`  | Unique device ID                              |
| `IOT_TOKEN`      | Device authentication token                   |
| `BLYNK_TOKEN`    | Blynk project token (optional)                |

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
3. Create `credentials.h` from the template:
   ```bash
   cp sensors/dhttemp/credentials.h.example sensors/dhttemp/credentials.h
   # Edit with your WiFi SSID/password, Blynk token, and IoT credentials
   ```
4. Select board (`NodeMCU 1.0` or `Wemos D1 Mini`) and upload

---

## Configuration Reference

Config file location: `cloud_app/BuildingDamageProtection/resources/config/config.json`

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
  "db_dbhost": "db2",
  "db_dbport": "50000",
  "db_admin_user": "db2inst1",
  "db_admin_password": "bdppassword",
  "iotplatform_options": {
    "org": "YOUR_IOT_ORG_ID",
    "id": "cloud-app",
    "auth-method": "apikey",
    "auth-key": "YOUR_API_KEY",
    "auth-token": "YOUR_AUTH_TOKEN"
  },
  "gmail_user": "your.email@gmail.com",
  "gmail_password": "your_app_password",
  "slack_auth": "xoxb-your-slack-bot-token",
  "tririga_api": "https://your-tririga-instance.com/api/",
  "tririga_user": "tririga_username",
  "tririga_password": "change_me",
  "alarm_interval_hr": "1",
  "snooze_hr": "2",
  "check_status_interval": "24"
}
```

| Parameter                | Description                                                            |
|--------------------------|------------------------------------------------------------------------|
| `server_type`            | `flask` (dev), `cli` (no HTTP), or any other value (Gevent WSGI + SSL) |
| `server_port`            | HTTP server port (mapped to 5001 externally in Docker)                 |
| `gateway_user/password`  | HTTP Basic Auth credentials for all API and UI endpoints               |
| `db_dbname`              | Db2 database name (default: `BLUDB`)                                   |
| `db_dbhost`              | Db2 hostname — use `db2` in Docker, `localhost` otherwise              |
| `db_dbport`              | Db2 TCP port (default: `50000`)                                        |
| `db_admin_user`          | Db2 username (default: `db2inst1`)                                     |
| `db_admin_password`      | Db2 password                                                           |
| `iotplatform_options`    | IBM Watson IoT Platform application credentials                        |
| `gmail_user/password`    | Gmail account used to send alert emails (use an App Password)          |
| `slack_auth`             | Slack bot token (`xoxb-...`) for Slack message delivery                |
| `tririga_*`              | IBM Tririga FM system API credentials (optional)                       |
| `alarm_interval_hr`      | Minimum interval between repeated alarms for the same incident (hours) |
| `snooze_hr`              | Duration of a SNOOZE action (hours)                                    |
| `check_status_interval`  | DB connection health check frequency (hours)                           |

---

## How It Works

```
1. Sensor detects humidity above threshold
        ↓
2. Publishes JSON reading via MQTT to IBM Watson IoT Platform
   Payload: {"humidity": 82.3, "temperature": 24.1}
        ↓
3. BDPIncident receives the event, stores it in BDP_RAW_EVENTS,
   and evaluates the urgency level
        ↓
4. Creates an incident record in BDP_INCIDENT (if not already active
   for this sensor + tenant combination)
        ↓
5. BDPNotifier identifies responsible users based on time of day
   (business hours: USER_TIMES=1, off-hours: USER_TIMES=2, always: USER_TIMES=3)
        ↓
6. Sends notifications via:
   ├── Email (Gmail SMTP) — contains a /respond?nid=<id> link
   ├── Slack message
   └── Tririga FM service request (optional)
        ↓
7. User opens the response link → views incident details, humidity
   chart, and current status
        ↓
8. User takes action:
   ├── SNOOZE → silences the alert for snooze_hr hours
   └── FIXED  → marks the incident as resolved (status = 1)
```

---

## REST Endpoints

All endpoints require **HTTP Basic Auth** (`gateway_user` / `gateway_password`).
Exception: `GET /` and `GET/POST /respond` are public.

| Method     | Endpoint                   | Description                                         |
|------------|----------------------------|-----------------------------------------------------|
| `GET`      | `/`                        | Health check — returns version and status           |
| `GET/POST` | `/respond`                 | Incident response web UI (linked from alert emails) |
| `GET`      | `/dashboard`               | Live sensor dashboard (web UI)                      |
| `GET`      | `/map3d`                   | Interactive 3D building map (web UI)                |
| `POST`     | `/tenant`                  | Register a tenant / organization                    |
| `POST`     | `/user`                    | Register a user with availability hours             |
| `POST`     | `/hardware`                | Register a sensor / detector                        |
| `GET`      | `/api/tenants`             | List all tenants                                    |
| `GET`      | `/api/hardware`            | List all sensors with latest reading + timestamp    |
| `GET`      | `/api/incidents`           | List last 100 incidents with sensor details         |
| `GET`      | `/api/events/<hardware_uid>` | Last 120 raw events for a specific sensor          |

---

## Security Notice

> **IMPORTANT:** Sensor source files previously contained hardcoded credentials (IoT tokens, Blynk tokens, WiFi passwords). These have been moved to environment variables and a gitignored `credentials.h` file. Before deploying:
>
> - Generate new tokens on IBM Watson IoT Platform
> - Generate a new Blynk token
> - Never commit `config.json` or `credentials.h` with real credentials
> - Change `gateway_password` in `config.json` before any public deployment

---

## Tech Stack

| Layer        | Technology                                                    |
|--------------|---------------------------------------------------------------|
| Sensor (Pi)  | Python 3, Adafruit DHT, paho-mqtt 1.6, BlynkLib              |
| Sensor (ESP) | C++/Arduino, PubSubClient, ESP8266WiFi, Blynk                 |
| Backend      | Python 3.11, Flask 3.0, Gevent 24.x, Flask-RESTful 0.3       |
| Database     | IBM Db2 (Community Edition via Docker)                        |
| IoT Platform | IBM Watson IoT Platform (MQTT)                                |
| Notifications| Gmail SMTP, Slack API, IBM Tririga                            |
| Web UI       | Vanilla JS, Chart.js 4, Three.js r158 (3D map)               |
| Deployment   | Docker + Docker Compose, IBM Cloud Foundry                    |

---

## Authors

- Rodrigo Brossi — IBM
- Angelo Danducci — IBM
- Hari Hara Prasad Viswanathan — IBM

Developed for the **IBM Munich Watson IoT Center** — 2018/2019.
Modernised and extended — 2026.
