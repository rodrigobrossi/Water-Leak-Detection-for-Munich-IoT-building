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

import bdp_dbutil, bdp_util
from bdp_notifier import BDPNotifier

class BDPIncident():

    def _checkForIncident(hardware):
        # Read all the values
        table = bdp_util.createHumidityTable(hardware["HARDWARE_UID"], 480)
       
        value_of_interest = table.HUMIDITY.iloc[-1]
        if value_of_interest < 10:
            return None

        # TODO: check the slope
        response = {}
        response['INCIDENT_DETAIL'] = hardware
        response['INCIDENT_DETAIL']['URGENCY'] = 'moderate' if value_of_interest < 75 else 'critical'
        response['INCIDENT_TIME'] = str(table.READING_TIME.iloc[-1])
        response['TENANT_ID'] = hardware['TENANT_ID']

        return response

    def handleRawEvents(hardware_uid):
        # Process the humidity values
        incident = BDPIncident._checkForIncident(hardware_uid)
        if incident is None:
            # No incident occured
            return
        # Post an incident
        response = BDPIncident._insertIncidentInDB(incident)

    def _insertIncidentInDB(new_incident):
        try:
            print('[BDPIncident] Incident received!')

            tenant = bdp_dbutil.getTenantByTenantID(new_incident['TENANT_ID'])
            if not tenant:
                print('[BDPIncident] Tenant {} is not found!'.format(new_incident['TENANT_ID']))
                return
            tenant_id = tenant['TENANT_ID']

            existing_incident = bdp_dbutil.checkExcistingIncident(tenant_id)
            new_incident_id = bdp_dbutil.insertIncident(existing_incident, new_incident, tenant_id)

            notification = {
                "ACTION": "ALARM",
                "OLD_INCIDENT": existing_incident,
                "NEW_INCIDENT_ID": new_incident_id
            }

            BDPNotifier.notify(notification, tenant_id)

        except Exception as e:
            print(e)
