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
    conn = ibm_db.connect(BDPProperty.getInstance().getValue('db_dbname'), BDPProperty.getInstance().getValue('db_admin_user'), AIProperty.getInstance().getValue('db_admin_password'))
    '''conn.autocommit = True'''
    return conn