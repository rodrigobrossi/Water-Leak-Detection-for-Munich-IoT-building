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

from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()

class BDPIncidentRespond2(Resource):

    def get(self):
        try:
            resp = make_response(render_template('respond.html'))
            resp.headers['Content-type'] = 'text/html; charset=utf-8'
            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

    def post(self):
        try:
            resp = make_response(render_template('respond_ok.html'))
            resp.headers['Content-type'] = 'text/html; charset=utf-8'
            return resp
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400
