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
import os, datetime
import json, pystache
import pandas as pd
import ibm_db

import bdp_dbutil, bdp_util
from bdp_property import BDPProperty
from bdp_incident import BDPIncident


class BDPNotifier():
    
    def getIncidentOccurence(conn, hardware):
        # Read all the values
        table = pd.DataFrame(bdp_dbutil.getRawEventsByHardwareUID(conn, hardware["HARDWARE_UID"]))
        # TODO: Find a better way
        # Consider only the last 2 h

        table = table.tail(4)
        table.reset_index(drop=True, inplace=True)
        print('[BDPNotifier] Table \n {}'.format(table))
        table.sort_values(by=['READING_TIME'],inplace=True)

        # Get important values
        table['HUMIDITY'] = None
        for i in range(table.shape[0]):
            hardware_json = json.loads(table.READING.iloc[i])
            table.at[i, 'HUMIDITY']  = hardware_json['humidity']
       
        value_of_interest = table.HUMIDITY.iloc[-1]
        if value_of_interest < 10:
            return None

        # TODO: check the slope
        response = {}
        response['INCIDENT_DETAIL'] = hardware
        response['INCIDENT_DETAIL']['URGENCY'] = 'moderate' if value_of_interest < 75 else 'critical'
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
        if len(response['GROUP']) == 0:
            print('[BDPNotifier] No notification will be send out.')
            return
        incident['GROUP'] = response['GROUP']
        incident['ACTION'] = response['ACTION']
        BDPNotifier.generateNotifications(incident)
    
    def generateNotifications(incident):
        if incident['ACTION'] == 'ALARM':
            subject = 'Water Intusion Detected!'
        
        print('GENERATING TEMPLATE')
        params = {
            'name': incident['GROUP'][0]['USER_NAME'], 
            'location': incident['INCIDENT_DETAIL']['URGENCY'], 
            'urgency': incident['INCIDENT_DETAIL']['URGENCY'],
            'link': 'http://0.0.0.0:8080/respond?nid=' + incident['GROUP'][0]['NOTIFICATION_ID']
        }

        current_dir = os.path.dirname(__file__)

        template_plain = open(os.path.join(current_dir, 'templates/alarm_email.txt')).read()
        template_html = open(os.path.join(current_dir, 'templates/alarm_email.html')).read()
        
        body_plain = pystache.render(template_plain, params)
        body_html = pystache.render(template_html, params)
        
        bdp_util.sendEmail('alona.sakhnenko@ibm.com', subject, body_plain, body_html)
        