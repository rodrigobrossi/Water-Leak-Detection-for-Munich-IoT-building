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
import ibm_db
from bdp_property import BDPProperty

def getDBConnection():
    conn_string = "DATABASE=" + BDPProperty.getInstance().getValue('db_dbname')
    conn_string = conn_string + ";HOSTNAME=" + BDPProperty.getInstance().getValue('db_dbhost')
    conn_string = conn_string + ";PORT=" + BDPProperty.getInstance().getValue('db_dbport')
    conn_string = conn_string + ";PROTOCOL=TCPIP;UID=" + BDPProperty.getInstance().getValue('db_admin_user')
    conn_string = conn_string + ";PWD=" + BDPProperty.getInstance().getValue('db_admin_password')
    print(conn_string)
    conn = ibm_db.connect(conn_string, "", "")
    '''conn.autocommit = True'''
    return conn

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
    print("getting all users for tenant: " + str(tenant_id))
    if tenant_id < 0:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER")
    else:
        sql_string = "SELECT * FROM " + getTableName("BDP_USER") + " WHERE TENANT_ID = " + str(tenant_id)
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_both(stmt)
    if dictionary != False:
        print(dictionary)
        return dictionary
    else:
        return None
    
def snoozeFlip(conn, incident_record, state):
    if state is True:
        #set snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SNOOZE_TIME = " + datetime.datetime.now() + " WHERE INCIDENT_ID = " + str(incident_record["INCIDENT_ID"])
    else:
        #turn of snooze
        sql_string = "UPDATE " + getTableName("BDP_INCIDENT") + " SET SNOOZE_TIME = null WHERE INCIDENT_ID = " + str(incident_record["INCIDENT_ID"])
    print(sql_string)
    stmt = ibm_db.exec_immediate(conn, sql_string)
    