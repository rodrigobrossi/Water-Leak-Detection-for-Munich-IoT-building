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
import os 
import sys
import pprint
import time
import datetime
from flask import Response, render_template, make_response
from flask import Flask
from flask_restful import Resource, Api
from flask import request
from flask import json
from flask_httpauth import HTTPBasicAuth
from bdp_dbutil import *
from bdp_util import *
from bdp_property import BDPProperty

from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()

class BDPIncidentRespond(Resource):

    def get(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            nid = request.args.get('nid')
            notificationJson = getNotificationByNotificationID(conn, nid)
            userJSON = getUserByUserID(conn, notificationJson["USER_ID"])
            resp = make_response(render_template('respond.html', contact = userJSON["USER_CONTACT_1"], nid = nid))
            resp.headers['Content-type'] = 'text/html; charset=utf-8'
            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

    def post(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            resp = make_response(render_template('respond_ok.html'))
            print(request.form['nid'])
            print(request.form['contact'])
            print(request.form['action'])
            nid = request.form['nid']
            action = request.form['action']
            notificationJson = getNotificationByNotificationID(conn, nid)
            userJSON = getUserByUserID(conn, notificationJson["USER_ID"])
            notificationResponseJson = []
            responsestr = notificationJson["RESPONSE"].strip()
            if notificationJson["RESPONSE"] is not None and len(responsestr) != 0 :
                notificationResponseJson = eval(notificationJson["RESPONSE"])
            print(notificationResponseJson)
            now = datetime.datetime.now()
            response = {'time' : now, 'action' : action}
            notificationResponseJson.append(response)
            print(notificationResponseJson)
            updateNotificationResponse(conn, nid, notificationResponseJson)
            
            incidentJSON = getIncidentByIncidentID(conn, notificationJson["INCIDENT_ID"])
            retbool = updateIncidentStatus(conn, notificationJson["INCIDENT_ID"], action)
            if not retbool:
                raise Exception('Not able to update incident status error')
            
            usergroups = getAllUsers(conn, incidentJSON["TENANT_ID"])
            retbool = sendNotificationToUsers(BDPProperty.getInstance().getValue('nodered_endpoint'), usergroups, action, userJSON)
            if not retbool:
                raise Exception('Not able to send ack to all user error')
            resp.headers['Content-type'] = 'text/html; charset=utf-8'
            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400
