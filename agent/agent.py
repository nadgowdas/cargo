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
import requests
import urllib
from string import Template
import json
import commands
import uuid

try:
    from flask import Flask, request
    from flask.ext.restful import reqparse, abort, Api, Resource
    from flask.helpers import make_response
except ImportError:
    print "flask module isn't installed on this machine. To get flask, run:"
    print "sudo apt-get install python-dev python-pip"
    print "sudo pip install Flask"
    sys.exit(1)
    
import codes
import controller


app = Flask(__name__)
api = Api(app)

reqHandler = None
cargoServer = None

parser = reqparse.RequestParser()
parser.add_argument('containerId', type=str)
parser.add_argument('volumeId', type=str)

REGISTER_URL = Template("http://$HOST:$PORT/register")
CONFIG_DIR = "/var/lib/cargo"
AGENT_IDFILE = "agent.id"

class ContainersHandler(Resource):
    def get(self):
        rc, msg = reqHandler.getAllContainers()
        return make_response(json.dumps(msg), codes.herror(rc))
            
    
class ContainerHandler(Resource):
    def get(self, containerId):
        rc, msg = reqHandler.getContainer(containerId)
        return make_response(msg, codes.herror(rc))

    def post(self, containerId):
        reqData = request.data
        rc = reqHandler.handleContainerOp(reqData, containerId)
        return make_response("", codes.herror(rc))

    def delete(self):
        rc = reqHandler.deleteContainer(None, containerId)
        return make_response("", 200)
	
class FilesystemHandler(Resource):
    def get(self):
        config = request.data
        rc, msg = reqHandler.handleFSOp(config)
        return make_response(json.dumps(msg), codes.herror(rc))

    def post(self):
    	config = request.data
        rc = reqHandler.handleFSOp(config)
        return make_response("", codes.herror(rc))

class ReplicationHandler(Resource):
    def post(self, containerId, volumeId):
        payload = request.data
        idfile = os.path.join(CONFIG_DIR, AGENT_IDFILE)
        with open(idfile, 'r') as infile:        
            for line in infile:
                nodeId = line

        rc = reqHandler.startReplication(containerId, volumeId, nodeId, cargoServer, payload)
        return make_response("", codes.herror(rc))
    
    def delete(self, containerId, volumeId):
        rc = reqHandler.stopReplication(containerId, volumeId)
        return make_response("", codes.herror(rc))

class FailoverHandler(Resource):
    def post(self, containerId):
        rc = reqHandler.doFailover(containerId)
        return make_response("", codes.herror(rc))


api.add_resource(ContainersHandler, '/containers')
api.add_resource(ContainerHandler, '/container/<string:containerId>')
api.add_resource(FilesystemHandler, '/fs')
api.add_resource(FailoverHandler, '/failover/<string:containerId>')
api.add_resource(ReplicationHandler, '/replication/<string:containerId>/<string:volumeId>')


def register(cargohost, cargoport, serverip, serverport, serverid):
    url = REGISTER_URL.substitute(HOST = cargohost, PORT = cargoport)
    headers = {"content-type": "application/json"}
    payload = dict()
    payload['ip'] = serverip
    payload['port'] = serverport
    payload['id'] = serverid
    try:
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        return 0
            
    if resp.status_code == 200:
        return 1
    else:
        return 0        

if __name__ == '__main__':

    usage = "usage: python %prog -c <config file>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--config", action="store", dest="config", default="./config.cfg", 
                      help="Config File(default=./config.cfg)")

    opts,args= parser.parse_args()
    cfgfile = opts.config

    '''
    usage = "usage: python %prog -n <Host IP> -p <port> -c <config file> -l <logfile path>"

    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-n", "--node", action="store", dest="node", default="127.0.0.1", 
                      help="Node IP Address(default=127.0.0.1)")
    parser.add_option("-i", "--nodeid", action="store", dest="nodeid", 
                      help="Node Identidier")
    parser.add_option("-p", "--port", action="store", dest="port", default="5000", 
                      help="Node port(default=5000)")
    parser.add_option("-c", "--config", action="store", dest="config", default="./config.cfg", 
                      help="Config File(default=./config.cfg)")
    parser.add_option("-l", "--logfile", action="store", dest="logfile", 
                      default="/var/log/cargo_agent.log", 
                      help="Log file path(default=/var/log/cargo_agent.log)")
    
    opts,args= parser.parse_args()
    host = opts.node
    port = opts.port
    nodeid = opts.nodeid
    logfile = opts.logfile
    cfgfile = opts.config
    cfg = dict()
    '''

    cfg = dict()
    config = ConfigParser.RawConfigParser()
    config.read(cfgfile)
    cfg["cargoip"] = config.get('cargo-server','ipaddr')
    cfg["cargoport"] = config.get('cargo-server','port')
    cfg["dockerurl"] = config.get('docker-config', 'URL')
    
    interface = config.get('global','interface')
    port = config.get('global','port')
    logfile = config.get('global','logfile')

    ipaddr = commands.getoutput("/sbin/ifconfig %s"%(interface)).split("\n")[1].split()[1][5:]

    if not os.path.exists(os.path.dirname(logfile)):
        print "Invalid log file path"
        parser.print_help()
        sys.exit(1)
   
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    idfile = os.path.join(CONFIG_DIR, AGENT_IDFILE)
    if not os.path.exists(idfile):
        nodeid = str(uuid.uuid4())
        with open(idfile, 'w') as outfile:
            outfile.write(nodeid)
    else:
        with open(idfile, 'r') as infile:        
            for line in infile:
                nodeid = line
    
    logging.basicConfig(filename=logfile, level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug("Starting agent on host address:{} and Port:{}".format(ipaddr, port))
    print ("Starting agent on host address:{} and Port:{}".format(ipaddr, port))

    if not register(cfg["cargoip"], cfg["cargoport"], ipaddr, port, nodeid):
        logging.error("Can not register to the cargo server.")
        logging.error("Abandon agent start.")
        print "Registration to cargo server failed. Agent not started"
        sys.exit(1)
    
    reqHandler = controller.RequestRouter(cfg)
    #global cargoServer
    cargoServer = "%s:%s"%(cfg["cargoip"], cfg["cargoport"])

    try:
        app.run(
            host=ipaddr,
            port=int(port),
            threaded=True
        )
    except socket.error, msg:
        logging.error("Error starting the server. Error[%s]"%(msg[1]))
        print "Error starting server. Please check the logs at %s"%(logfile)


