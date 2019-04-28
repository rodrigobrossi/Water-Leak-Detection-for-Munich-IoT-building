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
from bdp_property import BDPProperty
import ibm_db
from bdp_dbutil import *

from bdp_auth import BDPAuth
auth = HTTPBasicAuth()

authF = BDPAuth()


class BDPTenant(Resource):

    @auth.login_required
    def post(self):
        try:
            conn = BDPDBConnection.getInstance().getDBConnection()
            jsonbody = request.get_json(force=True)
            print(jsonbody)
            sql_string = "insert into " + BDPProperty.getInstance().getValue('db_admin_user') + ".BDP_TENANT (TENANT, TENANT_NAME) values ('" + jsonbody['TENANT'] + "', '" + jsonbody['TENANT_NAME'] + "')";
            stmt = ibm_db.exec_immediate(conn, sql_string)
            content = {'tenant':'created'}
            if ibm_db.num_rows(stmt) == 0:
                content = {'result':'failed to create tenant'}
            return content
        except Exception as e:
            print(e)
            return {"result":"fail to create tenant", "msg": str(e)}, 400


    @auth.verify_password
    def verify(username, password):
        print("BDPIncident called")
        return authF.auth(username, password)
    
    def postValidation(self, jsonbody):
        print(jsonbody)
        return True
