import unittest
from unittest import mock

import datetime

import ibm_db

from bdp_notifier import BDPNotifier
from bdp_incident import BDPIncident
import bdp_dbutil

class TestNotifier(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    @mock.patch('bdp_dbutil.getUsersWithNIDs')
    def test_send_if_new(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        tenant_record = {}
        tenant_record["ALARM_INTERVAL_HR"] = 1
        tenant_record["SNOOZE_HR"] = 1
        tenant_record["TENANT_ID"] = 1

        result = BDPNotifier._timeToNotify(False, tenant_record)
        self.assertEqual(result, userList)

    @mock.patch('bdp_dbutil.getUsersWithNIDs')
    def test_not_send(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        incident_record = {}
        incident_record["SNOOZE_TIME"] = datetime.datetime.now()

        tenant_record = {}
        tenant_record["ALARM_INTERVAL_HR"] = 1
        tenant_record["SNOOZE_HR"] = 1
        tenant_record["TENANT_ID"] = 1

        result = BDPNotifier._timeToNotify(incident_record, tenant_record)
        self.assertEqual(result, [])

class TestExistingIncident(unittest.TestCase):

    def setUp(self):
        old_incident = bdp_dbutil.checkExcistingIncident(2, 1)
        if old_incident: 
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        
        old_incident = bdp_dbutil.checkExcistingIncident(2, 11)
        if old_incident:     
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        

    def createIncident(self, time, sensor):
        incident = {}

        incident['INCIDENT_DETAIL'] = {}
        incident['INCIDENT_DETAIL']['URGENCY'] = 'moderate'
        incident['INCIDENT_DETAIL']['HUMIDITY'] = 50

        incident['INCIDENT_TIME'] = time
        incident['TENANT_ID'] = 2
        incident['CAUSE_HARDWARE'] = sensor

        return incident
        
    def test_newIncident(self):
        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = BDPIncident._insertIncidentInDB(incident)

        self.assertFalse(notification['OLD_INCIDENT'])

    def test_sameIncident(self):
        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = BDPIncident._insertIncidentInDB(incident)

        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = BDPIncident._insertIncidentInDB(incident)

        self.assertNotEqual(notification['OLD_INCIDENT'], False)

    def test_differentIncident(self):
        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = BDPIncident._insertIncidentInDB(incident)

        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 11)
        notification = BDPIncident._insertIncidentInDB(incident)

        self.assertFalse(notification['OLD_INCIDENT'])

    def test_updateIncident(self):
        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = BDPIncident._insertIncidentInDB(incident)

        incident = self.createIncident(str(datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = BDPIncident._insertIncidentInDB(incident)

        self.assertIsNotNone(notification['OLD_INCIDENT'])

        old_incident = bdp_dbutil.checkExcistingIncident(2, 1)
        bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        
        conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()
        # Check that incident was updated
        sql_string = "SELECT * FROM " + bdp_dbutil.getTableName("BDP_INCIDENT") + " WHERE INCIDENT_STATUS_CODE != 1 AND INCIDENT_ID = " + str(old_incident['INCIDENT_ID'])
        response_1 = ibm_db.fetch_assoc(ibm_db.exec_immediate(conn, sql_string))

        self.assertFalse(response_1)

        # Check that children incidents are updated
        sql_string = "SELECT * FROM " + bdp_dbutil.getTableName("BDP_INCIDENT") + " WHERE INCIDENT_STATUS_CODE != 1 AND INCIDENT_ID_ORIGINAL = " + str(old_incident['INCIDENT_ID'])
        response_2 = ibm_db.fetch_assoc(ibm_db.exec_immediate(conn, sql_string))
        
        self.assertFalse(response_2)

if __name__ == '__main__':
    unittest.main()