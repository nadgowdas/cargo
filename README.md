Cargo - Container Storage Migration Solution
======================================
Cargo is a system that we have developed at IBM Research to migrate containers along with their data with minimal downtime. Cargo leverages data federation capabilities of union filesystem to create a unified view of data (mainly the root file system) across the source and target hosts. This allows Cargo to start up a container almost immediately (within milliseconds)  on the target host as the data from source root file system gets copied to target hosts either on-demand (using a copy-on-write (COW) partition)  or lazily in the background (using rsync). 

Installation
--------------------------------------
Cargo system primarily consist of following two components:
1) server: a centralized authority to orchestrate and manage the migration process. 
2) agent: it needs to be installed on every docker host in the cluster. Agent is responsible 
for locally managing the container on the host.

>NOTE: Before deploying this service into production, please perform adequate testing.

>NOTE: Currently cargo supports migration of data volumes only. Support for 'rootfs' migration is under active development and will be added soon.


Installing server:
------------------------------------

Pre-requisites:
--------------
1) Flask framework

```bash
$ pip install Flask flask-restful
```

2) etcd Server

Cargo server uses `etcd` for storing the migration metadata. You can either download and install `etcd` on the server or 
you can simply instantiate a new etcd container.

```bash
$ docker  pull gcr.io/google_containers/etcd:2.0.12
$ docker run --net=host -d gcr.io/google_containers/etcd:2.0.12 /usr/local/bin/etcd --addr=127.0.0.1:4001
--bind-addr=0.0.0.0:4001 --data-dir=/var/etcd/data

```
3) etcd python client

```bash
$ git clone https://github.com/jplana/python-etcd.git
$ cd python-etcd/
$ python setup.py install
```

Starting a server
---------------------------------

Download the source code (.zip) or clone from the git-repo.


```bash
$ cd cargo/server
$ python apiserver.py -h
Usage: python apiserver.py -c <config file>

Options:
  -h, --help            show this help message and exit
  -c CONFIG, --config=CONFIG
                        Config File(default=./config.cfg)
```
Update the config.cfg file as required.

For example:
```bash
$ python apiserver.py
```

Currently, it will not go deamon. It will print logs to the terminal

Installing agent:
----------------------------
Follow this instructions to install agent on every docker host

Pre-requisites:
---------------------------
1) Flask framework
```bash
$ pip install Flask flask-restful
```

2) docker-py
```bash
$ pip install docker-py
```

3) py-inotify 
Download the latest py-inotify package from https://pypi.python.org/pypi/python-inotify and add this to the python package list
```
$ wget https://pypi.python.org/packages/2.7/p/python-inotify/python-inotify-0.6-test.linux-x86_64.tar.gz#md5=28415492ec2de0312d84debdb0e9a037
$ tar -xvf python-inotify-0.6-test.linux-x86_64.tar.gz
$ cp -r ./usr/local/lib/python2.7/dist-packages/inotify /usr/local/lib/python2.7/dist-packages/
$ cp ./usr/local/lib/python2.7/dist-packages/python_inotify-0.6_test.egg-info /usr/local/lib/python2.7/dist-packages/ 
```
> NOTE: This packages is expected to be bundled as .deb, to avoid manual install.

4) Setup password-less SSH between all agents

5) Setup NFS server and client on every docker host.

For example, on ubuntu hosts follow these instructions

```
$ apt-get install nfs-kernel-server #install server
$ apt-get install nfs-common # install client
```

And make sure the firewall rules are enabled for NFS mounting between docker hosts.


Starting Agent
------------------------
```bash
$ cd cargo/agent
$ python agent.py -h
Usage: python server.py -c <config file> 

Options:
  -h, --help            show this help message and exit
  -c CONFIG, --config=CONFIG

```
Update config.cfg file with docker deamon endpoint and cargo server details.
For example

```bash
$ python agent.py
```

Currently, it will not go deamon. It will print logs to the terminal

