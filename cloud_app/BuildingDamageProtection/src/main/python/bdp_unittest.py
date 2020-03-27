import unittest
from unittest import mock

from flask import json

from datetime import datetime, timedelta
import numpy as np

import ibm_db

from bdp_notifier import BDPNotifier
from bdp_incident import BDPIncident
from bdp_respond import BDPIncidentRespond
import bdp_dbutil

class TestNotifier(unittest.TestCase):

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
    def test_send_if_snooze_time_up(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        yesterday = datetime.today() - timedelta(days=1)
        incident_record = {}
        incident_record["SNOOZE_TIME"] = yesterday
        incident_record["NOTIFY_TIME"] = datetime.today()
        incident_record["INCIDENT_ID"] = 1

        tenant_record = self.buildTenantRecord(30, 12)

        result = BDPNotifier._timeToNotify(incident_record, tenant_record)
        self.assertEqual(result, userList)

    @mock.patch('bdp_dbutil.getUsersWithNIDs')
    def test_send_if_notify_time_up(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        yesterday = datetime.today() - timedelta(days=1)
        incident_record = {}
        incident_record["SNOOZE_TIME"] = None
        incident_record["NOTIFY_TIME"] = yesterday

        tenant_record = self.buildTenantRecord(1, 30)

        result = BDPNotifier._timeToNotify(incident_record, tenant_record)
        self.assertEqual(result, userList)

    @mock.patch('bdp_dbutil.getUsersWithNIDs')
    def test_not_send_if_notify_time_up_and_is_snoozed(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        yesterday = datetime.today() - timedelta(days=1)
        incident_record = {}
        incident_record["SNOOZE_TIME"] = datetime.now()
        incident_record["NOTIFY_TIME"] = yesterday

        tenant_record = self.buildTenantRecord(3, 1)

        result = BDPNotifier._timeToNotify(incident_record, tenant_record)
        self.assertEqual(result, [])

    @mock.patch('bdp_dbutil.getUsersWithNIDs')
    def test_not_send(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        incident_record = {}
        incident_record["SNOOZE_TIME"] = datetime.now()

        tenant_record = self.buildTenantRecord(1, 1)

        result = BDPNotifier._timeToNotify(incident_record, tenant_record)
        self.assertEqual(result, [])
    
    def buildTenantRecord(self, alarm_interval_hour, snooze_hour):
        tenant_record = {}
        tenant_record["ALARM_INTERVAL_HR"] = alarm_interval_hour
        tenant_record["SNOOZE_HR"] = snooze_hour
        tenant_record["TENANT_ID"] = 1
        return tenant_record

class StubDate(datetime):
    pass

class TestDBUtil(unittest.TestCase):

    def user_time_mock(tenant_id, times):
        if times == 1: #all hours
            return ['1']
        elif times == 2:
            return ['2']
        elif times == 3:
            return ['3']
        return []

    @mock.patch('bdp_dbutil.getUsersWithNIDsAtTimes', side_effect=user_time_mock)
    @mock.patch('bdp_dbutil.datetime.datetime', StubDate)
    def test_users_in_business_hours(self, getUsersAtTimes):

        StubDate.now = classmethod(lambda cls: datetime(2020, 11, 13, 10, 00, 00, 00))

        users = bdp_dbutil.getUsersWithNIDs(1)
        self.assertCountEqual(users, ['1', '3'])

    @mock.patch('bdp_dbutil.getUsersWithNIDsAtTimes', side_effect=user_time_mock)
    @mock.patch('bdp_dbutil.datetime.datetime', StubDate)
    def test_users_late_on_weekday(self, getUsersAtTimes):

        StubDate.now = classmethod(lambda cls: datetime(2020, 11, 13, 20, 00, 00, 00)) 

        users = bdp_dbutil.getUsersWithNIDs(1)
        self.assertCountEqual(users, ['2', '3'])

    @mock.patch('bdp_dbutil.getUsersWithNIDsAtTimes', side_effect=user_time_mock)
    @mock.patch('bdp_dbutil.datetime.datetime', StubDate)
    def test_users_on_weekend(self, getUsersAtTimes):

        StubDate.now = classmethod(lambda cls: datetime(2020, 11, 15, 10, 00, 00, 00)) 

        users = bdp_dbutil.getUsersWithNIDs(1)
        self.assertCountEqual(users, ['2', '3'])



class TestRespondWithDB(unittest.TestCase):

    def createIncident(self, time, sensor, urgency = 'moderate'):
        incident = {}

        incident['INCIDENT_DETAIL'] = {}
        incident['INCIDENT_DETAIL']['URGENCY'] = urgency
        incident['INCIDENT_DETAIL']['HUMIDITY'] = 50

        incident['INCIDENT_TIME'] = time
        incident['TENANT_ID'] = 2
        incident['CAUSE_HARDWARE'] = sensor

        return BDPIncident._insertIncidentInDB(incident)
    
    def getUsersWithNotificationIDs(self, incident):
        users = bdp_dbutil.getUsersWithNIDs(2)
        bdp_dbutil.createNotificationRecord(incident, 2, users)

        return users

    def setUp(self):
        old_incident = bdp_dbutil.checkExcistingIncident(2, 1)
        if old_incident: 
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        
        old_incident = bdp_dbutil.checkExcistingIncident(2, 11)
        if old_incident:     
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')

    @mock.patch("bdp_dbutil.getPlottingData")
    def test_buildContext(self, getPlottingData):
        incident_respond = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        users = self.getUsersWithNotificationIDs(incident_respond["NEW_INCIDENT_ID"])
        context = BDPIncidentRespond.buildContext(users[0]["NOTIFICATION_ID"])
        getPlottingData.return_value = [np.array([]), np.array([])]
        
        self.assertEqual(context['name'], users[0]["USER_NAME"])
        self.assertEqual(context['tenant'], 'IBM Test')
        self.assertEqual(context['sensor_id'], 'TestSensor1')
        self.assertEqual(context['hardware_uid'], 1)
        self.assertEqual(context['status'], 'New')
        self.assertEqual(context['handler'], 'Not assigned')

    @mock.patch("bdp_dbutil.getPlottingData")
    def test_correct_urgency(self, getPlottingData):
        orig_time = datetime.today() - timedelta(hours=2)
        incident_respond = self.createIncident(str(orig_time), 1, 'moderate')
        incident_respond = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1, 'critical')
        users = self.getUsersWithNotificationIDs(incident_respond["NEW_INCIDENT_ID"])
        context = BDPIncidentRespond.buildContext(users[0]["NOTIFICATION_ID"])
        
        getPlottingData.return_value = [np.array([]), np.array([])]
        
        self.assertEqual(context['urgency_vis_3'], 'visible')

class TestExistingIncidentWithDB(unittest.TestCase):

    def createIncident(self, time, sensor):
        incident = {}

        incident['INCIDENT_DETAIL'] = {}
        incident['INCIDENT_DETAIL']['URGENCY'] = 'moderate'
        incident['INCIDENT_DETAIL']['HUMIDITY'] = 50

        incident['INCIDENT_TIME'] = time
        incident['TENANT_ID'] = 2
        incident['CAUSE_HARDWARE'] = sensor

        return BDPIncident._insertIncidentInDB(incident)

    def setUp(self):
        old_incident = bdp_dbutil.checkExcistingIncident(2, 1)
        if old_incident: 
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        
        old_incident = bdp_dbutil.checkExcistingIncident(2, 11)
        if old_incident:     
            bdp_dbutil.updateIncidentStatus(old_incident['INCIDENT_ID'], 'FIXED')
        
    def test_newIncident(self):
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        
        self.assertFalse(notification['OLD_INCIDENT'])

    def test_sameIncident(self):
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        
        self.assertNotEqual(notification['OLD_INCIDENT'], False)

    def test_differentIncident(self):
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 11)
        
        self.assertFalse(notification['OLD_INCIDENT'])

    def test_updateIncident(self):
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        
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
    
class TestTririgaWorkTaskCreation(unittest.TestCase):
        
    def createIncident(self, time, sensor):
        incident = {}

        incident['INCIDENT_DETAIL'] = {}
        incident['INCIDENT_DETAIL']['URGENCY'] = 'moderate'
        incident['INCIDENT_DETAIL']['HUMIDITY'] = 50

        incident['INCIDENT_TIME'] = time
        incident['TENANT_ID'] = 2
        incident['CAUSE_HARDWARE'] = sensor

        return BDPIncident._insertIncidentInDB(incident)

    def test_tririga(self):
        notification = self.createIncident(str(datetime.now().strftime("%Y-%m-%d-%H.%M.%S")), 1)
        tririga_response = BDPNotifier._generateTririgaWorkTaks(notification["NEW_INCIDENT_ID"])
        self.assertTrue(tririga_response)


if __name__ == '__main__':
    unittest.main()