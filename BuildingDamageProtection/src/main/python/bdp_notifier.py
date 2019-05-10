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
from bdp_property import BDPProperty

class BDPNotifier():

    def hardwareCallback(event):
        print("[BDPNotifier] msg from device [%s]: %s" % (event.device, json.dumps(event.data)))
        try:
            conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            hardware_uid = bdp_dbutil.getHardwareByDevice(conn, event.device)["HARDWARE_UID"]

            sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_RAW_EVENTS") + "(READING_TIME, READING, HARDWARE_UID) VALUES ('" 
            sql_string += str(timestamp) + "', '" + json.dumps(event.data) + "', '" + str(hardware_uid)  + "')"
            print("[BDPNotifier] Inserting to DB: {}".format(sql_string))
            
            stmt = ibm_db.exec_immediate(conn, sql_string)
            if ibm_db.num_rows(stmt) == 0:
                print("[BDPNotifier] Could not add the event to DB!")

            BDPNotifier.processEvent(conn, hardware_uid)
            
        except Exception as e:
            print(e)
    
    def processEvent(conn,hardware_uid):
        print(bdp_dbutil.getRawEventsByHardwareUID(conn, hardware_uid))
        