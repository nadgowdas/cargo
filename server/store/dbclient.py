# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

"""

This is a Database client to store/fetch cargo metadata
"""

from common import codes
import etcd
import json
import logging
import pdb

class DBClient():
    def __init__(self, config):
        server = config['dbserver']
        port = config['dbport']
        self.client = etcd.Client(host=server, port=int(port))
        
    def storeAgent(self, agentip, agentport, agentid):
        agentProp = dict()
        key = "/agent/{}".format(agentid)
        agentProp["ip"] = agentip
        agentProp["port"]= agentport
        self.client.write(key, json.dumps(agentProp))
        return codes.SUCCESS

    def getAllAgents(self):
        key = "/agent"
        agents = self.client.read(key, recursive=True, sorted=True)
        agentsMap = dict()
        for child in agents.children:
             agentsMap[child.key] = json.loads(child.value)
  
        return (codes.SUCCESS, agentsMap)
         
    def getAgent(self, agentid):
        key = "/agent/{}".format(agentid)
        agentMeta = dict()
        rc = codes.SUCCESS

        try:
            agent = self.client.read(key)
        except etcd.EtcdKeyNotFound as err:
            logging.error("Agent {} not found".format(agentid)) 
            rc = codes.AGENT_NOT_FOUND
        else:
            agentMeta = json.loads(agent.value)

        return (rc, agentMeta)

    def updateStatus(self, conainerid, ts, total, curr, completed):
        key = "/status/{CONTAINER}".format(CONTAINER = conainerid)
        status = dict()
        started = False
        try:
            value = self.client.read(key)
        except etcd.EtcdKeyNotFound as err:
            logging.info("Update for new container") 
            started = True
            pass
        else:
            status = json.loads(value.value)
       
        if started:
            status["start"] = ts
            status["update"] = ""
            status["complete"] = ""
        elif not started and not completed:
            status["update"] = ts
        elif completed:
            status["complete"] = ts
            
        status["total"] = total
        status["curr"] = curr
        status["completed"] = completed
        if started:
            self.client.write(key, json.dumps(status))
        else:
            value.value = json.dumps(status)
            self.client.update(value)
        return codes.SUCCESS

    def getStatus(self, conainerid):
        key = "/status/{CONTAINER}".format(CONTAINER = conainerid)
        status = dict()
        rc = codes.SUCCESS
        try:
            result = self.client.read(key)
        except etcd.EtcdKeyNotFound as err:
            logging.error("Status {} not found".format(conainerid)) 
            rc = codes.AGENT_NOT_FOUND
        else:
            status = json.loads(result.value)
        return (rc, status)

