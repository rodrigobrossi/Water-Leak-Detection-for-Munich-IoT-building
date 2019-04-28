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
from flask import request
from flask import json
from flask_httpauth import HTTPBasicAuth

from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()

class BDPIncidentRespond(Resource):

    @auth.login_required
    def get(self):
        try:
            content = {'user action':'received'}
            action = request.args.get('action')
            print(action)
            nid = request.args.get('nid')
            print(nid)
#todo
#1. using nid to find the notification record
#2. using notification field to find incident record
#3. update the record using with response field
#needs to update the response field in the notification record. response field is a json format ["action(snooze/fix)":timestamp]
#4. update incident record

            return content
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

    @auth.verify_password
    def verify(username, password):
        print("BDPIncidentRespond called")
        return authF.auth(username, password)
