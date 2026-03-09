# Project Memory — Water Leak Detection Munich IoT

## Project Overview
IoT water leak detection system for IBM Munich Watson IoT Center (2018/2019).
- Sensors → IBM Watson IoT Platform (MQTT) → Flask backend → IBM Db2 → notifications

## Key Architecture
- **Sensors**: Raspberry Pi (`sensors/pi/humidity.py`) + ESP8266 (`sensors/dhttemp/dhttemp.ino`)
- **Backend**: Flask + Gevent in `cloud_app/BuildingDamageProtection/src/main/python/`
- **Entry point**: `gateway.py`
- **Config**: `resources/config/config.json` (singleton via `bdp_property.py`)

## Critical Setup Issue (Fixed)
- `resources/config/` directory did NOT exist → created it + added `config.example.json`
- `config.json` was not in `.gitignore` → added it

## Config File Path
`cloud_app/BuildingDamageProtection/resources/config/config.json`
Relative to `gateway.py`: `../../../resources/config/config.json`

## Humidity Thresholds
- < 50% → no incident
- 50–75% → MODERATE
- > 75% → CRITICAL

## Tech Stack
- Python 3.6, Flask 1.0.2, Gevent, ibmiotf 0.4.0, ibm_db 3.0.1
- IBM Db2, IBM Watson IoT Platform, Gmail SMTP, Slack, Tririga

## Known Issues / Suggestions
- Hardcoded credentials in sensor files (tokens, WiFi passwords)
- `ibmiotf` library is deprecated → migrate to `paho-mqtt`
- Python 3.6 is EOL → upgrade to 3.11+
- No docker-compose for local Db2 setup
