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
import ibm_db
from bdp_property import BDPProperty
from bdp_util import *
import datetime
from flask import json


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

'''def getDBConnection():
    conn_string = "DATABASE=" + BDPProperty.getInstance().getValue('db_dbname')
    conn_string = conn_string + ";HOSTNAME=" + BDPProperty.getInstance().getValue('db_dbhost')
    conn_string = conn_string + ";PORT=" + BDPProperty.getInstance().getValue('db_dbport')
    conn_string = conn_string + ";PROTOCOL=TCPIP;UID=" + BDPProperty.getInstance().getValue('db_admin_user')
    conn_string = conn_string + ";PWD=" + BDPProperty.getInstance().getValue('db_admin_password')
    print(conn_string)
    conn = ibm_db.connect(conn_string, "", "")
    #conn.autocommit = True
    return conn'''

def getTenantByName(conn, tenant):
    sql_string = "SELECT * FROM " + getTableName("BDP_TENANT") + " WHERE TENANT = '" + tenant + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_both(stmt)
    if dictionary != False:
        return dictionary
    else:
        return None
    
def getTableName(tablename):
    return BDPProperty.getInstance().getValue('db_admin_user') + "." + tablename

def getAllUsers(conn, tenant_id):
    usergroups = []
    print("getting all users for tenant: " + str(tenant_id))
    if tenant_id < 0:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER")
    else:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER") + " WHERE TENANT_ID = " + str(tenant_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        dictionary["NOTIFICATION_ID"] = randomString()
        usergroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return usergroups
    
def snoozeFlip(conn, incident_record, state):
    if state is True:
        #set snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET SNOOZE_TIME = '" + str(datetime.datetime.now()) + "' WHERE INCIDENT_ID = " + str(incident_record["INCIDENT_ID"])
    else:
        #turn of snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET SNOOZE_TIME = null WHERE INCIDENT_ID = " + str(incident_record["INCIDENT_ID"])
    stmt = ibm_db.exec_immediate(conn, sql_string)

def updateIncidentNotifyTime(conn, incidentid):
    sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET NOTIFY_TIME = '" + str(datetime.datetime.now()) + "' WHERE INCIDENT_ID = " + str(incidentid)
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    
def createNotificationRecord(conn, incidentid, usergroups):
    now = str(datetime.datetime.now())
    for user in usergroups:
        notificationid = user["NOTIFICATION_ID"]
        userid = str(user["USER_ID"])
        sql_string = "INSERT INTO " + getTableName("BDP_NOTIFICATION") + " (NOTIFICATION_ID, INCIDENT_ID, NOTIFICATION_TYPE, NOTIFICATION_TIME, USER_ID) VALUES( '" + notificationid + "', '" + str(incidentid) + "', 1, '" + now + "', " + userid + ")"
        print(sql_string)
        stmt = ibm_db.exec_immediate(conn, sql_string)
        
def getNotificationsByIncidentID(conn, incidentid): #not tested yet
    notificationgroups = []
    sql_string = "SELECT * FROM " + getTableName("BDP_NOTIFICATION") + " WHERE INCIDENT_ID = '"  + str(incidentid) + "'"
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        notificationgroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return notificationgroups

def getNotificationByNotificationID(conn, nid): #not tested yet
    notificationgroups = []
    sql_string = "SELECT * FROM " + getTableName("BDP_NOTIFICATION") + " WHERE NOTIFICATION_ID = '"  + str(nid) + "'"
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getUserByUserID(conn, user_id):
    print("getUserByUserID: " + str(user_id))
    sql_string = "SELECT * FROM " + getTableName("BDP_USER") + " WHERE USER_ID = " + str(user_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getIncidentByIncidentID(conn, incident_id):
    print("getIncidentByIncidentID: " + str(incident_id))
    sql_string = "SELECT * FROM " + getTableName("BDP_INCIDENT") + " WHERE INCIDENT_ID = " + str(incident_id)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def updateNotificationResponse(conn, nid, response):
    sql_string = "UPDATE " + getTableName("BDP_NOTIFICATION") + " SET RESPONSE = '" + json.dumps(response) + "' WHERE NOTIFICATION_ID = '" + str(nid) + "'"
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)

def updateIncidentStatus(conn, incident_id, actionstr):
    action = -1
    if actionstr == 'fixed':
        action = 1
    elif actionstr == 'snooze':
        action = 3
    if action < 0:
        return False
    now = str(datetime.datetime.now())
    if action == 1:
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', FIX_TIME = '" + now + "' WHERE INCIDENT_ID = " + str(incident_id)
    else:
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', SNOOZE_TIME = '" + now + "' WHERE INCIDENT_ID = " + str(incident_id)
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    return True

def getHardwareByDevice(conn, device):
    print("[getHardwareByDevice]: " + str(device))
    
    try:
        deviceType, deviceId = device.split(':')
    except Exception as e:
        print("[getHardwareByDevice] Wrong format of device {}".format(e))
    
    sql_string = "SELECT * FROM " + getTableName("BDP_HARDWARE") 
    sql_string += " WHERE HARDWARE_ID = '"+ deviceId + "' AND HARDWARE_TYPE = '" + deviceType + "'"
    print("[getHardwareByDevice] injecting to DB: " + sql_string)

    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    return dictionary

def getRawEventsByHardwareUID(conn, hardware_uid):
    print("[getRawEventsByDevice]: " + str(hardware_uid))
    
    sql_string = "SELECT * FROM " + getTableName("BDP_RAW_EVENTS") 
    sql_string += " WHERE HARDWARE_UID = '"+ str(hardware_uid) + "'"
    print("[getRawEventsByDevice] injecting to DB: " + sql_string)

    notificationgroups = []
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        notificationgroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return notificationgroups