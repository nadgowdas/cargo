# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

"""

"""

import logging
import json
import pdb
import commands
import requests

from docker import Client

import codes

CARGO_VOL_DIR = "/var/lib/cargo"

class DockerClient():

    def __init__(self, dockerURL):
        self.dclient = Client(base_url=dockerURL)


    def listContainers(self):
        containerList = []
        rc = codes.SUCCESS
        try:
            containerList = self.dclient.containers()
        except docker.errors.NotFound as err:
            rc = codes.NOT_FOUND
            logging.error(err) 
        except requests.exceptions.ConnectionError as e:
            rc = FAILED
            logging.error(e)

        else:                       
            return (rc, containerList)

    def inspectContainer(self, containerId):
        containerInfo = dict()
        rc = codes.SUCCESS
        try:
            containerInfo = self.dclient.inspect_container(containerId)
        except docker.errors.NotFound as err:
            rc = codes.NOT_FOUND
            logging.error(err) 
        except requests.exceptions.ConnectionError as e:
            rc = codes.FAILED
            logging.error(e)
        else:                       
            return (rc, json.dumps(containerInfo))
    
    def start(self, containerId):
        rc = codes.SUCCESS
        try:
            self.dclient.start(container=containerId)
        except docker.errors.NotFound as err:
            rc = codes.NOT_FOUND
        except requests.exceptions.ConnectionError as err:
            rc = FAILED    

        return rc
    

    def create(self, config):
        rc = codes.SUCCESS
        name = config["Name"].strip("/")
        image = config["Config"]["Image"]
        command  = config["Config"]["Cmd"]
        env  = config["Config"]["Env"]
        entrypoint = config["Config"]["Entrypoint"]
        ports = config["NetworkSettings"]["Ports"]
        cports = []
        portmap = {}
        if ports:
            for port in ports:
                cport  = port.split('/tcp')[0]
                portmap[cport] = None
                #hport = ports[port][0]['HostPort']
                #portmap[cport] = hport
                cports.append(cport)

        sVolList = []
        volMap = []
        
        mounts = config.get("Mounts", [])

        for volume in mounts:
            dVolume = volume["Destination"]
            isRW = volume["RW"]
            mode = 'rw'
            if not isRW:
                mode = 'ro'
            if not volume["isNFS"]:
                volcnt = volume["Source"]
                sVolume = "{home}/union_{name}_{cnt}".format(home=CARGO_VOL_DIR,name = name, cnt = volcnt)
            else:
                sVolume = volume["Source"]
                #sVolList.append(sVolume)

            volumeMeta = "{}:{}:{}".format(sVolume, dVolume, mode)
            volMap.append(volumeMeta)
        
        '''
        volumes = config["Volumes"]
        for contVol in volumes.keys():
            hostVolume = volumes[contVol]
            rwFlag = config["VolumesRW"][contVol]
            mode = 'rw'
            if not rwFlag:
                mode = 'ro'
            volumeMeta = "{}:{}:{}".format(hostVolume, contVol, mode)
            volMap.append(volumeMeta)
        '''
                
        host_config = self.dclient.create_host_config(port_bindings= portmap, \
                    binds = volMap)
        try:
            self.dclient.create_container(name = name, image = image, command = command, environment = env,\
                entrypoint = entrypoint, ports = cports, volumes = sVolList, host_config=host_config)

        except requests.exceptions.ConnectionError as err:
            rc = FAILED    
        
        return rc

    '''
    def create(self, config):
        rc = codes.SUCCESS
	pdb.set_trace()
        cmd = "docker create "
        name = config["Name"]
        cmd = cmd + "--name {} ".format(name)

        image = config["Config"]["Image"]
        envList  = config["Config"]["Env"]
       
	if envList: 
        	envstr = ""
        	for env in envList:
            		envstr  = envstr + "-e {}".format(env)
        
        	cmd  = cmd + envstr
                 
        entrypoint = config["Config"]["Entrypoint"]
        ports = config["NetworkSettings"]["Ports"]
        cports = []
        portmap = {}
        portstr = ""
        for port in ports:
            cport  = port.split('/tcp')[0]
            hport = ports[port][0]['HostPort']
            portmap[cport] = hport
            cports.append(cport)
            portstr = portstr +"-p {}:{} ".format(cport, hport)

        cmd  = cmd + portstr

        sVolList = []
        volMap = []
       
        volstr = ""
         
        mounts = config["Mounts"]
        for volume in mounts:
            dVolume = volume["Destination"]
            sVolume = volume["Source"]
            isRW = volume["RW"]
            mode = 'rw'
            if not isRW:
                mode = 'ro'
             
            volstr = volstr + "-v {}:{}:{} ".format(sVolume, dVolume, mode)
        cmd  = cmd +  volstr

	cmd = cmd + image
        print cmd
	status, output  = commands.getstatusoutput(cmd)
	if status != 0:
		return codes.FAILED
	else:
		return code.SUCCESS
    '''
 
    def stop(self, containerId):
        rc = codes.SUCCESS
        try:
            self.dclient.stop(container=containerId)
        except docker.errors.NotFound as err:
            rc = codes.NOT_FOUND
        except requests.exceptions.ConnectionError as err:
            rc = FAILED    

        return rc

                                 
