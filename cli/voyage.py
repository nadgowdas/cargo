# Copyright 2013, 2015 IBM Corp.
#
#Copyright IBM Corporation 2015.
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
        url = LIST_CONTAINER_URL.substitute(SERVER = self.server)
        headers = {"content-type": "application/json"}
        payload = dict()
        try:
            resp = requests.get(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as err:
            print "Can not connect to cargo server"
            sys.exit(1)
        containermap = json.loads(resp.content) if resp.status_code == 200 else dict()
        self.pretty_print_list(containermap)

    def pretty_print_list(self, containermap):
        fmt = "%s\t%30s\t%32s"
        print fmt % ("HOSTID", "CONTAINER", "STATUS")
        print fmt % ("-------", "------------", "------------")
        for agent in containermap:
            print agent.split('/agent/')[1]
            for container in containermap[agent]:
                print fmt % ("", container['Names'][0].split('/')[1] , container['Status'])

        return 0

    def migrate(self, source, container, target, rootfs = False):
        url = LIST_CONTAINER_URL.substitute(SERVER = self.server)
        payload = {"source": source, "target": target, "container": container, "rootfs": rootfs}
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

    def failover(self, container, target):
        url = FAILOVER_CONTAINER_URL.substitute(SERVER = self.server, NODE = target, CONTAINER = container)
        payload = dict()
        headers = {"content-type": "application/json"}
        try:
            resp = requests.post(url, data=json.dumps(payload), headers=headers)
        except requests.exceptions.ConnectionError as err:
            print "Can not connect to cargo server"
            sys.exit(1)
        print "Container failover %s." % ("succeeded" if resp.status_code == 200 else "failed")

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
            fmt = "%s\t%10s\t%10s\t%20s\t%20s\t%20s"
            print fmt % ("CONTAINER", "TOTAL FILES", "FILES COPIED", "STARTED AT", "LAST UPDATED",
                         "COMPLETED AT")
            print fmt % ("-" * 7 + "\t", "-" * 12, "-" * 12, "-" * 12, "-" * 12, "-" * 12)
            print fmt % (container, result["total"], result["curr"], str(result["start"]),
                         str(result["update"]), str(result["complete"]))

