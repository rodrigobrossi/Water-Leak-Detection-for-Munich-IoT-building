#############################################################
# IBM Confidential
# OCO Source Materials
#
#  (C) Copyright IBM Corp. 2018
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has
# been deposited with the U.S. Copyright Office.
#############################################################
import os 
import sys
import pprint
import time
import datetime
from flask import Response
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask import request
from flask import json
import ibm_db
from bdp_dbutil import *


from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()


class BDPIncident(Resource):

    @auth.login_required
    def post(self):
        try:
            conn = getDBConnection()
            jsonbody = request.get_json(force=True)
            print(jsonbody)
            tenantjson = getTenantByName(conn, jsonbody['TENANT'])
            if tenantjson is None:
                content = {'result':'failed to create incident'}
            else:
                tenantid = tenantjson['TENANT_ID']
                sql_string = "SELECT * FROM " + getTableName("BDP_INCIDENT") + " WHERE INCIDENT_ID_ORIGINAL IS NULL AND TENANT_ID = " + str(tenantid) + " AND INCIDENT_STATUS_CODE != 1 ORDER BY INCIDENT_TIME DESC FETCH FIRST 1 ROWS ONLY"
                stmt = ibm_db.exec_immediate(conn, sql_string)
                incidentjson = ibm_db.fetch_both(stmt)
                incidentid = None
                if incidentjson != False:
                    print(incidentjson["INCIDENT_ID"])
                    incidentid = str(incidentjson["INCIDENT_ID"])
                
                if incidentid is None:  #new incident
                    sql_string = "INSERT INTO " + getTableName("BDP_INCIDENT") + " (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID) VALUES( '" + json.dumps(jsonbody['INCIDENT_DETAIL']) + "', '" + jsonbody['INCIDENT_TIME'] + "', 2, '" + str(tenantid) + "')"
                else: #existing incident
                    sql_string = "INSERT INTO " + getTableName("BDP_INCIDENT") + " (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID, INCIDENT_ID_ORIGINAL) VALUES( '" + json.dumps(jsonbody['INCIDENT_DETAIL']) + "', '" + jsonbody['INCIDENT_TIME'] + "', 2, '" + str(tenantid) + "', " + incidentid + ")"
                print(sql_string)
                stmt = ibm_db.exec_immediate(conn, sql_string)
                if ibm_db.num_rows(stmt) == 0:
                    content = {'result':'failed to create incident'}
                else:
                    content = {'incident':'created'}
                    print("new incident added, need to determine if notification is needed: ")
                    self.timeToNotify(incidentjson, tenantjson, conn)

            return content
        except Exception as e:
            print(e)
            return {"result":"failed to create incident", "msg": str(e)}, 400


    @auth.verify_password
    def verify(username, password):
        print("BDPIncident called")
        return authF.auth(username, password)
    
    def postValidation(self, jsonbody):
        print(jsonbody)
        return True
    
    def timeToNotify(self, incident_record, tenant_record, conn):
        send = False
        if incident_record == False: #no previous incident, send immediately
            print("no previous incident, send immediately")
            send = True
        else:#needs to check all intervals
            print(incident_record)
            print("#needs to check all intervals")
            #is it snoozed? if so, past the znoozed period yet? if past, needs to reset and send. otherwise, hibernate. 
            #if not snoozed, what was the last time sent out? past period yet?
            if incident_record["SNOOZE_TIME"] is None:
                print("#no snooze, needs to check last sent and period")
                lastsent = incident_record["NOTIFY_TIME"]
                if lastsent is None:
                    print("#never sent before, now")
                else:
                    interval = tenant_record["ALARM_INTERVAL_HR"] * 60
                    now = datetime.datetime.now()
                    print(lastsent)
                    print(now)
                    diff = (now - lastsent).seconds/60
                    print("diff: " + str(diff) + "/interval: " + str(interval))
                    if diff > interval:
                        send = True
        if send is True:
            print("strange true")
            print(tenant_record)
            getAllUsers(conn, tenant_record["TENANT_ID"])
        else:
            print("strange")
        return False
