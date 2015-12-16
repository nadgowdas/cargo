# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


import os
import sys
import optparse
from jobQ import *
from crawler import *
import logging
from replicator import *
from monitor import *
import pdb
import signal
from multiprocessing import Manager

def main():
    logging.basicConfig(filename='/var/log/cargo-replicator.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    usage = "usage: python %prog -m <monitor path> -c <copy directory> -h <source host>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--mondir", action="store", dest="mondir", help="monitor directory path")
    parser.add_option("--nfsdir", action="store", dest="nfsdir", help="NFS mount directory path")
    parser.add_option("--srcdir", action="store", dest="srcdir", help="source directory path")
    parser.add_option("--destdir", action="store", dest="destdir", help="destincation/local directory path")
    parser.add_option("--container", action="store", dest="container", help="container-id")
    parser.add_option("--srchost", action="store", dest="srchost", help="source host")
    parser.add_option("--server", action="store", dest="server", help="cargo server host:port")
    parser.add_option("--agentid", action="store", dest="agentid", help="local agent id")
    parser.add_option("--volumeid", action="store", dest="volumeid", help="volume id")

    opts,args= parser.parse_args()
    mondir = opts.mondir
    nfsdir = opts.nfsdir
    destdir = opts.destdir
    srchost = opts.srchost
    srcdir = opts.srcdir
    server = opts.server
    container = opts.container
    agentid = opts.agentid
    volumeid = opts.volumeid

    if not os.path.exists(destdir):
        os.makedirs(destdir)

    #jobq = JobQ()
    mgr = Manager()
    jobq = mgr.list()
    #copydoneEvent = threading.Event()
    #copydoneEvent = 0
    crawler = Crawler(nfsdir, jobq)
   
    crawler.start()
    crawler.join()
    #jobq.printQ()    
    #pdb.set_trace()
    monitor = Monitor(mondir, jobq)
    monitor.start()

    replicator = Replicator(jobq, agentid, destdir, srchost, srcdir, container, volumeid, server)
    replicator.start()
    monitor.join()
    replicator.join()

if __name__=="__main__":
    main()
