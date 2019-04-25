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


from bdp_auth import AIAuth
#from ai_sysinit import AISysInit
#import psycopg2
from threading import Thread
from time import sleep

from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from bdp_property import AIProperty

app = Flask(__name__)
api = Api(app)
#auth = HTTPBasicAuth()
#authF = AIAuth()

class AIEngineGateway(Resource):
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
    
api.add_resource(AIEngineGateway, '/')

#app.run(ssl_context='adhoc', host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))
#app.run(host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))
#app.run(threaded=True, ssl_context=(AIProperty.getInstance().getValue('https_cert'), AIProperty.getInstance().getValue('https_key')), host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))

if 'flask' == AIProperty.getInstance().getValue('server_type'):
    app.run(ssl_context=(AIProperty.getInstance().getValue('https_cert'), AIProperty.getInstance().getValue('https_key')), host='0.0.0.0', port=int(AIProperty.getInstance().getValue('server_port')))
else:
    http_server = WSGIServer(('0.0.0.0', int(AIProperty.getInstance().getValue('server_port'))), app, keyfile=AIProperty.getInstance().getValue('https_key'), certfile=AIProperty.getInstance().getValue('https_cert'))
    http_server.serve_forever()

