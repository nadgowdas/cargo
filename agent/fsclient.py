# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


"""

"""
from string import Template
import os
import commands
import logging
import pdb
import pickle

import codes
import utils

NFS_EXPORT_CONFIG = "/etc/exports"
NFS_EXPORT_FS = "exportfs -a"
NFS_MOUNT_CMD = Template("mount -t nfs -o v3 $EXPORTPATH $MOUNTPATH")
UNION_MOUNT_CMD = Template("mount -t aufs -o br=$UPPER_DIR=rw:$LOWER_DIR=ro -o udba=reval none $MOUNT")
GET_ALL_NFS_MOUNTS = "mount -l -t nfs"
GET_ALL_AUFS_MOUNTS = "mount -l -t aufs | awk '{print $3}'"
UNMOUNT_CMD = Template("umount -l $MOUNT")
COPY_WITH_HARDLINKS = Template("cp -lR --remove-destination $SRC/* $TARGET/")

CARGO_VOL_DIR = "/var/lib/cargo"

class FilesystemClient():
    def nfsExport(self, config):
        dirpath = config["exportPath"]

        if not os.path.exists(dirpath):
            return codes.NOT_FOUND
        
        #exportcfg = "{path} *(rw,fsid=0,sync,no_root_squash)\n".format(path = dirpath)
        exportcfg = "{path} *(rw,sync,no_root_squash,nohide)\n".format(path = dirpath)
        fp = open(NFS_EXPORT_CONFIG, 'a')
        fp.write(exportcfg)
        fp.close()
        
        logging.debug("Re-exporting NFS mounts.")
        status, output = commands.getstatusoutput(NFS_EXPORT_FS)
        if status != 0:
            logging.error("NFS restart failed. {}".format(output))
            return codes.FAILED

        return codes.SUCCESS

    
    def __nfs_import(self, exportpath, mountpath):
        if not os.path.exists(mountpath):
            os.makedirs(mountpath)
        
        cmd = NFS_MOUNT_CMD.substitute(EXPORTPATH = exportpath, MOUNTPATH = mountpath)    
        logging.debug("Executing NFS mount command: {}".format(cmd))
        status, output = commands.getstatusoutput(cmd) 
        if status != 0:
            logging.error("Error mounting NFS. {}".format(output))
            return codes.FAILED
        
        logging.debug("NFS mounted successfully at {}".format(mountpath)) 
        return codes.SUCCESS
    
    def __merge_fs(self, lowerdir, upperdir, mountpath):
       
        #currently if mount path already exists, it will be overwritten with new mount
        if not os.path.exists(mountpath):
            os.mkdir(mountpath)
        
        if not os.path.exists(upperdir):
            os.mkdir(upperdir)

        cmd = UNION_MOUNT_CMD.substitute(UPPER_DIR = upperdir, LOWER_DIR = lowerdir, MOUNT = mountpath)
        logging.debug("Executing union mount command: {}".format(cmd))
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logging.error("Error mounting union filesystem. {}".format(output))
            return codes.FAILED
        
        logging.debug("Union filesystem mounted successfully at {}".format(mountpath))
        return codes.SUCCESS
        
    def __storeMeta(self, containerName, nfsMount, cowdir, unionMount, lzcopydir):
        mdfile = utils.getContainerMDFile(containerName)
        volMap = {}
        newVol = {}
        newVol["nfs"] = nfsMount
        newVol["cow"] = cowdir
        newVol["union"] = unionMount
        newVol["lazy"] = lzcopydir

        if os.path.exists(mdfile):
            volMap = pickle.load( open( mdfile, "rb" ))            
        volMap[unionMount] = newVol
        pickle.dump( volMap, open( mdfile, "wb" ) )

    def prepareTargetFS(self, config):
        containerName = config["container"]
        sourceHost = config["sourceHost"]
        exportPath = config["exportPath"]
       	volcnt = config["volcnt"]
	 
        #nfsMount = "{home}/nfs_{name}_{cnt}".format(home=CARGO_VOL_DIR,name = containerName, cnt = volcnt)
        #cowdir = "{home}/cow_{name}_{cnt}".format(home=CARGO_VOL_DIR,name = containerName, cnt = volcnt)
        #unionMount = "{home}/union_{name}_{cnt}".format(home=CARGO_VOL_DIR,name = containerName, cnt = volcnt)
        #lzcopydir = "{home}/lzcopy_{name}_{cnt}".format(home=CARGO_VOL_DIR,name = containerName, cnt = volcnt)
        nfsMount = utils.getNFSMountDir(containerName, volcnt)
        cowdir = utils.getCOWDir(containerName, volcnt)
        unionMount = utils.getUnionMountDir(containerName, volcnt)
        lzcopydir = utils.getLazyCopyDir(containerName, volcnt)

        #unionMount = exportPath
        nfsexport = "{host}:{path}".format(host=sourceHost, path = exportPath)

        if self.__nfs_import(nfsexport, nfsMount) == codes.SUCCESS:
                if self.__merge_fs(nfsMount, cowdir, unionMount) == codes.SUCCESS:
                    self.__storeMeta(containerName, nfsMount, cowdir, unionMount, lzcopydir)
                    return codes.SUCCESS

        return codes.FAILED

    def checkAndGetNFSMeta(self, config):
        nfsMeta = dict() 
        volPath = config["volume"]

        status, output = commands.getstatusoutput(GET_ALL_NFS_MOUNTS)
        if status != 0:
            logging.error("mount list command failed. {}".format(output))
            return codes.FAILED
        
        if output == None:
            nfsMeta["is_nfs_mounted"] = False
            return (codes.SUCCESS, nfsMeta)

        nfsList = output.split("\n")
        for nfsmount in nfsList:
            mountPoint = nfsmount.split()[2]
            if volPath in mountPoint:
                nfsMeta["is_nfs_mounted"] = True
                nfsMeta["nfs_server"] = nfsmount.split()[0].split(":")[0]
                nfsMeta["nfs_exportpath"] = nfsmount.split()[0].split(":")[1]
                nfsMeta["nfs_mountpath"] = mountPoint
                return (codes.SUCCESS, nfsMeta)    


    def mountNFSVolume(self, config):
        nfsServer = config["nfsmeta"]["nfs_server"]
        nfsExportPath = config["nfsmeta"]["nfs_exportpath"]
        nfsMount = config["nfsmeta"]["nfs_mountpath"]

        nfsexport = "{host}:{path}".format(host=nfsServer, path = nfsExportPath)
        return self.__nfs_import(nfsexport, nfsMount)

    def __exec(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logging.error("Executing command failed: %s: %s"%(cmd, output))

        return status

    def failoverVolumes(self, containerId):
        mdfile = utils.getContainerMDFile(containerId)
        rc = codes.SUCCESS
        volMap = {}
        if os.path.exists(mdfile):
            volMap = pickle.load( open( mdfile, "rb" ))            
        
        for unionMout, mountMap in volMap.items():
            logging.debug("Starting failover for volume: %s"%(unionMout))
            #1. unmount the aufs directory
            logging.debug("Un-mounting aufs mount point : %s"%(unionMout))
            
            cmd = UNMOUNT_CMD.substitute(MOUNT = str(unionMout))
            rc = self.__exec(cmd)
            if rc == codes.SUCCESS:
                logging.debug("aufs mount point unmounted successfully: %s"%(unionMout))
            else:
                return rc

            #2. delete aufs mount directory
            umdir = unionMout.rstrip('/')
            cmd = "rm -rf %s"%(umdir)
            rc = self.__exec(cmd)
            if rc == codes.SUCCESS:
                logging.debug("aufs mount point deleted successfully %s"%(unionMout))
            else:
                return rc

            #3. rename lazy directory to mount point
            lazycopyDir = volMap[unionMout]["lazy"].rstrip("/")
            os.rename(lazycopyDir, umdir)

            logging.debug("lazycopy directory renamed from %s to %s"%(lazycopyDir, umdir))
            #4. hard-link from cow to unin mount directory
            cmd = COPY_WITH_HARDLINKS.substitute(SRC = volMap[unionMout]["cow"], TARGET = unionMout)
            rc = self.__exec(cmd)
            if rc  == codes.SUCCESS:
                logging.debug("Data files hard-linked successfully")
            else:
                return rc

            #5. unmount nfs
            cmd = UNMOUNT_CMD.substitute(MOUNT = volMap[unionMout]["nfs"])
            self.__exec(cmd)

            return rc
        




