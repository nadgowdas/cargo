# Copyright 2013, 2015 IBM Corp.
#
#© Copyright IBM Corporation 2015.   
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


from __future__ import print_function
import threading
from threading import Thread
import sys
import pdb
from multiprocessing import Process, Manager
import os
from inotify import watcher
import inotify
import select


class Monitor(Thread):
    def __init__(self, dirpath, jobq):
        Thread.__init__(self)
        if dirpath.endswith("/"):
            self.mondir = dirpath
        else:
            self.mondir = dirpath +"/"
        self.jobq = jobq
     
    def run(self):
        w = watcher.AutoWatcher()
        try:
            # Watch all paths recursively, and all events on them.
            w.add_all(self.mondir, inotify.IN_CREATE)
        except OSError as err:
            print('%s: %s' % (err.filename, err.strerror), file=sys.stderr) 
        poll = select.poll()
        poll.register(w, select.POLLIN)

        timeout = None

        threshold = watcher.Threshold(w, 512)
        while self.jobq.count > 0:
            events = poll.poll(timeout)
            nread = 0
            if threshold() or not events:
                for evt in w.read(0):
                    nread += 1
		    print(repr(evt.fullpath), ' | '.join(inotify.decode_mask(evt.mask)))
                    mfilemeta = evt.fullpath.split(self.mondir)
		    if len(mfilemeta) <= 1:
			continue
		    modifiedfile = mfilemeta[1]
                    print(modifiedfile)
		    try:
                    	self.jobq.remove(modifiedfile)
		    except ValueError as err:
			pass

            if nread:
                timeout = None
                poll.register(w, select.POLLIN)
            else:
                timeout = 10
                poll.unregister(w)
