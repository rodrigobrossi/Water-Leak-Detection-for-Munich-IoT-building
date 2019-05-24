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


class BDPNotifier():

    def notify(notification, tenant):
        print('[BDPNotifier] notify')
        if notification["ACTION"] == "ALARM":
            old_incident_record = notification["OLD_INCIDENT"]
            tenant_record = bdp_dbutil.getTenantByTenantID(tenant)

            users = BDPNotifier._timeToNotify(old_incident_record, tenant_record)

            if len(users) == 0:
                print('[BDPNotifier] No notification will be send out.')
                return

            bdp_dbutil.updateIncidentNotifyTime(notification["NEW_INCIDENT_ID"])
            bdp_dbutil.createNotificationRecord(notification["NEW_INCIDENT_ID"], 2, users)

            BDPNotifier._generateAlarmEmails(notification["NEW_INCIDENT_ID"], users)
            return

        elif notification["ACTION"] == "SNOOZE":
            now = datetime.datetime.now()
            response = {'TIME' : now, 'ACTION' : notification["ACTION"]}
            bdp_dbutil.updateNotificationResponse(notification["NOTIFICATION_ID"], response)
            
            retbool = bdp_dbutil.updateIncidentStatus(notification["INCIDENT_ID"], notification["ACTION"])
            if not retbool:
                print('Not able to update incident status')
                return
            
            users = bdp_dbutil.getAllUsers(tenant)
            bdp_dbutil.createNotificationRecord(notification["INCIDENT_ID"], 3, users)
            BDPNotifier._generateSnoozeEmails(notification, users)
            
        elif notification["ACTION"] == "FIXED":
            now = datetime.datetime.now()
            response = {'TIME' : now, 'ACTION' : notification["ACTION"]}
            bdp_dbutil.updateNotificationResponse(notification["NOTIFICATION_ID"], response)
            
            retbool = bdp_dbutil.updateIncidentStatus(notification["INCIDENT_ID"], notification["ACTION"])
            if not retbool:
                print('Not able to update incident status')
                return
            
            users = bdp_dbutil.getAllUsers(tenant)
            bdp_dbutil.createNotificationRecord(notification["INCIDENT_ID"], 1, users)
            BDPNotifier._generateFixedEmails(notification, users)
            return


    def _timeToNotify(incident_record, tenant_record):
        usergroups = []
        send = False

        if incident_record == False: 
            #no previous incident, send immediately
            print("[BDPNotifier]: No previous incident, send immediately")
            send = True
        else:
            #is it snoozed? if so, past the znoozed period yet? if past, needs to reset and send. otherwise, hibernate. 
            #if not snoozed, what was the last time sent out? past period yet?
            if incident_record["SNOOZE_TIME"] is None:
                lastsent = incident_record["NOTIFY_TIME"]
                if lastsent is None:
                    print("[BDPNotifier] No snooze, never sent before: SEND!")
                    send = True
                else:
                    interval = tenant_record["ALARM_INTERVAL_HR"] * 60
                    now = datetime.datetime.now()
                    diff = (now - lastsent).seconds/60
                    if diff > interval:
                        print("[BDPNotifier] No snooze, sent an hour ago: SEND!")
                        send = True
            else:
                lastsnooze = incident_record["SNOOZE_TIME"]
                interval = tenant_record["SNOOZE_HR"] * 60
                now = datetime.datetime.now()
                diff = (now - lastsnooze).seconds/60
                if diff > interval:
                    print("[BDPIncident] Snoozed, snoozed an hour ago: SEND!")
                    send = True
                    bdp_dbutil.snoozeFlip(incident_record, False)

        if send is True:
            usergroups = bdp_dbutil.getAllUsers(tenant_record["TENANT_ID"])
        return usergroups
    
    def _generateAlarmEmails(incident_id, users):
        subject = 'Water Intusion Detected!'

        print('[_generateAlarmEmails] to {}'.format(users))
        for user in users:
            incident = bdp_dbutil.getIncidentByIncidentID(incident_id)
            tenant = bdp_dbutil.getTenantByTenantID(incident['TENANT_ID'])['TENANT_NAME']
            incident_detail = json.loads(incident['INCIDENT_DETAIL'])
            urgency = incident_detail['URGENCY']
            hardware = bdp_dbutil.getHardwareByHardwareUID(incident_detail['HARDWARE_UID'])

            params = {
                'name': user['USER_NAME'], 
                'tenant': tenant,
                'sensor_id': hardware['HARDWARE_ID'],
                'location': hardware['HARDWARE_DETAIL'], 
                'urgency': urgency,
                'urgency_vis_1': 'visible',
                'urgency_vis_2': 'visible',
                'urgency_vis_3': 'visible' if urgency=='critical' else 'hidden',
                # TODO: Fix
                'link': 'http://0.0.0.0:8080/respond?nid=' + user['NOTIFICATION_ID']
            }
            print('[BDPNotifier] generating template with params {}'.format(params))
            current_dir = os.path.dirname(__file__)

            template_plain = open(os.path.join(current_dir, 'templates/alarm_email.txt')).read()
            template_html = open(os.path.join(current_dir, 'templates/alarm_email.html')).read()
            
            body_plain = pystache.render(template_plain, params)
            body_html = pystache.render(template_html, params)
            
            bdp_util.sendEmail(user['USER_CONTACT_1'], subject, body_plain, body_html)
    
    def _generateSnoozeEmails(notification, users):
        subject = 'Water Intrusion Notification Snoozed'
        
        print('[_generateSnoozeEmails] to {}'.format(users))
        for user in users:
            tenant = bdp_dbutil.getTenantByTenantID(notification['TENANT_ID'])
            params = {
                'name': user['USER_NAME'], 
                'handler': 'You have' if user['USER_NAME'] == notification["RESPONDER"] else notification["RESPONDER"],
                'snooze_time': tenant["SNOOZE_HR"],
                # TODO: Fix
                'link': 'http://0.0.0.0:8080/respond?nid=' + user['NOTIFICATION_ID']
            }
            print('[BDPNotifier] generating template with params {}'.format(params))
            current_dir = os.path.dirname(__file__)

            template_plain = open(os.path.join(current_dir, 'templates/snooze_email.txt')).read()
            template_html = open(os.path.join(current_dir, 'templates/snooze_email.html')).read()
            
            body_plain = pystache.render(template_plain, params)
            body_html = pystache.render(template_html, params)
            
            bdp_util.sendEmail(user['USER_CONTACT_1'], subject, body_plain, body_html)

    def _generateFixedEmails(notification, users):
        subject = 'Water Intrusion Incident Resolved'
        
        print('[_generateFixedEmails] to {}'.format(users))
        for user in users:
            params = {
                'name': user['USER_NAME'], 
                'handler': 'You have' if user['USER_NAME'] == notification["RESPONDER"] else notification["RESPONDER"],
                # TODO: Fix
                'link': 'http://0.0.0.0:8080/respond?nid=' + user['NOTIFICATION_ID']
            }
            print('[BDPNotifier] generating template with params {}'.format(params))
            current_dir = os.path.dirname(__file__)

            template_plain = open(os.path.join(current_dir, 'templates/fixed_email.txt')).read()
            template_html = open(os.path.join(current_dir, 'templates/fixed_email.html')).read()
            
            body_plain = pystache.render(template_plain, params)
            body_html = pystache.render(template_html, params)
            
            bdp_util.sendEmail(user['USER_CONTACT_1'], subject, body_plain, body_html)
        