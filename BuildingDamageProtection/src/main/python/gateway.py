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

#design doc: https://ibm.ent.box.com/file/293956264729
import os 
import sys
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer
from importlib import reload
gevent.monkey.patch_all()
reload(sys)
#sys.setdefaultencoding('utf8')
sys.dont_write_bytecode = True


from bdp_auth import BDPAuth
#from ai_sysinit import AISysInit
#import psycopg2
from threading import Thread
from time import sleep

from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from bdp_property import BDPProperty
from bdp_incident import BDPIncident
from bdp_respond import BDPIncidentRespond

app = Flask(__name__)
api = Api(app)
#auth = HTTPBasicAuth()
#authF = AIAuth()

class BDPGateway(Resource):
    def get(self):
        return {'Building Damage Protection': 'alive'}

#sysInit = AISysInit()
#sysInit.init()

'''def startScheduler():
    periodic_scheduler = AIServiceInit()  
    periodic_scheduler.setup()
    periodic_scheduler.run()

thread1 = Thread(target = startScheduler, args = ())
thread1.start()
'''
    
api.add_resource(BDPGateway, '/')
api.add_resource(BDPIncident, '/incident')
api.add_resource(BDPIncidentRespond, '/respond')

#app.run(ssl_context='adhoc', host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))
#app.run(host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))
#app.run(threaded=True, ssl_context=(AIProperty.getInstance().getValue('https_cert'), AIProperty.getInstance().getValue('https_key')), host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))

if 'flask' == BDPProperty.getInstance().getValue('server_type'):
    app.run(ssl_context=(BDPProperty.getInstance().getValue('https_cert'), BDPProperty.getInstance().getValue('https_key')), host='0.0.0.0', port=int(BDPProperty.getInstance().getValue('server_port')))
else:
    http_server = WSGIServer(('0.0.0.0', int(BDPProperty.getInstance().getValue('server_port'))), app, keyfile=BDPProperty.getInstance().getValue('https_key'), certfile=BDPProperty.getInstance().getValue('https_cert'))
    http_server.serve_forever()

