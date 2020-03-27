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

from threading import Thread
from time import sleep

import sys
sys.dont_write_bytecode = True

import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()

from bdp_auth import BDPAuth
from bdp_sysinit import BDPSysInit

from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth

from bdp_property import BDPProperty
from bdp_incident import BDPIncident
from bdp_tenant import BDPTenant
from bdp_user import BDPUser
from bdp_respond import BDPIncidentRespond
from bdp_servicecheck import BDPServiceCheck
from bdp_hardware import BDPHardware

import bdp_util, bdp_dbutil

application = Flask(__name__)
api = Api(application)

class BDPGateway(Resource):
    def get(self):
        return {'Building Damage Protection': 'alive', 'ver': BDPProperty.getInstance().getValue('ver')}

sysInit = BDPSysInit()
sysInit.init()

def startScheduler():
    periodic_scheduler = BDPServiceCheck()  
    periodic_scheduler.setup()
    periodic_scheduler.run()

thread1 = Thread(target = startScheduler, args = ())
thread1.start()

api.add_resource(BDPGateway, '/')
api.add_resource(BDPIncidentRespond, '/respond')
api.add_resource(BDPTenant, '/tenant')
api.add_resource(BDPUser, '/user')
api.add_resource(BDPHardware, '/hardware')

BDPIncident.start()

if __name__ == "__main__":
    server_type = BDPProperty.getInstance().getValue('server_type')
    server_port = int(BDPProperty.getInstance().getValue('server_port'))

    if 'flask' == server_type:
        application.run(threaded=True, host='0.0.0.0', port=server_port)
    elif 'cli' != server_type:
        http_server = WSGIServer(('0.0.0.0', server_port), app, keyfile=BDPProperty.getInstance().getValue('https_key'), certfile=BDPProperty.getInstance().getValue('https_cert'))
        http_server.serve_forever()