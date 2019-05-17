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

import bdp_dbutil
import bdp_util
from bdp_property import BDPProperty

class BDPIncidentRespond(Resource):

    def get(self):
        try:
            conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()
            nid = request.args.get('nid')
            notification = bdp_dbutil.getNotificationByNotificationID(conn, nid)
            user = bdp_dbutil.getUserByUserID(conn, notification["USER_ID"])

            incident_id = bdp_dbutil.getNotificationByNotificationID(conn, nid)["INCIDENT_ID"]
            incident = bdp_dbutil.getIncidentByIncidentID(conn, incident_id)

            # TODO: Fix original incident assignment
            #original_incident = bdp_dbutil.getIncidentByIncidentID(conn, incident['INCIDENT_ID_ORIGINAL'])
            original_ts = incident['INCIDENT_TIME']

            tenant = bdp_dbutil.getTenantByTenantID(conn, incident["TENANT_ID"])['TENANT_NAME']

            status_code = {
                1: 'Fixed',
                2: 'New',
                3: 'Snoozed'
            }
            incident_status = status_code[incident['INCIDENT_STATUS_CODE']]
            incident_detail = json.loads(incident['INCIDENT_DETAIL'])

            resp = make_response(render_template('respond.html', 
                                                name = user['USER_NAME'],
                                                tenant = tenant,
                                                sensor_id = incident_detail['HARDWARE_ID'],
                                                sensor_type = incident_detail['HARDWARE_TYPE'],
                                                location = incident_detail['HARDWARE_DETAIL'],
                                                timestamp = original_ts,
                                                status = incident_status,
                                                handler = 'None'))
            resp.headers['Content-type'] = 'text/html; charset=utf-8'

            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

    def post(self):
        print("[BDPIncidentRespond] post request received")
        try:
            conn = bdp_dbutil.BDPDBConnection.getInstance().getDBConnection()
            resp = make_response(render_template('respond_ok.html'))
            request_json = request.get_json(force=True)
            nid = str(request.referrer).split('?')[1][4:]

            action = request_json['ACTION']

            notification = bdp_dbutil.getNotificationByNotificationID(conn, nid)
            user = bdp_dbutil.getUserByUserID(conn, notification["USER_ID"])
            
            print(notification)
            if notification['RESPONSE'] is not None:
                # TODO: Somebody already answered
                return {'result': 'Something went wrong'}
            
            now = datetime.datetime.now()
            response = {'TIME' : now, 'ACTION' : action}
            bdp_dbutil.updateNotificationResponse(conn, nid, response)
            
            retbool = bdp_dbutil.updateIncidentStatus(conn, notification["INCIDENT_ID"], action)
            if not retbool:
                return {'result': 'Not able to update incident status'}
            
            incident = bdp_dbutil.getIncidentByIncidentID(conn, notification["INCIDENT_ID"])
            users = bdp_dbutil.getAllUsers(conn, incident["TENANT_ID"])
            bdp_dbutil.createNotificationRecord(conn, incident["INCIDENT_ID"], 2, users)

            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400
