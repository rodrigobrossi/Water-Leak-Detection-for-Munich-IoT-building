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
import json
import datetime

from flask import Response, render_template, make_response
from flask import Flask
from flask_restful import Resource, Api
from flask import request
from flask import json
from flask_httpauth import HTTPBasicAuth

import bdp_dbutil, bdp_util
from bdp_property import BDPProperty
from bdp_notifier import BDPNotifier

class BDPIncidentRespond(Resource):
    """
    Class that handles UI POST and GET requests
    """
    def get(self):
        """
        Generates UI web page based on notification id parameter
        """
        try:
            nid = request.args.get('nid')
            context = BDPIncidentRespond.buildContext(nid)

            resp = make_response(render_template('respond.html', **context))
            resp.headers['Content-type'] = 'text/html; charset=utf-8'

            return resp

        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

    def buildContext(nid):
        """
        Builds a context required for an UI tempate
        
        :param nid: notification ID
        :type nid: int

        :return: json of context
        """

        details = bdp_dbutil.getNotificationDetailsById(nid)

        users_group = bdp_dbutil.getUsersWithNIDs(details['TENANT_ID'])

        users_names = []
        for user in users_group:
            users_names.append(user['USER_NAME'])

        bdp_dbutil.createPlot(details['HARDWARE_UID'], 480)

        status_code = {
                    1: 'Resolved',
                    2: 'New',
                    3: 'In progress'
                }

        incident_status = status_code[details['INCIDENT_STATUS_CODE']]
        incident_detail = json.loads(details['INCIDENT_DETAIL'])
        urgency = incident_detail['URGENCY']

        handler = 'Not assigned'
        if 'RESPONDER' in incident_detail.keys():
            handler_id = incident_detail['RESPONDER']
            handler = bdp_dbutil.getUserByUserID(handler_id)['USER_NAME']

        bdp_dbutil.createPlot(details['HARDWARE_UID'], 480)

        return {'name': details['USER_NAME'],
                'tenant' : details['TENANT_NAME'],
                'sensor_id' : details['HARDWARE_ID'],
                'sensor_type' : details['HARDWARE_TYPE'],
                'hardware_uid' : details['HARDWARE_UID'],
                'location' : details['HARDWARE_DETAIL'],
                'timestamp' : details['INCIDENT_TIME'],
                'status' : incident_status,
                'handler' : handler,
                'urgency_vis_1' : 'visible',
                'urgency_vis_2' : 'visible',
                'urgency_vis_3' : 'visible' if urgency=='critical' else 'hidden',
                'users' : users_names,
                'users_amount' : len(users_names)}

    def post(self):
        """
        Receives POST requests with action type
        """
        print("[BDPIncidentRespond] post request received")
        try:
            request_json : request.get_json(force=True)
            nid = str(request.referrer).split('?')[1][4:]

            action = request_json['ACTION']

            notification = bdp_dbutil.getNotificationByNotificationID(nid)
            user = bdp_dbutil.getUserByUserID(notification["USER_ID"])

            if notification['RESPONSE'] is not None and action == 'SNOOZE':
                return {'result': 'You already have already responded to this incident'}, 208
            
            bdp_dbutil.insertResponderToIncidentID(notification["INCIDENT_ID"], user["USER_ID"])

            notification = {
                "ACTION": action,
                "RESPONDER": user["USER_NAME"],
                "NOTIFICATION_ID": nid,
                "INCIDENT_ID": notification["INCIDENT_ID"],
                "TENANT_ID": user["TENANT_ID"]
            }

            BDPNotifier.notify(notification, user["TENANT_ID"])

            return {"result":"OK"}, 200
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400
