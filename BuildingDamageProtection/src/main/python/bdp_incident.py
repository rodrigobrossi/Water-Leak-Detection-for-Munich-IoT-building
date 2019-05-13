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
import bdp_dbutil

class BDPIncident():

    def post(new_incident):
        try:
            conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()
            print('[BDPIncident] Incident received: {}'.format(new_incident))

            tenant = bdp_dbutil.getTenantByTenantID(conn, new_incident['TENANT_ID'])
            print('[BDPIncident] Tenant: {}'.format(tenant))
            if not tenant:
                print('[BDPIncident] Tenant {} is not found!'.format(new_incident['TENANT_ID']))
                return
            tenant_id = tenant['TENANT_ID']

            existing_incident = bdp_dbutil.checkExcistingIncident(conn, tenant_id)
            incident_id = BDPIncident.processIncident(conn, existing_incident, new_incident, tenant_id)

            users= BDPIncident.timeToNotify(conn, existing_incident, tenant)
            print('[BDPIncident] Users: {}'.format(users))
            
            notification = {}
            notification["GROUP"] = users
            notification["ACTION"] = "ALARM"

            bdp_dbutil.updateIncidentNotifyTime(conn, incident_id)
            bdp_dbutil.createNotificationRecord(conn, incident_id, users)

            return notification
        except Exception as e:
            print(e)
            return
    
    def timeToNotify(conn, incident_record, tenant_record):
        usergroups = []
        send = False

        if incident_record == False: 
            #no previous incident, send immediately
            print("[BDPIncident]: No previous incident, send immediately")
            send = True
        else:
            #needs to check all intervals
            print("[BDPIncident] Checking all intervals")
            #is it snoozed? if so, past the znoozed period yet? if past, needs to reset and send. otherwise, hibernate. 
            #if not snoozed, what was the last time sent out? past period yet?
            if incident_record["SNOOZE_TIME"] is None:
                lastsent = incident_record["NOTIFY_TIME"]
                if lastsent is None:
                    print("[BDPIncident] No snooze, never sent before: SEND!")
                    send = True
                else:
                    interval = tenant_record["ALARM_INTERVAL_HR"] * 60
                    now = datetime.datetime.now()
                    diff = (now - lastsent).seconds/60
                    if diff > interval:
                        print("[BDPIncident] No snooze, sent an hour ago: SEND!")
                        send = True
            else:
                lastsnooze = incident_record["SNOOZE_TIME"]
                interval = tenant_record["SNOOZE_HR"] * 60
                now = datetime.datetime.now()
                diff = (now - lastsnooze).seconds/60
                if diff > interval:
                    print("[BDPIncident] Snoozed, snoozed an hour ago: SEND!")
                    send = True
                    bdp_dbutil.snoozeFlip(conn, incident_record, False)

        if send is True:
            usergroups = bdp_dbutil.getAllUsers(conn, tenant_record["TENANT_ID"])
        return usergroups

    def processIncident(conn, existing_incident, new_incident, tenant_id):
        if not existing_incident:  
            #new incident
            sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_INCIDENT") 
            sql_string += " (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID) " 
            sql_string += "VALUES( '" + json.dumps(new_incident['INCIDENT_DETAIL']) + "', '" 
            sql_string += new_incident['INCIDENT_TIME'] + "', 2, '" + str(tenant_id) + "')"
            print('[BDPIncident] Inserting into DB: {}'.format(sql_string))
            
            stmt = ibm_db.exec_immediate(conn, sql_string)
            incident_id = bdp_dbutil.getIncidentID(conn, new_incident)
            print('[BDPIncident] New incident_id = {}'.format(new_incident))
        else: 
            #existing incident
            incident_id = str(existing_incident["INCIDENT_ID"])
            print('[BDPIncident] Existing incident_id = {}'.format(incident_id))

            sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_INCIDENT") 
            sql_string += " (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID, INCIDENT_ID_ORIGINAL) " 
            sql_string += "VALUES( '" + json.dumps(new_incident['INCIDENT_DETAIL']) + "', '" 
            sql_string += new_incident['INCIDENT_TIME'] + "', 2, '" + str(tenant_id) + "', " + incident_id + ")"

            print('[BDPIncident] Inserting into DB: {}'.format(sql_string))
            stmt = ibm_db.exec_immediate(conn, sql_string)
        
        if ibm_db.num_rows(stmt) == 0:
            print("[BDPIncident] Could not add the incident to DB!")
            return 
        
        return incident_id
