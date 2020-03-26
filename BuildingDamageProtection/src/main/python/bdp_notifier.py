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
import os, datetime, socket
import json, pystache
import pandas as pd

from threading import Thread

import ibm_db

import bdp_dbutil, bdp_util
from bdp_property import BDPProperty
from bdp_email import BDPEmail
from bdp_tririga_worktask import BDPWorktask

class BDPNotifier():
    """ 
    Class that handles notifications
    """
    def notify(notification, tenant):
        """ 
        Notifies all user about an event

        :param notification: JSON constaining action type 
        :type notification: JSON
        :param tenant: Tenant ID
        :type tenant: int
        """

        # TODO: try except block
        if notification["ACTION"] == "ALARM":
            # Incident notification
            old_incident_record = notification["OLD_INCIDENT"]
            tenant_record = bdp_dbutil.getTenantByTenantID(tenant)

            users = BDPNotifier._timeToNotify(old_incident_record, tenant_record)

            if len(users) == 0:
                print('[STATUS][BDPNotifier] No notification will be send out.')
                return
            print(users)
            bdp_dbutil.updateIncidentNotifyTime(notification["NEW_INCIDENT_ID"])
            bdp_dbutil.createNotificationRecord(notification["NEW_INCIDENT_ID"], 2, users)

            BDPNotifier._generateAlarm(notification["NEW_INCIDENT_ID"], users)
            BDPNotifier._generateTririgaWorkTaks(notification["NEW_INCIDENT_ID"])

            return

        elif notification["ACTION"] == "SNOOZE":
            # Snoozing notification
            now = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            response = {'TIME' : now, 'ACTION' : notification["ACTION"]}
            bdp_dbutil.updateNotificationResponse(notification["NOTIFICATION_ID"], response)

            retbool = bdp_dbutil.updateIncidentStatus(notification["INCIDENT_ID"], notification["ACTION"])
            if not retbool:
                print('[ERROR][BDPNotifier] Not able to update incident status')
                return

            users = bdp_dbutil.getUsersWithNIDs(tenant)
            bdp_dbutil.createNotificationRecord(notification["INCIDENT_ID"], 3, users)
            BDPNotifier._generateSnooze(notification, users)
            
        elif notification["ACTION"] == "FIXED":
            # Incident is resolved notification
            now = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            response = {'TIME' : now, 'ACTION' : notification["ACTION"]}
            bdp_dbutil.updateNotificationResponse(notification["NOTIFICATION_ID"], response)
            
            retbool = bdp_dbutil.updateIncidentStatus(notification["INCIDENT_ID"], notification["ACTION"])
            if not retbool:
                print('[ERROR][BDPNotifier] Not able to update incident status')
                return
            
            users = bdp_dbutil.getUsersWithNIDs(tenant)
            bdp_dbutil.createNotificationRecord(notification["INCIDENT_ID"], 1, users)
            BDPNotifier._generateFixed(notification, users)
            return


    def _timeToNotify(incident_record, tenant_record):
        """
        Check if it is time to notify based on existing notification stamp and incident status
        
        :param incident_record: incident information
        :type incident_record: json
        :param tenant_record: tenant information
        :type tenant_record: json

        :return: list of users if it is time to notify else empty list
        """
        usergroups = []
        send = False

        if incident_record == False: 
            #no previous incident, send immediately
            print("[STATUS][BDPNotifier]: No previous incident, send immediately")
            send = True
        else:
            #is it snoozed? if so, past the snoozed period yet? if past, needs to reset and send. otherwise, hibernate. 
            #if not snoozed, what was the last time sent out? past period yet?
            if incident_record["SNOOZE_TIME"] is None:
                lastsent = incident_record["NOTIFY_TIME"]
                if lastsent is None:
                    print("[STATUS][BDPNotifier] No snooze, never sent before -> sending alarm")
                    send = True
                else:
                    interval = tenant_record["ALARM_INTERVAL_HR"] * 60
                    now = datetime.datetime.now()
                    diff = (now - lastsent).total_seconds() / 60
                    if diff > interval:
                        print("[STATUS][BDPNotifier] No snooze -> sending alarm")
                        send = True
            else:
                lastsnooze = incident_record["SNOOZE_TIME"]
                interval = tenant_record["SNOOZE_HR"] * 60
                now = datetime.datetime.now()
                diff = (now - lastsnooze).total_seconds() / 60
                if diff > interval:
                    print("[STATUS][BDPIncident] No snooze -> sending alarm")
                    send = True
                    bdp_dbutil.snoozeFlip(incident_record["INCIDENT_ID"], False)
                    
        if send is True:
            usergroups = bdp_dbutil.getUsersWithNIDs(tenant_record["TENANT_ID"])

        return usergroups
    
    def _generateAlarm(incident_id, users):
        """
        Generate alarm template and send it out
        """
        subject = 'Water Intusion Detected'

        for user in users:
            incident = bdp_dbutil.getIncidentByIncidentID(incident_id)
            tenant = bdp_dbutil.getTenantByTenantID(incident['TENANT_ID'])['TENANT_NAME']
            incident_detail = json.loads(incident['INCIDENT_DETAIL'])
            urgency = incident_detail['URGENCY']
            hardware = bdp_dbutil.getHardwareByHardwareUID(incident['CAUSE_HARDWARE'])

            params = {
                'name': user['USER_NAME'], 
                'tenant': tenant,
                'sensor_id': hardware['HARDWARE_ID'],
                'location': hardware['HARDWARE_DETAIL'], 
                'urgency': urgency,
                'urgency_vis_1': 'visible',
                'urgency_vis_2': 'visible',
                'urgency_vis_3': 'visible' if urgency=='critical' else 'hidden',
                'link': 'https://bdp.eu-de.mybluemix.net/respond?nid=' + user['NOTIFICATION_ID']
            }

            current_dir = os.path.dirname(__file__)

            template_plain = open(os.path.join(current_dir, 'templates/alarm_email.txt')).read()
            template_html = open(os.path.join(current_dir, 'templates/alarm_email.html')).read()
            
            body_plain = pystache.render(template_plain, params)
            body_html = pystache.render(template_html, params)
            
            bdp_util.sendEmail(user['USER_CONTACT_1'], subject, body_plain, body_html)
            bdp_util.sendSlack(user['USER_CONTACT_2'], body_plain)

    def _sendEmails(emailList):
        bdp_util.sendEmails(emailList)

    def _generateSnooze(notification, users):
        """
        Generate snooze alarm template and send it out
        """
        subject = 'Water Intrusion Notification Snoozed'
        
        emailList = []
        tenant = bdp_dbutil.getTenantByTenantID(notification['TENANT_ID'])
        
        current_dir = os.path.dirname(__file__)

        template_plain = open(os.path.join(current_dir, 'templates/snooze_email.txt')).read()
        template_html = open(os.path.join(current_dir, 'templates/snooze_email.html')).read()

        for user in users:
            params = {
                'name': user['USER_NAME'], 
                'handler': 'You have' if user['USER_NAME'] == notification["RESPONDER"] else notification["RESPONDER"],
                'snooze_time': tenant["SNOOZE_HR"],
                'link': 'https://bdp.eu-de.mybluemix.net/respond?nid=' + user['NOTIFICATION_ID']
            }
            
            body_plain = pystache.render(template_plain, params)
            body_html = pystache.render(template_html, params)

            email = BDPEmail(user['USER_CONTACT_1'], subject, body_html, body_plain)
            emailList.append(email)

            bdp_util.sendSlack(user['USER_CONTACT_2'], body_plain)

        BDPNotifier._startEmailThread(emailList)

    def _generateFixed(notification, users):
        """
        Generate fixed template and send it out
        """
        subject = 'Water Intrusion Incident Resolved'

        emailList = []

        current_dir = os.path.dirname(__file__)

        template_plain = open(os.path.join(current_dir, 'templates/fixed_email.txt')).read()
        template_html = open(os.path.join(current_dir, 'templates/fixed_email.html')).read()
        
        for user in users:
            params = {
                'name': user['USER_NAME'], 
                'handler': 'You have' if user['USER_NAME'] == notification["RESPONDER"] else notification["RESPONDER"],
                'link': 'https://bdp.eu-de.mybluemix.net/respond?nid=' + user['NOTIFICATION_ID']
            }
            
            body_plain = pystache.render(template_plain, params)
            body_html = pystache.render(template_html, params)

            email = BDPEmail(user['USER_CONTACT_1'], subject, body_html, body_plain)
            emailList.append(email)
            
            bdp_util.sendSlack(user['USER_CONTACT_2'], body_plain)

        BDPNotifier._startEmailThread(emailList)

    def _startEmailThread(emailList):
        emailThread = Thread(target = BDPNotifier._sendEmails, args = (emailList,))
        emailThread.start()

    def _generateTririgaWorkTaks(incident_id):

        incident = bdp_dbutil.getIncidentByIncidentID(incident_id)
        tenant = bdp_dbutil.getTenantByTenantID(incident['TENANT_ID'])['TENANT_NAME']
        incident_detail = json.loads(incident['INCIDENT_DETAIL'])
        urgency = 'Emergency' if incident_detail['URGENCY'] == 'critical' else 'High' 
        hardware = bdp_dbutil.getHardwareByHardwareUID(incident['CAUSE_HARDWARE'])
        link = 'https://bdp.eu-de.mybluemix.net/respond?nid='

        #tririgaPayload = BDPWorktask(urgency, hardware['HARDWARE_ID'], hardware['HARDWARE_DETAIL'], incident_detail['HUMIDITY'] , link)
        tririgaPayload = {}
        tririgaPayload['spi:action'] = 'Submit'
        tririgaPayload['spi:triRequestClassCL'] = 'Humidity'
        tririgaPayload['spi:triEmergencyBL'] = 'true' if urgency == 'Emergency' else 'false'  
        tririgaPayload['spi:triDescriptionTX'] = 'Water has been detected! \n Urgency: ' + urgency + '\n Sensor ID: ' + str(hardware['HARDWARE_ID']) + '\n Location: ' + str(hardware['HARDWARE_DETAIL']) + '\n Humidity level: ' + str(incident_detail['HUMIDITY']) + '\n See the link for more information: ' + link
        tririgaPayload['spi:triBuildingTX'] = 'Munich Watson Center'
        tririgaPayload['spi:triCustomerOrgTX'] = '\\Organizations\\IBM Watson IoT Center GmbH'
        tririgaPayload['spi:triLocationRequestedTX'] = '\\Locations\\Offices\\Europe\\Munich Watson Center'
        payload = json.dumps(tririgaPayload)
        
        return bdp_util.sendTririga(payload)
        