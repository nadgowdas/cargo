# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

import json
import requests
from string import Template
import pdb
import sys


LIST_CONTAINER_URL = Template("http://$SERVER/cargo")
OPERATE_CONTAINER_URL = Template("http://$SERVER/container/$NAME")
FAILOVER_CONTAINER_URL = Template("http://$SERVER/cargo/failover/$NODE/$CONTAINER")
STATUS_URL = Template("http://$SERVER/cargo/replication/$CONTAINER")

class Voyage():
    def __init__(self, server):
        self.server = server

    def listcontainers(self):
        containermap = dict()
        
        url = LIST_CONTAINER_URL.substitute(SERVER = self.server)
        headers = {"content-type": "application/json"}
        payload = dict()
        try:
            resp = requests.get(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as err:
            print "Can not connect to cargo server"
            sys.exit(1)
        if resp.status_code == 200:
            containermap = json.loads(resp.content)
        
        self.pretty_print_list(containermap)

    def pretty_print_list(self, containermap):
        print "%s\t%30s\t%32s"%("HOSTID", "CONTAINER", "STATUS")
        print "%s\t%30s\t%32s"%("-------", "------------","------------")
        for agent in containermap.keys():
            print "%s"%(agent.split('/agent/')[1])
            containers = containermap[agent]
            if containers:
                for container in containers:
                    print "\t%30s\t%32s"%(container['Names'][0].split('/')[1] , container['Status'])

        return 0                           

    def migrate(self, source, container, target, rootfs = False):
        url = LIST_CONTAINER_URL.substitute(SERVER = self.server)
        payload = dict()
        payload["source"] = source
        payload["target"] = target
        payload["container"] = container
        payload["rootfs"] = rootfs

        headers = {"content-type": "application/json"}
        try:
            resp = requests.post(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as err:
            print "Can not connect to cargo server"
            sys.exit(1)

        if resp.status_code == 200:
            print "Container Migrated successfully."
            print "Lazy copy is in progress."
        else:
            print "Container migration failed."
            print "Please check the logs." 

        return         

    def failover(self, container, target):
        url = FAILOVER_CONTAINER_URL.substitute(SERVER = self.server, NODE = target, CONTAINER = container)  
        payload = dict()
        headers = {"content-type": "application/json"}
        try:
            resp = requests.post(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as err:
            print "Can not connect to cargo server"
            sys.exit(1)

        if resp.status_code == 200:
            print "Container failover successfully."
        else:
            print "Container failover failed."


    def getStatus(self, container):
        url = STATUS_URL.substitute(SERVER = self.server, CONTAINER = container)  
        payload = dict()
        headers = {"content-type": "application/json"}
        try:
            resp = requests.get(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as err:
            print "Can not connect to cargo server"
            sys.exit(1)
        if resp.status_code != 200:
            print "Can not gets status for container"
        else:
            result = json.loads(resp.content)
            print "%s\t%10s\t%10s\t%20s\t%20s\t%20s"%("CONTAINER", "TOTAL FILES", "FILES COPIED", \
            "STARTED AT", "LAST UPDATED", "COMPLETED AT")
            print "%s\t\t%10s\t%10s\t%20s\t%20s\t%20s"%("-------", "------------","------------", \
            "------------", "------------","------------")
            print "%s\t%10s\t%10s\t%20s\t%20s\t%20s"%(container, result["total"], result["curr"], \
            str(result["start"]),str(result["update"]), str(result["complete"]))
            
        return

            
         
