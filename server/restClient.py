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
HEADERS = {"content-type": "application/json"}
ERR_FMT = "{}: Can not connect to cargo agent at: {}"

def inspectContainer(host, port, container):
    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port,
            NAME = container)
    containerMeta = dict()
    rc = codes.SUCCESS
    try:
        resp = requests.get(clientUrl, headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        if resp.status_code == codes.herror(codes.SUCCESS):
            containerMeta = json.loads(resp.content)
    return rc, containerMeta

def exportVolume(host, port, exportpath):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    params = {"exportPath": exportpath}
    payload = {"role": "source", "opcode": "EXPORT_FS", "params": params}
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)    


def importVolume(host, port, source, path, container, volcnt, isroot = False):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    params = {"sourceHost": source, "exportPath": path, "container": container,
              "volcnt": volcnt, "isroot": isroot}
    payload = {"role": "target", "opcode": "IMPORT_FS", "params": params}

    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
                
    return codes.perror(rc)    

def isNFSMounted(host, port, volume):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    params = {"volume": volume}
    payload = {"role": "source", "opcode": "CHECK_NFS", "params": params}

    rc = codes.SUCCESS
    nfsMeta  = None

    try:
        resp = requests.get(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        if resp.status_code == codes.herror(codes.SUCCESS):
            nfsMeta = json.loads(resp.content)

    return rc, nfsMeta

def nfsImportVolume(host, port, nfsMeta, volume):
    clientUrl = EXPORT_FS.substitute(HOST = host, PORT = port)
    params = {"nfsmeta": nfsMeta, "volume": volume}
    payload = {"role": "target", "opcode": "IMPORT_NFS", "params": params}
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)    

def createContainer(host, port, containerCfg):
    name = containerCfg["Name"]
    if name.startswith("/"):
        name = name.split("/")[1]
    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, NAME = name)
    payload = {"opcode": "create", "params": containerCfg}
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)    

def startContainer(host, port, name):
    if name.startswith("/"):
        name = name.split("/")[1]
    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, NAME = name)
    payload = {"opcode": "start"}
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)

def stopContainer(host, port, name):
    if name.startswith("/"):
        name = name.split("/")[1]
    clientUrl = OPERATE_CONTAINER.substitute(HOST = host, PORT = port, NAME = name)
    payload = {"opcode": "stop"}
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, host))
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)

def startLazycopy(host, port, container, volume, volcnt, srchost):
    volumeId = hashlib.md5(volume).hexdigest()
    clientUrl = LAZY_COPY.substitute(HOST = host, PORT = port, CONTAINER = container, VOLUME = volumeId)
    payload = {"srchost": srchost, "volcnt": volcnt, "volume": volume}
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, data=json.dumps(payload), headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, agent))  # should this be host instead of agent?
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)

def stopLazyCopy(host, port, container, volume): 
    volumeId = hashlib.md5(volume).hexdigest()
    clientUrl = LAZY_COPY.substitute(HOST = host, PORT = port, CONTAINER = container, VOLUME = volumeId)
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.delete(clientUrl, headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, agent))  # should this be host instead of agent?
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)

def failover(host, port, container):
    clientUrl = FAILOVER_CONTAINER.substitute(HOST = host, PORT = port, CONTAINER = container)
    rc = codes.SUCCESS  # TODO: This is not used
    try:
        resp = requests.post(clientUrl, headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        logging.error(ERR_FMT.format(e, agent))  # should this be host instead of agent?
        rc = codes.FAILED
    else:
        rc = resp.status_code
    return codes.perror(rc)
