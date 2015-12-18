#
#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0
"""

"""
import requests
import json
from string import Template
import hashlib

import common.codes as codes

OPERATE_CONTAINER = Template("http://$HOST:$PORT/container/$NAME")
EXPORT_FS = Template("http://$HOST:$PORT/fs")
GREP_EXPORT = Template("cat /etc/exports | grep $DIR")
LAZY_COPY = Template("http://$HOST:$PORT/replication/$CONTAINER/$VOLUME")
FAILOVER_CONTAINER = Template("http://$HOST:$PORT/failover/$CONTAINER")

def inspectContainer(host, port, container):
    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, \
            NAME = container)
    headers = {"content-type": "application/json"}
    payload = dict()
    containerMeta = dict()
    rc = codes.SUCCESS

    try:
        resp = requests.get(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    
    else:
        if resp.status_code == codes.herror(codes.SUCCESS):
            containerMeta = json.loads(resp.content)
    
    return (rc, containerMeta)

def exportVolume(host, port, exportpath):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    headers = {"content-type": "application/json"}
    payload = dict()
    payload["role"] = "source"
    payload["opcode"] = "EXPORT_FS"
    params = dict()
    params["exportPath"] = exportpath
    payload["params"] = params

    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        rc = resp.status_code

    return codes.perror(rc)    


def importVolume(host, port, source, path, container, volcnt, isroot = False):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    headers = {"content-type": "application/json"}
    payload = dict()
    payload["role"] = "target"
    payload["opcode"] = "IMPORT_FS"
    params = dict()
    params["sourceHost"] = source
    params["exportPath"] = path
    params["container"] = container
    params["volcnt"] = volcnt
    params["isroot"] = isroot
    payload["params"] = params

    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
                
    return codes.perror(rc)    

def isNFSMounted(host, port, volume):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    headers = {"content-type": "application/json"}
    payload = dict()
    payload["role"] = "source"
    payload["opcode"] = "CHECK_NFS"
    params = dict()
    params["volume"] = volume
    payload["params"] = params

    rc = codes.SUCCESS
    nfsMeta  = None

    try:
        resp = requests.get(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        if resp.status_code == codes.herror(codes.SUCCESS):
            nfsMeta = json.loads(resp.content)

    return (rc, nfsMeta) 

def nfsImportVolume(host, port, nfsMeta, volume):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    headers = {"content-type": "application/json"}
    payload = dict()
    payload["role"] = "target"
    payload["opcode"] = "IMPORT_NFS"
    params = dict()
    params["nfsmeta"] = nfsMeta
    params["volume"] = volume
    payload["params"] = params
    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
                
    return codes.perror(rc)    

def createContainer(host, port, containerCfg):
    payload = dict()
    payload["opcode"] = "create"
    payload["params"] = containerCfg
    name = containerCfg["Name"]
    if name.startswith("/"):
        name = name.split("/")[1]

    headers = {"content-type": "application/json"}
    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, NAME = name)
    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)    

def startContainer(host, port, name):
    payload = dict()
    payload["opcode"] = "start"
    if name.startswith("/"):
        name = name.split("/")[1]

    headers = {"content-type": "application/json"}

    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, NAME = name)
    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)

 
def stopContainer(host, port, name):
    payload = dict()
    payload["opcode"] = "stop"
    if name.startswith("/"):
        name = name.split("/")[1]
    headers = {"content-type": "application/json"}

    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, NAME = name)
    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(host))
        rc = codes.FAILED
    else:
        rc = resp.status_code

    return codes.perror(rc)


def startLazycopy(host, port, container, volume, volcnt, srchost):
    md5=hashlib.md5()
    md5.update(volume)
    volumeId = md5.hexdigest()

    clientUrl = LAZY_COPY.substitute(HOST = host, PORT = port, CONTAINER = container, VOLUME = volumeId)
    headers = {"content-type": "application/json"}
    payload = dict()
    payload["srchost"] = srchost
    payload["volcnt"] = volcnt
    payload["volume"] = volume

    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(agent))
        rc = codes.FAILED
    else:
        rc = resp.status_code

    return codes.perror(rc)

def stopLazyCopy(host, port, container, volume): 
    md5=hashlib.md5()
    md5.update(volume)
    volumeId = md5.hexdigest()
    clientUrl = LAZY_COPY.substitute(HOST = host, PORT = port, CONTAINER = container, VOLUME = volumeId)
    headers = {"content-type": "application/json"}
    payload = dict()
    rc = codes.SUCCESS
    try:
        resp = requests.delete(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(agent))
        rc = codes.FAILED
    else:
        rc = resp.status_code

    return codes.perror(rc)

def failover(host, port, container):
    clientUrl = FAILOVER_CONTAINER.substitute(HOST = host, PORT = port, CONTAINER = container)
    headers = {"content-type": "application/json"}
    payload = dict()
    rc = codes.SUCCESS
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("Can not connect to cargo agent at: {}".format(agent))
        rc = codes.FAILED
    else:
        rc = resp.status_code

    return codes.perror(rc)
    
