# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

"""

import pdb
import dockerclient
import fsclient
import json
from string import Template
import os
import signal
import subprocess
import logging

import codes 
import utils

START_LAZY_COPY_CMD = Template("python $PWD/replicator/manager.py --mondir $MON_DIR --nfsdir $NFS_DIR --srcdir $SRC_DIR \
    --destdir $DEST_DIR --srchost $SRC_HOST --container $CONTAINER --server $CARGO_SERVER --volumeid  $VOLUMEID \
    --agentid $AGENTID")

class RequestRouter():
    def __init__(self, config):
        self.containerClient = dockerclient.DockerClient(config["dockerurl"])
        self.fsClient = fsclient.FilesystemClient()
        #self.replicator = Replicator()

    def getAllContainers(self):
        return self.containerClient.listContainers()
         
    
    def getContainer(self, containerId):
        return self.containerClient.inspectContainer(containerId)
        
    def handleFSOp(self, configRaw):
        config = json.loads(configRaw)
        if config["role"] == "source" and config["opcode"] == "EXPORT_FS":
            return self.fsClient.nfsExport(config["params"])
        elif config["role"] == "target" and config["opcode"] == "IMPORT_FS":    
            return self.fsClient.prepareTargetFS(config["params"])
        elif config["role"] == "source" and config["opcode"] == "CHECK_NFS":
            return self.fsClient.checkAndGetNFSMeta(config["params"])
        elif config["role"] == "target" and config["opcode"] == "IMPORT_NFS":
            return self.fsClient.mountNFSVolume(config["params"])


    def _createContainer(self, config):
        return self.containerClient.create(config)

    def _startContainer(self, containerId):
        return self.containerClient.start(containerId)

    def _stopContainer(self, containerId):
        return self.containerClient.stop(containerId)

        
    def handleContainerOp(self, payload, containerId):
        reqData = json.loads(payload)
        opcode = reqData["opcode"]
        if opcode == "create":
            return self._createContainer(reqData["params"])
        elif opcode ==  "start":
            return self._startContainer(containerId) 
        elif opcode ==  "stop": 
            return self._stopContainer(containerId)
        else:
            return codes.BAD_REQ

    def deleteContainer(self, containerId):
        print "TODO"

    def startReplication(self, containerId, volumeId, nodeId, cargoServer, payload):
        payloadJson = json.loads(payload)
        srchost = payloadJson["srchost"]
        volume = payloadJson["volume"]
        volcnt = payloadJson["volcnt"]
        mondir = utils.getCOWDir(containerId, volcnt)
        lzcopydir = utils.getLazyCopyDir(containerId, volcnt)        
        nfsdir = utils.getNFSMountDir(containerId, volcnt)

        cmd = START_LAZY_COPY_CMD.substitute(PWD = os.getcwd(), MON_DIR = mondir, NFS_DIR = nfsdir, SRC_DIR = volume, \
            DEST_DIR = lzcopydir, SRC_HOST = srchost, CONTAINER = containerId,\
            CARGO_SERVER = cargoServer, VOLUMEID = volumeId, AGENTID = nodeId)
       
        svcName = utils.createReplSvc(containerId, volumeId, cmd)
        rc, output = utils.startSvc(svcName)
        if rc != codes.SUCCESS :
            logging.error("Error starting replication service %s: %s"%(svcName, output))
        else:
            logging.debug("Replication service %s started successfully"%(svcName))
        
        return rc

    def doFailover(self,containerId):
        rc = self._stopContainer(containerId)
        if rc != codes.SUCCESS:
            return rc

        rc  = self.fsClient.failoverVolumes(containerId)
        if rc != codes.SUCCESS:
            return rc
        
        rc = self._startContainer(containerId)
        if rc != codes.SUCCESS:
            return rc

        return rc
