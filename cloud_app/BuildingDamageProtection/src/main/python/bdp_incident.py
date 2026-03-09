#############################################################
# IBM Confidential
# OCO Source Materials
#
#  (C) Copyright IBM Corp. 2019
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has
# been deposited with the U.S. Copyright Office.
#############################################################
import datetime, json

import ibm_db
import paho.mqtt.client as mqtt

import bdp_dbutil, bdp_util

from bdp_property import BDPProperty
from bdp_notifier import BDPNotifier


class _IoTEvent:
    """Adapter that maps a raw paho MQTT message to the event structure used by _hardwareCallback."""
    def __init__(self, device_type, device_id, data):
        self.device = "{}:{}".format(device_type, device_id)
        self.data = data


class BDPIncident():
    """
    Class that checks for incident
    """
    def _checkForIncident(hardware):
        """
        Check if incident occured

        :param hardware_uid: Hardware ID
        :type hardware_uid: int

        :todo: particle swarm analytics

        :return: response JSON to insert into DB
        """
        # Read all the values
        table = bdp_dbutil.createHumidityTable(hardware["HARDWARE_UID"], 480)
        value_of_interest = table.HUMIDITY.iloc[-1]
        if value_of_interest < 50:
            return None

        response = {}

        response['INCIDENT_DETAIL'] = {}
        response['INCIDENT_DETAIL']['URGENCY'] = 'moderate' if value_of_interest < 75 else 'critical'
        response['INCIDENT_DETAIL']['HUMIDITY'] = value_of_interest

        response['INCIDENT_TIME'] = str(table.READING_TIME.iloc[-1])
        response['TENANT_ID'] = hardware['TENANT_ID']
        response['CAUSE_HARDWARE'] = hardware['HARDWARE_UID']

        return response

    def handleRawEvents(hardware_uid):
        """
        Check incoming events from device

        :param hardware_uid: Hardware ID
        :type hardware_uid: int
        """
        # Process the humidity values
        incident = BDPIncident._checkForIncident(hardware_uid)
        if incident is None:
            # No incident occured
            return
        # Post an incident
        notification = BDPIncident._insertIncidentInDB(incident)
        # Send notifications out
        BDPNotifier.notify(notification, incident['TENANT_ID'])

    def _insertIncidentInDB(new_incident):
        """
        Save incident info into DB

        :param new_incident: incident JSON to insert 
        :type new_incident: JSON

        :return: notification
        """
        try:
            print('[STATUS][BDPIncident] Incident identified')

            tenant = bdp_dbutil.getTenantByTenantID(new_incident['TENANT_ID'])
            if not tenant:
                print('[ERROR][BDPIncident] Tenant {} is not found!'.format(new_incident['TENANT_ID']))
                return
            tenant_id = tenant['TENANT_ID']

            existing_incident = bdp_dbutil.checkExcistingIncident(tenant_id, new_incident['CAUSE_HARDWARE'])
            new_incident_id = bdp_dbutil.insertIncident(existing_incident, new_incident, tenant_id)

            notification = {
                "ACTION": "ALARM",
                "OLD_INCIDENT": existing_incident,
                "NEW_INCIDENT_ID": new_incident_id
            }

            return notification

        except Exception as e:
            print(e)
    
    def _hardwareCallback(event):
        try:
            conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()

            # Generate timestamp and query hardware uid
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")

            hardware = bdp_dbutil.getHardwareByDevice(event.device)
            if not hardware:
                print("[ERROR][BDPIncident.hardwareCallback] Device {} not found.".format(event.device))
                return
            hardware_uid = hardware["HARDWARE_UID"]

            # Generate SQL string
            sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_RAW_EVENTS") + "(READING_TIME, READING, HARDWARE_UID) VALUES ('" 
            sql_string += str(timestamp) + "', '" + json.dumps(event.data) + "', '" + str(hardware_uid)  + "')"
            
            # Save to DB
            stmt = ibm_db.exec_immediate(conn, sql_string)
            if ibm_db.num_rows(stmt) == 0:
                print("[ERROR][BDPIncident.hardwareCallback] Could not add the event to DB!")
                return

            # Remove old points
            week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d-%H.%M.%S")
            sql_string = "DELETE FROM " + bdp_dbutil.getTableName("BDP_RAW_EVENTS") + " WHERE date(READING_TIME) < date('" + str(week_ago) +"')"
            stmt = ibm_db.exec_immediate(conn, sql_string)

            # Process event
            BDPIncident.handleRawEvents(hardware)
            
        except Exception as e:
            print(e)

    def start():
        """
        Starts the application
        """
        BDPIncident._iotSubscribe()

    def _iotSubscribe():
        """
        Subscribe to devices from IBM Watson IoT Platform via paho-mqtt.
        Topic format: iot-2/type/{deviceType}/id/{deviceId}/evt/{eventType}/fmt/{format}
        """
        try:
            props      = BDPProperty.getInstance().getValue('iotplatform_options')
            org        = props['org']
            app_id     = props.get('id', 'cloud-app')
            auth_key   = props['auth-key']
            auth_token = props['auth-token']

            broker    = "{}.messaging.internetofthings.ibmcloud.com".format(org)
            client_id = "a:{}:{}".format(org, app_id)

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    client.subscribe("iot-2/type/waterLeakDetector/id/+/evt/+/fmt/json")
                    client.subscribe("iot-2/type/waterSensorsDemo/id/+/evt/+/fmt/json")
                    print("[STATUS][BDPIncident] Connected to IoT Platform and subscribed.")
                else:
                    print("[ERROR][BDPIncident] MQTT connection failed with code {}".format(rc))

            def on_message(client, userdata, msg):
                try:
                    # iot-2/type/{deviceType}/id/{deviceId}/evt/{eventType}/fmt/{format}
                    parts = msg.topic.split('/')
                    device_type = parts[2]
                    device_id   = parts[4]
                    data = json.loads(msg.payload.decode('utf-8'))
                    event = _IoTEvent(device_type, device_id, data)
                    BDPIncident._hardwareCallback(event)
                except Exception as e:
                    print("[ERROR][BDPIncident.on_message] {}".format(e))

            client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
            client.username_pw_set(auth_key, auth_token)
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect(broker, 1883, keepalive=60)
            client.loop_start()

        except Exception as e:
            print("[ERROR][BDPIncident._iotSubscribe] {}".format(e))