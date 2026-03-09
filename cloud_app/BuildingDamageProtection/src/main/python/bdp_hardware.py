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
from flask import Response
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask import request
from flask import json
import ibm_db
import bdp_dbutil
from bdp_dbutil import *

from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()


class BDPHardware(Resource):

    @auth.login_required
    def post(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            jsonbody = request.get_json(force=True)
            print("[BDPHardware] POST request received: {}".format(jsonbody))

            sql_string = "INSERT INTO " + bdp_dbutil.getTableName("BDP_HARDWARE") + " (HARDWARE_ID, HARDWARE_TYPE, HARDWARE_DETAIL, TENANT_ID) SELECT '" 
            sql_string += jsonbody['HARDWARE_ID'] + "', '" + jsonbody['HARDWARE_TYPE'] + "', '" + jsonbody['HARDWARE_DETAIL'] + "', " 
            sql_string += "TENANT_ID FROM " + bdp_dbutil.getTableName("BDP_TENANT") + " WHERE TENANT = '"+ jsonbody['TENANT'] + "'"
            print("[BDPHardware] Injecting to DB: {}".format(sql_string))
            
            stmt = ibm_db.exec_immediate(conn, sql_string)
            content = {'harware':'added'}
            if ibm_db.num_rows(stmt) == 0:
                content = {'result':'failed to add hardware'}
                
            return content

        except Exception as e:
            print(e)
            return {"result":"failed to add hardware", "msg": str(e)}, 400


    @auth.verify_password
    def verify(username, password):
        print("BDPIncident called")
        return authF.auth(username, password)
    
    def postValidation(self, jsonbody):
        print(jsonbody)
        return True
