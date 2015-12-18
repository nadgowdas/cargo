#
#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


import os
import sys
from threading import Thread
from string import Template
import logging
import pdb
import commands
import time
import requests
import urllib
import json
import time


RSYNC_REPO_CMD = Template("rsync -az root@$SERVER:$REMOTE_REPO $LOCAL_REPO")
#RSYNC_REPO_CMD = Template("scp -i /root/nopwdkey  root@$SERVER:$REMOTE_REPO $LOCAL_REPO")
#COPY_CMD = Template("cp $NFS_MOUNT/$FILE_PATH $LOCAL_REPO/$FILE_PATH")
NOTIFY_COMPLETE_URL = Template("http://$SERVER/cargo/replication/$CONTAINER")
SHUTDOWN_SERVICE = Template("service $CONTAINER-$VOLUME stop")
SVC_FILEPATH = Template("/etc/init/$CONTAINER-$VOLUME")

class Replicator(Thread):
    def __init__(self, jobq, agentid, localrepo, sourcehost, sourcepath, containerid, volumeid, server):
        Thread.__init__(self)
        self.jobq = jobq
        self.localrepo = localrepo
        self.sourcehost = sourcehost
        self.sourcepath = sourcepath
        self.containerid = containerid
        self.server = server
        self.agentid = agentid
        self.volumeid = volumeid

    def notify_server(self, totalCount, currCount, completed):
        url = NOTIFY_COMPLETE_URL.substitute(SERVER = self.server, CONTAINER=self.containerid)
        headers = {"content-type": "application/json"}
        payload = dict()
        curtime = time.strftime("%Y-%m-%d %H:%M:%S")
        payload['timestamp'] = curtime
        payload['volume'] = self.sourcepath
        payload['total'] = totalCount
        payload['current'] = currCount
        payload['completed'] = completed

        try:
            logging.debug("Notify cargo server URL: %s"%(url))
            resp = requests.post(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as e:
            logging.eror("Error connecting to cargo server: %s"%(e))

    def graceful_stop(self):
        svcFile = SVC_FILEPATH.substitute(CONTAINER = self.containerid, VOLUME = self.volumeid)
        try:
            os.remove(svcFile)
        except:
            pass

        cmd = SHUTDOWN_SERVICE.substitute(CONTAINER = self.containerid, VOLUME = self.volumeid)
        status, output = commands.getstatusoutput(cmd)
        logging.debug("Executing command %s"%(cmd))
        if status != 0:
           logging.error("Error stopping replication service for %s %s: %s"%(self.containerid, self.volumeid,
           output))

    def run(self):
        totalCount = len(self.jobq)
        currCount = 0
        self.notify_server(totalCount, currCount, completed = False)

        while len(self.jobq) > 0:
            try:
                job = self.jobq.pop()
            except IndexError as err:
                logging.error("Error retriving the job: %s"%(err))
                break
            else:
                currCount+=1
            	sdatapath = os.path.join(self.sourcepath, job.lstrip("/"))
            	tdatapath = os.path.join(self.localrepo, job.lstrip("/"))
            	if not os.path.exists(os.path.dirname(tdatapath)):
               		os.makedirs(os.path.dirname(tdatapath))
           
            	cmd = RSYNC_REPO_CMD.substitute(SERVER = self.sourcehost, \
                	REMOTE_REPO = sdatapath, LOCAL_REPO = tdatapath)
          	
            	logging.debug("Execute command: %s"%(cmd))
            	status, output = commands.getstatusoutput(cmd)     
            	if status != 0:
                	logging.error("Error copying file: %s"%(output))
       
                if(currCount%100 == 0):
                    self.notify_server(totalCount, currCount, completed = False)

        self.notify_server(totalCount, currCount, completed = True)
        self.graceful_stop()
