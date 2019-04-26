#############################################################
# IBM Confidential
# OCO Source Materials
#
#  (C) Copyright IBM Corp. 2018
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
from flask import Response
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask import request
from flask import json
import ibm_db
from bdp_dbutil import *


from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()


class BDPIncident(Resource):

    @auth.login_required
    def post(self):
        try:
            conn = get_db_connection()
            jsonbody = request.get_json(force=True)
            print(jsonbody)
            sql_string = "INSERT INTO " + BDPProperty.getInstance().getValue('db_admin_user') + ".BDP_INCIDENT (INCIDENT_DETAIL, INCIDENT_TIME, INCIDENT_STATUS_CODE, TENANT_ID) SELECT '" + json.dumps(jsonbody['INCIDENT_DETAIL']) + "', '" + jsonbody['INCIDENT_TIME'] + "', 2, TENANT_ID FROM LKR34911.BDP_TENANT WHERE TENANT = '"+ jsonbody['TENANT'] + "'"
            print(sql_string)
            stmt = ibm_db.exec_immediate(conn, sql_string)
            content = {'incident':'created'}
            if ibm_db.num_rows(stmt) == 0:
                content = {'result':'failed to create incident'}

            return content
        except Exception as e:
            print(e)
            return {"result":"failed to create incident", "msg": str(e)}, 400


    @auth.verify_password
    def verify(username, password):
        print("BDPIncident called")
        return authF.auth(username, password)
    
    def postValidation(self, jsonbody):
        print(jsonbody)
        return True
