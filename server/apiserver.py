#!/usr/bin/env python

#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

"""
This server is hosted with Flask framework.

"""

import sys
import optparse
import logging
import os
import socket
import ConfigParser
import pdb
import json
import commands

try:
    from flask import Flask, request
    from flask.ext.restful import reqparse, abort, Api, Resource
    from flask.helpers import make_response
except ImportError:
    print "flask module isn't installed on this machine. To get flask, run:"
    print "sudo apt-get install python-dev python-pip"
    print "sudo pip install Flask"
    sys.exit(1)
    
import common.codes as codes
import controller 

app = Flask(__name__)
api = Api(app)

reqHandler = None

parser = reqparse.RequestParser()
parser.add_argument('nodeid', type=str)
parser.add_argument('containerid', type=str)

class CargoHandler(Resource):
    def get(self):
        rc, msg = reqHandler.getAllContainers()
        return make_response(msg, codes.herror(rc))
            
    def post(self):
        migreq  = json.loads(request.data)
        rc = reqHandler.migrate(migreq)
        return make_response("", codes.herror(rc))
    
class AgentHandler(Resource):
    def post(self):
        agent = request.data
        rc = reqHandler.register(agent)
        return make_response("", codes.herror(rc))

    def delete(self):
        return make_response("", 200)
	
class CargoStatusHandler(Resource):
    def get(self, containerid):
        rc, msg = reqHandler.getStatus(containerid)
        return make_response(msg, codes.herror(rc))

    def post(self, containerid):
        payload = request.data
        rc = reqHandler.updateStatus(containerid, payload)
        return make_response("", codes.herror(rc))

class FailoverHandler(Resource):
    def post(self, nodeid, containerid):
        rc = reqHandler.doFailover(nodeid, containerid)
        return make_response("", codes.herror(rc))


api.add_resource(AgentHandler, '/register')
api.add_resource(CargoHandler, '/cargo')
api.add_resource(CargoStatusHandler, '/cargo/replication/<string:containerid>')
api.add_resource(FailoverHandler, '/cargo/failover/<string:nodeid>/<string:containerid>')

if __name__ == '__main__':
    usage = "usage: python %prog --config <config file>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--config", action="store", dest="config", default="./config.cfg", 
                      help="Config File(default=./config.cfg)")

    '''
    usage = "usage: python %prog -n <Host IP> -p <port> -c <config file> -l <logfile path>"

    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-n", "--node", action="store", dest="node", default="127.0.0.1", 
                      help="Node IP Address(default=127.0.0.1)")
    parser.add_option("-p", "--port", action="store", dest="port", default="5000", 
                      help="Node port(default=5000)")
    parser.add_option("-c", "--config", action="store", dest="config", default="./config.cfg", 
                      help="Config File(default=./config.cfg)")
    parser.add_option("-l", "--logfile", action="store", dest="logfile", 
                      default="/var/log/cargo.log", 
                      help="Log file path(default=/var/log/cargo.log)")
    
    host = opts.node
    port = opts.port
    logfile = opts.logfile
    '''
    
    opts,args= parser.parse_args()
    cfg = dict()
    cfgfile = opts.config

    config = ConfigParser.RawConfigParser()
    config.read(cfgfile)
    cfg["dbserver"] = config.get('etcd','server')
    cfg["dbport"] = config.get('etcd','port')

    interface = config.get('global','interface')
    port = config.get('global','port')
    logfile = config.get('global','logfile')

    ipaddr = commands.getoutput("/sbin/ifconfig %s"%(interface)).split("\n")[1].split()[1][5:]
    if not os.path.exists(os.path.dirname(logfile)):
        print "Invalid log file path"
        parser.print_help()
        sys.exit(1)
    
    logging.basicConfig(filename=logfile, level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug("Starting server on host address:{} and Port:{}".format(ipaddr, port))
    reqHandler = controller.RequestHandler(cfg)
    print "Starting cargo server on %s:%s"%(ipaddr, port)

    try:
        app.run(
            host=ipaddr,
            port=int(port),
            threaded=True
        )
    except socket.error, msg:
        logging.error("Error starting the server. Error[%s]"%(msg[1]))
        print "Error starting server. Please check the logs at %s"%(logfile)


