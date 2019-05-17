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
        table = bdp_util.createHumidityTable(conn, hardware["HARDWARE_UID"], 480)
       
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
        BDPNotifier.generateAlarmNotifications(conn, incident)
    
    def generateAlarmNotifications(conn, incident):
        if incident['ACTION'] == 'ALARM':
            subject = 'Water Intusion Detected!'
        else:
            return
        
        tenant = bdp_dbutil.getTenantByTenantID(conn, incident['TENANT_ID'])['TENANT_NAME']
        urgency = incident['INCIDENT_DETAIL']['URGENCY']
        
        params = {
            'name': incident['GROUP'][0]['USER_NAME'], 
            'tenant': tenant,
            'sensor_id': incident['INCIDENT_DETAIL']['HARDWARE_ID'],
            'location': incident['INCIDENT_DETAIL']['HARDWARE_DETAIL'], 
            'urgency': urgency,
            'urgency_vis_1': 'visible',
            'urgency_vis_2': 'visible',
            'urgency_vis_3': 'visible' if urgency=='critical' else 'hidden',
            # TODO: Fix
            'link': 'http://0.0.0.0:8080/respond?nid=' + incident['GROUP'][0]['NOTIFICATION_ID']
        }
        print('[BDPNotifier] generating template with params {}'.format(params))
        current_dir = os.path.dirname(__file__)

        template_plain = open(os.path.join(current_dir, 'templates/alarm_email.txt')).read()
        template_html = open(os.path.join(current_dir, 'templates/alarm_email.html')).read()
        
        body_plain = pystache.render(template_plain, params)
        body_html = pystache.render(template_html, params)
        
        bdp_util.sendEmail('alona.sakhnenko@ibm.com', subject, body_plain, body_html)
    
    def generateSmoozeNotifications(conn, nid):
        if incident['ACTION'] == 'ALARM':
            subject = 'Water Intusion Detected!'
        
        tenant = bdp_dbutil.getTenantByTenantID(conn, incident['TENANT_ID'])['TENANT_NAME']
        urgency = incident['INCIDENT_DETAIL']['URGENCY']
        
        params = {
            'name': incident['GROUP'][0]['USER_NAME'], 
            'tenant': tenant,
            'sensor_id': incident['INCIDENT_DETAIL']['HARDWARE_ID'],
            'location': incident['INCIDENT_DETAIL']['HARDWARE_DETAIL'], 
            'urgency': urgency,
            'urgency_vis_1': 'visible',
            'urgency_vis_2': 'visible',
            'urgency_vis_3': 'visible' if urgency=='critical' else 'hidden',
            # TODO: Fix
            'link': 'http://0.0.0.0:8080/respond?nid=' + incident['GROUP'][0]['NOTIFICATION_ID']
        }
        print('[BDPNotifier] generating template with params {}'.format(params))
        current_dir = os.path.dirname(__file__)

        template_plain = open(os.path.join(current_dir, 'templates/alarm_email.txt')).read()
        template_html = open(os.path.join(current_dir, 'templates/alarm_email.html')).read()
        
        body_plain = pystache.render(template_plain, params)
        body_html = pystache.render(template_html, params)
        
        bdp_util.sendEmail('alona.sakhnenko@ibm.com', subject, body_plain, body_html)
        