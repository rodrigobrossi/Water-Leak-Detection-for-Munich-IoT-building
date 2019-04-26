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

def get_db_connection():
    conn_string = "DATABASE=" + BDPProperty.getInstance().getValue('db_dbname')
    conn_string = conn_string + ";HOSTNAME=" + BDPProperty.getInstance().getValue('db_dbhost')
    conn_string = conn_string + ";PORT=" + BDPProperty.getInstance().getValue('db_dbport')
    conn_string = conn_string + ";PROTOCOL=TCPIP;UID=" + BDPProperty.getInstance().getValue('db_admin_user')
    conn_string = conn_string + ";PWD=" + BDPProperty.getInstance().getValue('db_admin_password')
    print(conn_string)
    conn = ibm_db.connect(conn_string, "", "")
    '''conn.autocommit = True'''
    return conn

def get_tenantid_by_name(conn, tenant):
    sql_string = "SELECT * FROM " + get_table_name("BDP_TENANT") + " WHERE TENANT = '" + tenant + "'"
    stmt = ibm_db.exec_immediate(conn, sql_string)
    dictionary = ibm_db.fetch_both(stmt)
    if dictionary != False:
        return dictionary
    else:
        return None
    
def get_table_name(tablename):
    return BDPProperty.getInstance().getValue('db_admin_user') + "." + tablename
    