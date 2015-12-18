#!/usr/bin/env python

#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

import os
import optparse
import logging
from voyage import *

def main():
    usage = "usage: python %prog -f <config_file> {--list | --migrate --source <source> --container <container> --target <target> (optional)--rootfs}"

    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-l", "--list", action="store_true", dest="listc", default=False, help="list containers")
    parser.add_option("-m", "--migrate", action="store_true", dest="migrate", default=False, help="migrate container")
    parser.add_option("-f", "--failover", action="store_true", dest="failover", default=False, help="failover container")
    parser.add_option("--status", action="store_true", dest="status", default=False, help="query lazy replication status")
    parser.add_option("--source", action="store", dest="source", default = None, help="Source Host (agent name)")
    parser.add_option("--container", action="store", dest="container", default = None, help="Container name to be migrated")
    parser.add_option("--target", action="store", dest="target", default = None, help="Target Host (agent name)")
    parser.add_option("--rootfs", action="store_true", dest="rootfs", default=False, help="migrate rootfs")
    parser.add_option("-s", "--server", action="store", dest="server", default="127.0.0.1:5000", help="Cargo server and port")

    opts,args= parser.parse_args()
    
    listc = opts.listc
    migrate = opts.migrate
    failover = opts.failover
    server = opts.server
    source = opts.source
    target = opts.target
    rootfs = opts.rootfs
    container = opts.container
    status = opts.container

    if not listc and not migrate and not failover and not status:
        parser.print_help()

    if migrate and not source and not target and not container:
        parser.print_help()

    if failover and not target and not container and not server:
        parser.print_help()

    if status and not container:
        parser.print_help()


    voyage = Voyage(server)

    if listc:
        voyage.listcontainers()
        sys.exit(0)
    if migrate:
        voyage.migrate(source, container, target, rootfs)    
        sys.exit(0)

    if failover:
        voyage.failover(container, target)
        sys.exit(0)

    if status:
        voyage.getStatus(container)

if __name__=="__main__":
    main()

