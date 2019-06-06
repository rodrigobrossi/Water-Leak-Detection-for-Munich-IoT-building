import unittest
from unittest import mock

import datetime

from bdp_notifier import BDPNotifier

class TestStringMethods(unittest.TestCase):

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
    def test_time_to_notify(self, getUsers):
        userList = ['jo']
        getUsers.return_value = userList

        incident_record = {}
        incident_record["SNOOZE_TIME"] = datetime.datetime.now()

        tenant_record = {}
        tenant_record["ALARM_INTERVAL_HR"] = 1
        tenant_record["SNOOZE_HR"] = 1
        tenant_record["TENANT_ID"] = 1

        result = BDPNotifier._timeToNotify(incident_record, tenant_record)
        self.assertEqual(result, userList)


if __name__ == '__main__':
    unittest.main()