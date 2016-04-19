#
#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


import os
import fileinput
import shutil
import commands
import sys


CONFIG_DIR = "/var/lib/cargo"
SVC_TEMPLATE = "replicator_svc.conf"
ETC_INIT_DIR = "/etc/init/"

def getDir(service, container, volcnt):
    fmt = "{CARGO_HOME}/{SERVICE}_{CONTAINER}_{CNT}"
    path = fmt.format(CARGO_HOME = CONFIG_DIR, SERVICE = service, CONTAINER = container, CNT = volcnt)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def getNFSMountDir(container, volcnt):
    return getDir("nfs", container, volcnt)

def getCOWDir(container, volcnt):
    return getDir("cow", container, volcnt)

def getUnionMountDir(container, volcnt):
    return getDir("union", container, volcnt)

def getLazyCopyDir(container, volcnt):
    return getDir("lzcopy", container, volcnt)

def getContainerMDFile(container):
    mdfilepath = "{CARGO_HOME}/{CONTAINER}.md".format(CARGO_HOME = CONFIG_DIR, CONTAINER = container)
    return mdfilepath

def getRepProcID(container, volumeId):
    idfile = "{CARGO_HOME}/repl_{CONTAINER}_{VOLID}.pid".format(CARGO_HOME = CONFIG_DIR, CONTAINER = container, VOLID =
    volumeId)
    if not os.path.exists(idfile):
        return 0

    with open(idfile, 'r') as infile:
        for line in infile:
            procid = line
    return procid

def storeReplProcID(container, volumeId, procId):
    idfile = "{CARGO_HOME}/repl_{CONTAINER}_{VOLID}.pid".format(CARGO_HOME = CONFIG_DIR, CONTAINER = container, VOLID =
    volumeId)
    if os.path.exists(idfile):
        os.remove(idfile)
    with open(idfile, 'w') as outfile:
        outfile.write(procId)

def findAndReplace(infile, searchExp, replaceExp):
    for line in fileinput.input(infile, inplace = 1):
        sys.stdout.write(line.replace(searchExp, replaceExp))

def createReplSvc(container, volumeId, cmd):
    svcName = "{CONTAINER}-{VOLUMEID}".format(CONTAINER = container, VOLUMEID = volumeId)
    svcfile = os.path.join(ETC_INIT_DIR, "{SVC}.conf".format(SVC = svcName))
    shutil.copy2(SVC_TEMPLATE, svcfile)
    findAndReplace(svcfile, "CMD", cmd)
    return svcName

def startSvc(name):
    cmd = "service {NAME} start".format(NAME = name)
    status,output = commands.getstatusoutput(cmd)
    return status, output 
