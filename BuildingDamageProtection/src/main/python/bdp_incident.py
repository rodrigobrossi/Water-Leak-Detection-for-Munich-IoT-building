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

import ibm_db, ibmiotf

import bdp_dbutil, bdp_util
from bdp_notifier import BDPNotifier

class BDPIncident():
    """
    Class that checks for incident
    """
    def _checkForIncident(hardware):
        """
        Check if incident occured

        :param hardware_uid: Hardware ID
        :type hardware_uid: int

        :todo: check rate of change and change urgency accordingly
        :todo: make sure that anomaly persists before marking as incident
        :todo: account for multiple sensors at once

        :return: response JSON to insert into DB
        """
        # Read all the values
        table = bdp_dbutil.createHumidityTable(hardware["HARDWARE_UID"], 480)
       
        value_of_interest = table.HUMIDITY.iloc[-1]
        if value_of_interest < 50:
            return None

        # TODO: check the slope
        # TODO: make sure that anomaly persists
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
            print('[BDPIncident] Incident received!')

            tenant = bdp_dbutil.getTenantByTenantID(new_incident['TENANT_ID'])
            if not tenant:
                print('[BDPIncident] Tenant {} is not found!'.format(new_incident['TENANT_ID']))
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
                print("[hardwareCallback] Device {} not found.".format(event.device))
                return
            hardware_uid = hardware["HARDWARE_UID"]

            # Generate SQL string
            sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_RAW_EVENTS") + "(READING_TIME, READING, HARDWARE_UID) VALUES ('" 
            sql_string += str(timestamp) + "', '" + json.dumps(event.data) + "', '" + str(hardware_uid)  + "')"
            
            # Save to DB
            stmt = ibm_db.exec_immediate(conn, sql_string)
            if ibm_db.num_rows(stmt) == 0:
                print("[hardwareCallback] Could not add the event to DB!")
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
        BDPIncident._iotSubscribe()

    def _iotSubscribe():
        try:
            myDeviceType="waterLeakDetector"
            options = {
                "org": "h9eyui",
                "id": "orgfx53ykk",
                "auth-method": "apikey",
                "auth-key": "a-h9eyui-orgfx53ykk",
                "auth-token": "rGXJy+2xk1FbSzCR&-",
                "type": "shared",
                "clean-session": True
            }
            client = ibmiotf.application.Client(options)
            client.connect()
            client.deviceEventCallback = BDPIncident._hardwareCallback
            client.subscribeToDeviceEvents(deviceType=myDeviceType)
        except ibmiotf.ConnectionException  as e:
            print(e)