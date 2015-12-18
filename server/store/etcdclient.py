#
#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0


"""
this is a etcd client
"""

class EtcdClient():
    def __init__(self, server, port):
        self.client = etcd.Client(host=server, port=port)

    def write(self, key, value):
        self.client.write(key, value)
        
    def read(self, key):
        value = client.read(key).value     

    def update(self, value):
        self.client.update(value)
                        
