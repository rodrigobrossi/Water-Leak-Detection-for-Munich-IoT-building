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

import sched
import datetime, time
import pprint
from threading import Thread
from bdp_property import BDPProperty
from bdp_dbutil import *


class BDPServiceCheck(object):

    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def setup(self, actionargs=()):
        action = periodic_event
        action(*actionargs)
        self.scheduler.enter(int(BDPProperty.getInstance().getValue('check_status_interval')) * 60 * 60, 60, self.setup,
                        ()) #hour level

    def run(self):
        self.scheduler.run()


# This is the event to execute every time  
def periodic_event():
    try:
        print(datetime.datetime.now())
        print("system checking")
        conn = BDPDBConnection.getInstance().getDBConnection()
        sql_string = "select * from " + BDPProperty.getInstance().getValue('db_admin_user') + ".BDP_DBCHANGELOG where changeid = '01'"
        print(sql_string)
        stmt = ibm_db.exec_immediate(conn, sql_string)
        dictionary = ibm_db.fetch_assoc(stmt)
        if dictionary != False:
            ret = True
            print("good")
        else:
            ret = False
            print("bad")
        return ret
    except Exception as e:
        print(e)
        conn = BDPDBConnection.getInstance().getDBConnection(True)

    



