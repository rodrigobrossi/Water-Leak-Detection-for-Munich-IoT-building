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
from flask import request
from flask import json

class BDPIncidentRespond(Resource):

    def get(self):
        try:
            content = {'user action':'received'}

            return content
        except Exception as e:
            print(e)
            return {"result":"fail", "msg": str(e)}, 400

