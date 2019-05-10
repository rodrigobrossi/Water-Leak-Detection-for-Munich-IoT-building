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
from bdp_dbutil import *


from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()

class BDPNotifier(Resource):

    @auth.login_required
    def post(self):
        try:
            #TODO Store sensor data in a temp storage
            jsonbody = request.get_json(force=True)
            print('Sensor data received {}'.format(jsonbody))

            if 'humidity' not in jsonbody.keys():
                return {"result":"failed to save values, missing humidity value"}, 400

            return self.getResponse(jsonbody['humidity'], jsonbody['deviceId'])
        except Exception as e:
            print(e)
            return {"result":"failed to save values", "msg": str(e)}, 400

    @auth.verify_password
    def verify(username, password):
        print("BDPIncident called")
        return authF.auth(username, password)
    
    def postValidation(self, jsonbody):
        print(jsonbody)
        return True
    
    def getResponse(self, value, hardware):
        if value < 50:
            return {"result": "OK"}, 204
        elif value < 75: 
            return {"result": {"urgency": "significant", "hardware": hardware}}, 200
        return {"result": {"urgency": "critical", "hardware": hardware}}, 200
        