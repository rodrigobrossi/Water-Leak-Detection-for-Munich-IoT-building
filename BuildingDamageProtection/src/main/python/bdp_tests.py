import datetime
import colorama

import unittest
from  unittest.mock import patch

import ibm_db

from bdp_incident import BDPIncident
from bdp_notifier import BDPNotifier
import bdp_dbutil

class TestNotifier(unittest.TestCase):
    @patch('bdp_dbutil.getUsersWithNIDs')
    def getUsersMock(self):
        print('MOCKING')
        return

    def test_timeToNotify(self):
        #BDPNotifier._timeToNotify({'SNOOZE_TIME':None,'NOTIFY_TIME':str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"))},{})
        self.assertTrue(True)

class Tests():
    def getTestResult(condition):
        result = colorama.Back.GREEN + '[PASS]' if condition else colorama.Back.RED + '[FAIL]'
        return result + colorama.Style.RESET_ALL

    def incidentHierarchyTest():
        test_name = colorama.Back.CYAN + '[incidentHierarchy]' + colorama.Style.RESET_ALL
        print(test_name + ' Test start ...')
        over_all_condition = True
        # ----------------------------------------------------------------------------
        print(test_name + ' Preparing the DB')
        # Resolve open incidents
        old_incident = bdp_dbutil.checkExcistingIncident(2, 1)
        if old_incident: 
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        old_incident = bdp_dbutil.checkExcistingIncident(2, 11)
        
        if old_incident:     
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        # ----------------------------------------------------------------------------
        # Create an incident
        incident = {}

        incident['INCIDENT_DETAIL'] = {}
        incident['INCIDENT_DETAIL']['URGENCY'] = 'moderate'
        incident['INCIDENT_DETAIL']['HUMIDITY'] = 50

        incident['INCIDENT_TIME'] = str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"))
        incident['TENANT_ID'] = 2
        incident['CAUSE_HARDWARE'] = 1

        notification = BDPIncident._insertIncidentInDB(incident)

        condition = not notification['OLD_INCIDENT']
        print(Tests.getTestResult(condition) + ' registering new incident')
        over_all_condition = over_all_condition and condition
        # ----------------------------------------------------------------------------
        # Update the time
        incident['INCIDENT_TIME'] = str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"))
        
        notification = BDPIncident._insertIncidentInDB(incident)

        condition = notification['OLD_INCIDENT'] != None
        print(Tests.getTestResult(condition) + ' finding a parent incident')
        over_all_condition = over_all_condition and condition
        # ----------------------------------------------------------------------------
        # Change the hardware
        incident['INCIDENT_TIME'] = str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"))
        incident['CAUSE_HARDWARE'] = 11

        notification = BDPIncident._insertIncidentInDB(incident)

        condition = not notification['OLD_INCIDENT']
        print(Tests.getTestResult(condition) + ' creating an incident with a different hardware')
        over_all_condition = over_all_condition and condition
        # ----------------------------------------------------------------------------
        old_incident = bdp_dbutil.checkExcistingIncident(2, 1)
        bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        
        conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()
        # Check that incident was updated
        sql_string = "SELECT * FROM " + bdp_dbutil.getTableName("BDP_INCIDENT") + " WHERE INCIDENT_STATUS_CODE != 1 AND INCIDENT_ID = " + str(old_incident['INCIDENT_ID'])
        response_1 = ibm_db.fetch_assoc(ibm_db.exec_immediate(conn, sql_string))
        # Check that children incidents are updated
        sql_string = "SELECT * FROM " + bdp_dbutil.getTableName("BDP_INCIDENT") + " WHERE INCIDENT_STATUS_CODE != 1 AND INCIDENT_ID_ORIGINAL = " + str(old_incident['INCIDENT_ID'])
        response_2 = ibm_db.fetch_assoc(ibm_db.exec_immediate(conn, sql_string))
        
        condition = not (response_1 or response_2)
        print(Tests.getTestResult(condition) + ' updating status')
        over_all_condition = over_all_condition and condition
        # ----------------------------------------------------------------------------
        print(test_name + Tests.getTestResult(over_all_condition))

if __name__ == '__main__':
    unittest.main()