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


from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()


class BDPIncident(Resource):

    @auth.login_required
    def post(self):
        try:
            jsonbody = request.get_json(force=True)
            print(jsonbody)
            content = {'incident':'created'}

    
            return content
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400


    @auth.verify_password
    def verify(username, password):
        print("BDPIncident called")
        return authF.auth(username, password)
