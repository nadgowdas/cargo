#
#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


import os
import sys
from threading import Thread
import logging
import pdb

class Crawler(Thread):
    def __init__(self, dirpath, jobQ):
        Thread.__init__(self)
        self.dirpath = dirpath
        self.jobq = jobQ
    
    def run(self):
        try:
            for root, dirs, files in os.walk(self.dirpath):
                for f in files:
                    try:
                        fpath = str(os.path.join(root, f))
                    	self.jobq.append(fpath.split(self.dirpath)[1])
                    except UnicodeEncodeError as err:
                        logging.error("Ignoring non-ascii path: %s"%(f))
                        pass
                    #self.jobq.enqueue(fpath.split(self.dirpath)[1])
        except Exception as e:
            (type, value, tb) = sys.exc_info()
            logging.error("Unhandled Exception : %s %s"%(type, tb))
            sys.exit(1)
 
