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
import pandas as pd
import ibm_db

import bdp_dbutil
from bdp_property import BDPProperty
from bdp_incident import BDPIncident

class BDPNotifier():
    
    def getIncidentOccurence(conn, hardware):
        # Read all the values
        table = pd.DataFrame(bdp_dbutil.getRawEventsByHardwareUID(conn, hardware["HARDWARE_UID"]))
        # TODO: Find a better way
        # Consider only the last 2 h

        table = table.tail(4 * 120)
        table.reset_index(drop=True, inplace=True)
        table.sort_values(by=['READING_TIME'],minplace=True)

        # Get important values
        table['HUMIDITY'] = None
        for i in range(table.shape[0]):
            hardware_json = json.loads(table.READING.iloc[i])
            table.at[i, 'HUMIDITY']  = hardware_json['humidity']
       
        value_of_interest = table.HUMIDITY.iloc[-1]
        if value_of_interest < 20:
            return None

        # TODO: check the slope
        response = {}
        response['INCIDENT_DETAIL'] = hardware
        response['INCIDENT_DETAIL']['URGENCY'] = 'MODERATE' if value_of_interest < 75 else 'CRITICAL'
        response['INCIDENT_TIME'] = str(table.READING_TIME.iloc[-1])
        response['TENANT_ID'] = hardware['TENANT_ID']

        print('[BDPNotifier] response: {}'.format(response))
        return response
        
    def handleEvents(conn, hardware_uid):
        # Process the humidity values
        incident = BDPNotifier.getIncidentOccurence(conn, hardware_uid)
        if incident is None:
            # No incident occured
            return
        # Post an incident
        response = BDPIncident.post(incident)
        print('[BDPNotifier] incident response: {}'.format(response))
        