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
import datetime
from flask import json

import ibm_db

from bdp_property import BDPProperty
from bdp_util import *


class BDPDBConnection():
    __instance = None

    @staticmethod
    def getInstance():
        if BDPDBConnection.__instance == None:
            BDPDBConnection()
        return BDPDBConnection.__instance 

    def __init__(self):
        if BDPDBConnection.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            BDPDBConnection.__instance = self
            conn_string = "DATABASE=" + BDPProperty.getInstance().getValue('db_dbname')
            conn_string = conn_string + ";HOSTNAME=" + BDPProperty.getInstance().getValue('db_dbhost')
            conn_string = conn_string + ";PORT=" + BDPProperty.getInstance().getValue('db_dbport')
            conn_string = conn_string + ";PROTOCOL=TCPIP;UID=" + BDPProperty.getInstance().getValue('db_admin_user')
            conn_string = conn_string + ";PWD=" + BDPProperty.getInstance().getValue('db_admin_password')
            print(conn_string)
            self.conn = ibm_db.pconnect(conn_string, "", "") 
            
    def getDBConnection(self, enforce = False):
        if enforce:
            conn_string = "DATABASE=" + BDPProperty.getInstance().getValue('db_dbname')
            conn_string = conn_string + ";HOSTNAME=" + BDPProperty.getInstance().getValue('db_dbhost')
            conn_string = conn_string + ";PORT=" + BDPProperty.getInstance().getValue('db_dbport')
            conn_string = conn_string + ";PROTOCOL=TCPIP;UID=" + BDPProperty.getInstance().getValue('db_admin_user')
            conn_string = conn_string + ";PWD=" + BDPProperty.getInstance().getValue('db_admin_password')
            self.conn = ibm_db.pconnect(conn_string, "", "") 
        else:
            return self.conn
    
def getTableName(tablename):
    return BDPProperty.getInstance().getValue('db_admin_user') + "." + tablename

def getTenantByName(tenant):
    conn = BDPDBConnection.getInstance().getDBConnection()
    sql_string = "SELECT * FROM " + getTableName("BDP_TENANT") + " WHERE TENANT = '" + tenant + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)
    return ibm_db.fetch_both(stmt)

def getTenantByTenantID(tenant_id):
    conn = BDPDBConnection.getInstance().getDBConnection()

    sql_string = "SELECT * FROM " + getTableName("BDP_TENANT") + " WHERE TENANT_ID = '" + str(tenant_id) + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)
    return ibm_db.fetch_both(stmt)

def getUsersWithNIDsAtTimes(tenant_id, times):
    conn = BDPDBConnection.getInstance().getDBConnection()
    usergroups = []
    if tenant_id < 0:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER")
    else:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER") + " WHERE TENANT_ID = " + str(tenant_id) + " AND USER_TIMES = " + str(times)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        dictionary["NOTIFICATION_ID"] = randomString()
        usergroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return usergroups

def getUsersWithNIDs(tenant_id):
    usergroups = getUsersWithNIDsAtTimes(tenant_id, 3)
    
    timestamp = datetime.datetime.now()
    if timestamp.weekday() > 4 or timestamp.hour < 8 or timestamp.hour > 18:
        usergroups.extend(getUsersWithNIDsAtTimes(tenant_id, 2))
    else:
        usergroups.extend(getUsersWithNIDsAtTimes(tenant_id, 1))

    return usergroups

def snoozeFlip(incident_record, state):
    conn = BDPDBConnection.getInstance().getDBConnection()

    if state is True:
        #set snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET SNOOZE_TIME = '" + str(datetime.datetime.now()) + "' WHERE INCIDENT_ID = " + str(incident_record["INCIDENT_ID"])
    else:
        #turn of snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET SNOOZE_TIME = null WHERE INCIDENT_ID = " + str(incident_record["INCIDENT_ID"])
    stmt = ibm_db.exec_immediate(conn, sql_string)

def updateIncidentNotifyTime(incidentid):
    conn = BDPDBConnection.getInstance().getDBConnection()

    print("[updateIncidentNotifyTime] incident_id = {}".format(incidentid))
    sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET NOTIFY_TIME = '" + str(datetime.datetime.now()) + "' WHERE INCIDENT_ID = " + str(incidentid)
    stmt = ibm_db.exec_immediate(conn, sql_string)

