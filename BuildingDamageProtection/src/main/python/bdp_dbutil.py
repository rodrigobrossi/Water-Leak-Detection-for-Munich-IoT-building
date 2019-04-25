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
#DATABASE=name;HOSTNAME=host;PORT=60000;PROTOCOL=TCPIP;UID=username;PWD=password;
    conn_string = "DATABASE=" + BDPProperty.getInstance().getValue('db_dbname')
    conn_string = conn_string + ";HOSTNAME=" + BDPProperty.getInstance().getValue('db_host')
    conn_string = conn_string + ";PORT=" + BDPProperty.getInstance().getValue('db_port')
    conn_string = conn_string + ";PROTOCOL=TCPIP;UID=" + BDPProperty.getInstance().getValue('db_admin_user')
    conn_string = conn_string + ";PWD=" + BDPProperty.getInstance().getValue('db_password')
    print(conn_string)
    conn = ibm_db.connect(BDPProperty.getInstance().getValue('db_dbname'), BDPProperty.getInstance().getValue('db_admin_user'), AIProperty.getInstance().getValue('db_admin_password'))
    '''conn.autocommit = True'''
    return conn