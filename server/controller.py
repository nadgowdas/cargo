# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

import json
from string import Template
import requests
import pdb
import logging

import common.codes as codes
from store import dbclient
import restClient as rclient

GET_CONTAINERS = Template("http://$HOST:$PORT/containers")
DOCKER_HOME = '/var/lib/docker'

class RequestHandler():
    def __init__(self, config):
        self.dbclient = dbclient.DBClient(config) 

    def register(self, agent):
        agentCfg = json.loads(agent)    
        agentip = agentCfg["ip"]
        agentport = agentCfg["port"]
        agentid = agentCfg["id"]
        return self.dbclient.storeAgent(agentip, agentport, agentid)
   

    def __get_agents(self):
        rc, agentList = self.dbclient.getAllAgents()
        return agentList      

    def getAllContainers(self):
        agentList = self.__get_agents()
        containerMap = dict()
        rc = codes.SUCCESS 
        for agent in agentList:
            agentip = str(agentList[agent]["ip"])
            agentport = int(agentList[agent]["port"])
            clientUrl = GET_CONTAINERS.substitute(HOST = agentip, PORT = agentport)
            headers = {"content-type": "application/json"}
            payload = dict()
            try:
                resp = requests.get(clientUrl, data=json.dumps(payload), headers=headers)
            except requests.exceptions.ConnectionError as e:
                logging.error("Can not connect to cargo agent at: {}".format(agent))
                rc = codes.FAILED
                pass

            else:
                if resp.status_code == codes.herror(codes.SUCCESS):
                        containerMap[agent] = json.loads(resp.content)   

        return (rc, json.dumps(containerMap))


    def migrate(self, migrateReq):
        rc = codes.SUCCESS
        try:
            source = migrateReq["source"]
            target = migrateReq["target"]
            containerName = migrateReq["container"]
            migRootfs = migrateReq.get("rootfs", False)
        except KeyError as err:
            logging.error("Invalid request: {}".format(migrateReq)) 
            rc  = codes.INVALID_REQ
            return rc
        
        # get source/target agent meta
        rc, sourceAgent = self.dbclient.getAgent(source)
        if rc != codes.SUCCESS:
            return rc
        
        rc, targetAgent = self.dbclient.getAgent(target)
        if rc !=  codes.SUCCESS:
            return rc

        # get container meta from source 
        rc, containerMeta = rclient.inspectContainer(sourceAgent["ip"], sourceAgent["port"], containerName)
        if rc != codes.SUCCESS:
            return rc

        # update start time in db
        mounts = containerMeta.get("Mounts", [])
        if len(mounts) == 0:
            logging.info("No data volumes found for container {}".format(containerName))

        newVolList = []
        #pdb.set_trace()
        volcnt = 1
        for contVol in mounts:
            hostVol = contVol["Source"]
            #mountMap["Source"] = hostVol
            #mountMap["Destination"] = contVol
            #mountMap["Mode"] = ""
            #mountMap["RW"] = containerMeta["VolumesRW"][contVol]
            #volList.append(mountMap)

            rc, nfsMeta = rclient.isNFSMounted(sourceAgent["ip"], sourceAgent["port"], hostVol)
            if rc != codes.SUCCESS:
                logging.error("NFS mount check {} failed".format(hostVol))
                return rc
            if nfsMeta and nfsMeta["is_nfs_mounted"]:
                rc = rclient.nfsImportVolume(targetAgent["ip"], targetAgent["port"], nfsMeta, hostVol)
                if rc != codes.SUCCESS:
                    logging.error("NFS import failed for volume {}".format(hostVol))
                    return rc
                logging.info("Volume {} successfully imported at the target".format(hostVol))
                contVol["isNFS"] = True

            else:        
                rc = rclient.exportVolume(sourceAgent["ip"], sourceAgent["port"], hostVol)
                logging.debug("Exporting volume {} from source {}".format(hostVol, sourceAgent["ip"]))
                if rc != codes.SUCCESS:
                    logging.error("Exporting volume {} failed".format(hostVol))
                    return rc
           
                logging.debug("Volume {} exported successfully".format(hostVol))
            
                logging.debug("Importing volume {} at the target {}".format(hostVol, targetAgent["ip"])) 
                rc = rclient.importVolume(targetAgent["ip"], targetAgent["port"], sourceAgent["ip"], hostVol, containerName, volcnt, False)
                contVol["Source"] = volcnt
                
                if rc != codes.SUCCESS:
                    logging.error("Importing volume {} failed".format(hostVol))
                    return rc
                 
                contVol["isNFS"] = False
                logging.debug("Volume imported at target successfully")     
                rc = rclient.startLazycopy(targetAgent["ip"], targetAgent["port"], containerName, hostVol, volcnt, sourceAgent["ip"])
                if rc != codes.SUCCESS:
                    logging.error("Error starting lazy copy on target {}".format(targetAgent["ip"]))
                    return rc

                volcnt+=1

            newVolList.append(contVol)
       
        containerMeta["Mounts"] = newVolList
        rc = rclient.createContainer(targetAgent["ip"], targetAgent["port"], containerMeta)
        if rc != codes.SUCCESS: 
            logging.error("Error starting container on target {}".format(targetAgent["ip"]))
            return rc
    
        if migRootfs:
            rc = rclient.exportVolume(sourceAgent["ip"], sourceAgent["port"], DOCKER_HOME_DIR)
            if rc != codes.SUCCESS:
                return rc
            
            rc = rclient.importVolume(targetAgent["ip"], targetAgent["port"], sourceAgent["ip"], containerName, True)
            if rc != codes.SUCCESS:
                return rc
                
        rc = rclient.startContainer(targetAgent["ip"], targetAgent["port"], containerName)
        if rc != codes.SUCCESS: 
            logging.error("Error starting container on target {}".format(targetAgent["ip"]))
            return rc

        rc = rclient.stopContainer(sourceAgent["ip"], sourceAgent["port"], containerName)
        if rc != codes.SUCCESS: 
            logging.error("Error stopping container on source {}".format(sourceAgent["ip"]))
            return rc
        

        return codes.SUCCESS    
        
    
    def updateStatus(self, container, payload):
        payloadJson = json.loads(payload)
        total = payloadJson["total"]
        current = payloadJson["current"]
        timestamp = payloadJson["timestamp"]
        completed = payloadJson["completed"]

        self.dbclient.updateStatus(container, timestamp, total, current, completed)
        return codes.SUCCESS
        #return rclient.stopLazyCopy(agentip, agentport, container, volume)

    def getStatus(self, container):
        rc, status = self.dbclient.getStatus(container)
        if rc != codes.SUCCESS:
            logging.error("Container status not found")
            return rc, ""
        else:
            return rc, json.dumps(status)

    def doFailover(self, nodeid, container):
        rc, agentMeta = self.dbclient.getAgent(nodeid)
        if rc != codes.SUCCESS:
            logging.error("Agent not found")
            return rc
        agentip = str(agentMeta["ip"])
        agentport = int(agentMeta["port"])
        rc = rclient.failover(agentip, agentport, container)
        return rc 