def createNotificationRecord(incidentid, type_code, usergroups):
    conn = BDPDBConnection.getInstance().getDBConnection()

    now = str(datetime.datetime.now())
    notification_uids = []
    for user in usergroups:
        notificationid = user["NOTIFICATION_ID"]
        userid = str(user["USER_ID"])
        sql_string = "INSERT INTO " + getTableName("BDP_NOTIFICATION") + " (NOTIFICATION_ID, INCIDENT_ID, NOTIFICATION_TYPE, NOTIFICATION_TIME, USER_ID) VALUES( '" 
        sql_string += notificationid + "', '" + str(incidentid) + "', "+ str(type_code)+", '" + now + "', " + userid + ")"
        stmt = ibm_db.exec_immediate(conn, sql_string)

def getNotificationsByIncidentID(incidentid): #not tested yet
    conn = BDPDBConnection.getInstance().getDBConnection()
    notificationgroups = []
    sql_string = "SELECT * FROM " + getTableName("BDP_NOTIFICATION") + " WHERE INCIDENT_ID = '"  + str(incidentid) + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        notificationgroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return notificationgroups

def getNotificationByNotificationID(nid): #not tested yet
    conn = BDPDBConnection.getInstance().getDBConnection()
    notificationgroups = []
    sql_string = "SELECT * FROM " + getTableName("BDP_NOTIFICATION") + " WHERE NOTIFICATION_ID = '"  + str(nid) + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getUserByUserID(user_id):
    conn = BDPDBConnection.getInstance().getDBConnection()
    print("getUserByUserID: " + str(user_id))
    sql_string = "SELECT * FROM " + getTableName("BDP_USER") + " WHERE USER_ID = " + str(user_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getIncidentID(incident):
    conn = BDPDBConnection.getInstance().getDBConnection()
    
    sql_string = "SELECT * FROM " + getTableName("BDP_INCIDENT") 
    sql_string += " WHERE INCIDENT_DETAIL = '" + json.dumps(incident['INCIDENT_DETAIL']) 
    sql_string += "' AND INCIDENT_TIME = '" + incident['INCIDENT_TIME'] 
    sql_string += "' AND INCIDENT_STATUS_CODE = 2 AND TENANT_ID = '" + str(incident['TENANT_ID']) 
    sql_string += "' ORDER BY INCIDENT_ID DESC"
    
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary['INCIDENT_ID']

def getIncidentByIncidentID(incident_id):
    conn = BDPDBConnection.getInstance().getDBConnection()

    sql_string = "SELECT * FROM " + getTableName("BDP_INCIDENT") + " WHERE INCIDENT_ID = " + str(incident_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def checkExcistingIncident(tenant_id, hardware_uid):
    """
    Check whether an incident was already created

    :param tenant_id: Tenant ID
    :type tenant_id: int 
    :param hardware_uid: Hardware unique ID
    :type hardware_uid: int 

    :return: dictionary if found else False
    """
    conn = BDPDBConnection.getInstance().getDBConnection()
    
    sql_string = "SELECT * FROM " + getTableName("BDP_INCIDENT") 
    sql_string += " WHERE INCIDENT_ID_ORIGINAL IS NULL AND TENANT_ID = " + str(tenant_id) 
    sql_string += " AND CAUSE_HARDWARE = " + str(hardware_uid)
    sql_string += " AND INCIDENT_STATUS_CODE != 1 ORDER BY INCIDENT_TIME DESC FETCH FIRST 1 ROWS ONLY"

    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def updateNotificationResponse(nid, response):
    conn = BDPDBConnection.getInstance().getDBConnection()

    sql_string = "UPDATE " + getTableName("BDP_NOTIFICATION") + " SET RESPONSE = '" + json.dumps(response) + "' WHERE NOTIFICATION_ID = '" + str(nid) + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)

def updateIncidentStatus(incident_id, actionstr):
    conn = BDPDBConnection.getInstance().getDBConnection()
    
    action = -1
    if actionstr == 'FIXED':
        action = 1
    elif actionstr == 'SNOOZE':
        action = 3
    if action < 0:
        print('[updateIncidentStatus] action code not identified')
        return False

    now = str(datetime.datetime.now())
    if action == 1:
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', FIX_TIME = '" + now + "' WHERE INCIDENT_ID = " + str(incident_id)
        stmt = ibm_db.exec_immediate(conn, sql_string)
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', FIX_TIME = '" + now + "' WHERE INCIDENT_ID_ORIGINAL = " + str(incident_id)
        stmt = ibm_db.exec_immediate(conn, sql_string)
    else:
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', SNOOZE_TIME = '" + now + "' WHERE INCIDENT_ID = " + str(incident_id)
        stmt = ibm_db.exec_immediate(conn, sql_string)
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', SNOOZE_TIME = '" + now + "' WHERE INCIDENT_ID_ORIGINAL = " + str(incident_id)
        stmt = ibm_db.exec_immediate(conn, sql_string)
    return True

def getHardwareByDevice(device):
    conn = BDPDBConnection.getInstance().getDBConnection()
    
    try:
        deviceType, deviceId = device.split(':')
    except Exception as e:
        print("[getHardwareByDevice] Wrong format of device {}".format(e))
    
    sql_string = "SELECT * FROM " + getTableName("BDP_HARDWARE") 
    sql_string += " WHERE HARDWARE_ID = '"+ deviceId + "' AND HARDWARE_TYPE = '" + deviceType + "'"

    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getHardwareByHardwareUID(hardware_uid):
    conn = BDPDBConnection.getInstance().getDBConnection()

    print("[getHardwareByHardwareUID]: hardware_uid = " + str(hardware_uid))
    
    sql_string = "SELECT * FROM " + getTableName("BDP_HARDWARE") 
    sql_string += " WHERE HARDWARE_UID = '"+ str(hardware_uid) + "'"

    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getRawEventsByHardwareUID(hardware_uid, datapoints_amount):
    conn = BDPDBConnection.getInstance().getDBConnection()
    
    sql_string = "SELECT * FROM " + getTableName("BDP_RAW_EVENTS") 
    sql_string += " WHERE HARDWARE_UID = "+ str(hardware_uid)
    sql_string += " ORDER BY READING_TIME DESC FETCH FIRST " +str(datapoints_amount) + " ROWS ONLY"

    notificationgroups = []
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        notificationgroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return notificationgroups

def insertIncident(existing_incident, new_incident, tenant_id):
    conn = BDPDBConnection.getInstance().getDBConnection()
    if not existing_incident:  
        #new incident
        sql_string = "INSERT INTO " + getTableName("BDP_INCIDENT") 
        sql_string += " (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID, CAUSE_HARDWARE) " 
        sql_string += "VALUES( '" + json.dumps(new_incident['INCIDENT_DETAIL']) + "', '" 
        sql_string += new_incident['INCIDENT_TIME'] + "', 2, '" + str(tenant_id) + "'," + str(new_incident['CAUSE_HARDWARE']) +")"
        
        stmt = ibm_db.exec_immediate(conn, sql_string)
        incident_id = getIncidentID(new_incident)
        print('[insertIncident] New incident_id = {}'.format(new_incident))
    else: 
        #existing incident
        incident_id = str(existing_incident["INCIDENT_ID"])
        print('[insertIncident] Existing incident_id = {}'.format(incident_id))

        sql_string = "INSERT INTO " + getTableName("BDP_INCIDENT") 
        sql_string += " (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID, CAUSE_HARDWARE, INCIDENT_ID_ORIGINAL) " 
        sql_string += "VALUES( '" + json.dumps(new_incident['INCIDENT_DETAIL']) + "', '" 
        sql_string += new_incident['INCIDENT_TIME'] + "', 2, '" + str(tenant_id) + "', "+ str(new_incident['CAUSE_HARDWARE']) + ", " + incident_id + ")"

        stmt = ibm_db.exec_immediate(conn, sql_string)
    
    if ibm_db.num_rows(stmt) == 0:
        print("[insertIncident] Could not add the incident to DB!")
        return 
    
    return incident_id


def insertResponderToIncidentID(incident_id, responder_id):
    conn = BDPDBConnection.getInstance().getDBConnection()

    incident_details = json.loads(getIncidentByIncidentID(incident_id)['INCIDENT_DETAIL'])
    incident_details['RESPONDER'] = responder_id

    sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_DETAIL = '" + json.dumps(incident_details) + "' WHERE INCIDENT_ID = " + str(incident_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)


def removeUser(user_id):
    conn = BDPDBConnection.getInstance().getDBConnection()
    sql_string = "DELETE FROM " + getTableName("BDP_USER") + " WHERE USER_ID = " + str(user_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)
