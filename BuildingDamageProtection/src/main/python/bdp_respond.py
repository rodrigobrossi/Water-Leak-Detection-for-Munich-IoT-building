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

    def get(self):
        try:
            nid = request.args.get('nid')
            notification = bdp_dbutil.getNotificationByNotificationID(nid)
            user = bdp_dbutil.getUserByUserID(notification["USER_ID"])

            incident_id = bdp_dbutil.getNotificationByNotificationID(nid)["INCIDENT_ID"]
            incident = bdp_dbutil.getIncidentByIncidentID(incident_id)
            print('[BDPIncidentRespond] {}'.format(incident))
            # TODO: Fix original incident assignment
            #original_incident = bdp_dbutil.getIncidentByIncidentID(conn, incident['INCIDENT_ID_ORIGINAL'])
            original_ts = incident['INCIDENT_TIME']

            tenant = bdp_dbutil.getTenantByTenantID(incident['TENANT_ID'])
            tenant_name = tenant['TENANT_NAME']

            users_group = bdp_dbutil.getAllUsers(tenant['TENANT_ID'])

            users_names = []
            for user in users_group:
                users_names.append(user['USER_NAME'])

            status_code = {
                1: 'Resolved',
                2: 'New',
                3: 'In progress'
            }

            incident_status = status_code[incident['INCIDENT_STATUS_CODE']]
            incident_detail = json.loads(incident['INCIDENT_DETAIL'])
            urgency = incident_detail['URGENCY']
            hardware = bdp_dbutil.getHardwareByHardwareUID(incident_detail['HARDWARE_UID'])

            handler = 'Not assigned'
            if 'RESPONDER' in incident_detail.keys():
                handler_id = incident_detail['RESPONDER']
                handler = bdp_dbutil.getUserByUserID(handler_id)['USER_NAME']

            bdp_util.createPlot(incident_detail['HARDWARE_UID'])

            resp = make_response(render_template('respond.html', 
                                                name = user['USER_NAME'],
                                                tenant = tenant_name,
                                                sensor_id = hardware['HARDWARE_ID'],
                                                sensor_type = hardware['HARDWARE_TYPE'],
                                                hardware_uid = hardware['HARDWARE_UID'],
                                                location = hardware['HARDWARE_DETAIL'],
                                                timestamp = original_ts,
                                                status = incident_status,
                                                handler = handler,
                                                urgency_vis_1 = 'visible',
                                                urgency_vis_2 = 'visible',
                                                urgency_vis_3 = 'visible' if urgency=='critical' else 'hidden',
                                                users = users_names,
                                                users_amount = len(users_names)
                                                ))
            resp.headers['Content-type'] = 'text/html; charset=utf-8'

            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

    def post(self):
        print("[BDPIncidentRespond] post request received")
        try:
            request_json = request.get_json(force=True)
            nid = str(request.referrer).split('?')[1][4:]

            action = request_json['ACTION']

            notification = bdp_dbutil.getNotificationByNotificationID(nid)
            user = bdp_dbutil.getUserByUserID(notification["USER_ID"])

            if notification['RESPONSE'] is not None:
                return {'result': 'You already have already responded to this incident'}, 400
            
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
