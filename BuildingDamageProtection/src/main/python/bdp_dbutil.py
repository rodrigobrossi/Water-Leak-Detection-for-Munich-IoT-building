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
import datetime, uuid
from flask import json
import pandas as pd
#import matplotlib.pyplot as plt

import ibm_db

from bdp_property import BDPProperty
import bdp_util

from pathlib import Path

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

def _randomString(string_length=10):
    """
    Returns a random string of a certain length.

    :param string_length: length
    :type string_length: int

    :return: str
    """
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.

def getUsersWithNIDsAtTimes(tenant_id, times):
    """
    Returns a list of users that are associated with certain times and assigns a notification ID

    :param tenant_id: length
    :type tenant_id: int
    :param times: availability times
    :type times: enum

    :return: list of users 
    """
    conn = BDPDBConnection.getInstance().getDBConnection()
    usergroups = []
    if tenant_id < 0:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER")
    else:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER") + " WHERE TENANT_ID = " + str(tenant_id) + " AND USER_TIMES = " + str(times)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_assoc(stmt)
    while dictionary != False:
        dictionary["NOTIFICATION_ID"] = _randomString()
        usergroups.append(dictionary)
        dictionary = ibm_db.fetch_assoc(stmt)
    return usergroups

def getUsersWithNIDs(tenant_id):
    """
    Returns a list of users that are associated with current time and assigns a notification ID

    :param tenant_id: length
    :type tenant_id: int

    :return: list of users 
    """
    usergroups = getUsersWithNIDsAtTimes(tenant_id, 3)
    
    timestamp = datetime.datetime.now()
    if timestamp.weekday() > 4 or timestamp.hour < 8 or timestamp.hour > 18:
        usergroups.extend(getUsersWithNIDsAtTimes(tenant_id, 2))
    else:
        usergroups.extend(getUsersWithNIDsAtTimes(tenant_id, 1))

    return usergroups

def snoozeFlip(incident_id, state):
    """
    Flips the snooze flag.

    :param incident_id: Incident ID
    :type incident_id: int
    :param state: If true, the flag is set; otherwise removed
    :type state: bool
    """
    conn = BDPDBConnection.getInstance().getDBConnection()
    if state is True:
        updateIncidentStatus(incident_id, 3)
    else:
        #turn off snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET SNOOZE_TIME = NULL, INCIDENT_STATUS_CODE=2 WHERE INCIDENT_ID = " + str(incident_id) + " OR INCIDENT_ID_ORIGINAL = " + str(incident_id)
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
        sql_string += str(notificationid) + "', '" + str(incidentid) + "', "+ str(type_code)+", '" + now + "', " + str(userid) + ")"
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
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', FIX_TIME = '" + now + "' WHERE INCIDENT_ID = " + str(incident_id) + " OR INCIDENT_ID_ORIGINAL = " + str(incident_id)
        stmt = ibm_db.exec_immediate(conn, sql_string)
    else:
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET INCIDENT_STATUS_CODE = '" + str(action) + "', SNOOZE_TIME = '" + now + "' WHERE INCIDENT_ID = " + str(incident_id) + " OR INCIDENT_ID_ORIGINAL = " + str(incident_id)
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

def createHumidityTable(hardware_uid, datapoint_amount):
    """
    Creates a pandas table with humidity

    :param hardware_uid: Hardware unique ID
    :type hardware_uid: int
    :param datapoint_amount: Amount to datapoints to extract
    :type datapoint_amount: int

    :return: pandas.DataFrame
    """
    table = pd.DataFrame(getRawEventsByHardwareUID(hardware_uid, 480))

    table['HUMIDITY'] = None
    table['TIME_ONLY'] = None

    # Change to descending order
    table = table.iloc[::-1].reset_index(drop=True)
    
    for i in range(table.shape[0]):
        # Extract data from json
        hardware_json = json.loads(table.READING.iloc[i])
        # Save humidity in a seperate row
        table.at[i, 'HUMIDITY']  = hardware_json['humidity']
        # Extract time from datetime
        table.at[i, 'TIME'] = table.loc[i, 'READING_TIME'].strftime('%H:%m:%S')
    return table

def getPlottingData(hardware_uid, datapoint_amount=480, plotpoint_amount=8, datapoint_types=['TIME','HUMIDITY']):
    """
    Create an overview points od the plotpoint_amount about the data points of datapoint_amount

    :param hardware_uid: Hardware unique ID
    :type hardware_uid: int
    :param datapoint_amount: Amount to datapoints to extract
    :type datapoint_amount: int
    :param plotpoint_amount: Amount to plotting points to extract (values are averaged out from datapoints)
    :type plotpoint_amount: int
    :param datapoint_types: List of datapoints types that should be extracted from the table
    :type datapoint_types: list

    :return: list arrays that contain different datapoint types
    """
    table = createHumidityTable(hardware_uid, datapoint_amount)
    #tmp storage
    tmp = pd.DataFrame(data=None, columns=datapoint_types)
    #data chunk size
    jump_size = int(datapoint_amount / plotpoint_amount)
    
    for i in range(0, table.shape[0], jump_size):
        # slice out the interesting part of the table
        table_slice = table[i:i + jump_size + 1]
        # calculate means of numeric columns
        column_means = table_slice.mean()
        # append an empty row
        tmp = tmp.append(pd.Series(), ignore_index=True)
        for t in datapoint_types:
            # if one of the datapoint types is not numeric
            if not t in column_means.index:
                # take the value in the middle of the table slice
                middle_row = int(i + jump_size/2)
                tmp[t].iat[-1] = table_slice.loc[middle_row, t]
            else:
                # else take the mean
                tmp[t].iat[-1] = round(column_means[t], 2)
    return [tmp[i].values for i in datapoint_types]

def getNotificationDetailsById(notification_id):

    conn = BDPDBConnection.getInstance().getDBConnection()

    sql = """ SELECT usr.USER_NAME, 
        incident.INCIDENT_TIME, incident.INCIDENT_STATUS_CODE, INCIDENT.INCIDENT_DETAIL, incident.INCIDENT_ID,
        HARDWARE.HARDWARE_ID, HARDWARE.HARDWARE_DETAIL, HARDWARE.HARDWARE_TYPE, HARDWARE.HARDWARE_UID, 
        TENANT.TENANT_NAME, TENANT.TENANT_ID 
        FROM BDP_NOTIFICATION notification 
        INNER JOIN BDP_USER usr ON NOTIFICATION.USER_ID = usr.USER_ID 
        INNER JOIN BDP_INCIDENT incident ON INCIDENT.INCIDENT_ID = notification.INCIDENT_ID 
        INNER JOIN BDP_TENANT tenant ON INCIDENT.TENANT_ID = TENANT.TENANT_ID 
        INNER JOIN BDP_HARDWARE hardware ON INCIDENT.CAUSE_HARDWARE = HARDWARE.HARDWARE_UID 
        WHERE notification.NOTIFICATION_ID = ? """

    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, str(notification_id))
    ibm_db.execute(stmt)
    return ibm_db.fetch_assoc(stmt)
