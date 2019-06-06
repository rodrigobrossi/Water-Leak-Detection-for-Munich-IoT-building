import unittest
from unittest import mock

from datetime import datetime, timedelta

from bdp_notifier import BDPNotifier

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

if __name__ == '__main__':
    unittest.main()