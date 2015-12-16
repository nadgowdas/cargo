Cargo - User Guide
==========================================

Cargo currently support a CLI and an REST-API model for managing container migration.
Once you have successfully setup server and agent(s), you can use following guide to 
trigger/manage container migration.

> NOTE: Currently, cargo assumes the base image for the container being migrated is 
available at both source and target host. We are looking to add the capability to 
automatically pull/copy the image on the target if it is not present.

CLI
-----------------------------------
> NOTE: Corresponding REST-API are listed below for reference

1) Go to `cli` directory
```bash
$ cd cargo/cli
```

2) List Containers
```bash
$ ./cargo.py -l --server <cargo server ip:port>
```

Example
```bash
$./cargo.py --list --server 9.0.0.5:5000
HOSTID                       CONTAINER                            STATUS
-------                   ------------                      ------------
ee80061b-0d11-4b7a-aeeb-f8cd4ddbd9b8
                                testme                        Up 12 days
457e43a5-e62d-4669-ab0f-6f5ae7ec7492
                             mysqldemo                      Up 2 minutes
                                testme                        Up 2 weeks

```

3) Start a migration
```bash
$./cargo.py -migrate --source <source hostid> --container <containerid> --target <target hostid> --server <cargo server ip:port>
```
Example
```bash
$./cargo.py --migrate --source 457e43a5-e62d-4669-ab0f-6f5ae7ec7492 --container mysqldemo --target
ee80061b-0d11-4b7a-aeeb-f8cd4ddbd9b8 --server 9.0.0.5:5000

Container Migrated successfully.
Lazy copy is in progress.

```

4) At this point, your container is migrated and started at the target host and is stopped at the source.
   And lazy copy is in progress, which will copy files from source host in the background.

5) You can monitor the status of the lazy copy 
```bash
$./cargo.py --status --container <containerid> --server <cargo server ip:port>
```

Example
```bash
#./cargo.py --status --container mysqldemo --server 9.0.0.5:5000
CONTAINER       TOTAL FILES     FILES COPIED              STARTED AT            LAST UPDATED            COMPLETED AT
-------         ------------    ------------            ------------            ------------            ------------
mysqldemo              137             0         2015-11-12 05:38:21     

# python cargo.py --status --container mysqldemo --server 9.0.0.5:5000
CONTAINER       TOTAL FILES     FILES COPIED              STARTED AT            LAST UPDATED            COMPLETED AT
-------         ------------    ------------            ------------            ------------            ------------
mysqldemo              137             100       2015-11-12 05:38:21     2015-11-12 05:39:15     

# python cargo.py --status --container mysqldemo --server 9.0.0.5:5000
CONTAINER       TOTAL FILES     FILES COPIED              STARTED AT            LAST UPDATED            COMPLETED AT
-------         ------------    ------------            ------------            ------------            ------------
mysqldemo              137             137       2015-11-12 05:38:21     2015-11-12 05:39:15     2015-11-12 05:39:37

```

6) Once the lazy copy is completed, all of your container data is successfully migrated to target host. 
   Unless you failover the container, it is still accessing the un-modified data from the source host.

7) Finally, in your maintainace window, you can perform the failover
```bash
$/cargo.py --failover --target <target host> --container <containerid> --server <cargo server ip:port>
```

Example:
```bash
#./cargo.py --failover --target ee80061b-0d11-4b7a-aeeb-f8cd4ddbd9b8 --container mysqldemo --server 9.0.0.5:5000
Container failover successfully.
```
> NOTE: Failover will bring down your container momentarily and will start it again.
 

REST-API
-----------------------------------------
1) List all the containers in your cluster

```bash
GET /cargo
```

Example
```bash
curl -i -H "Content-Type: application/json" -H "Accept: application/json" -X GET http://9.0.0.5:5000/cargo
```

Example Response
```bash
HTTP/1.1 200 OK
Content-Type: application/json
{
    "/agent/457e43a5-e62d-4669-ab0f-6f5ae7ec7492": [
        {
            "Command": "/entrypoint.sh mysqld --datadir=/var/lib/mysql --user=mysql",
            "Created": 1447255384,
            "HostConfig": {
                "NetworkMode": "default"
            },
            "Id": "e1bf478fe8075fa6fe2be2ea1d6fdb348e5abbb10627bf7083e521a2ab45c30e",
            "Image": "mysql:5.6.17",
            "Labels": {},
            "Names": [
                "/mysqldemo"
            ],
            "Ports": [
                {
                    "PrivatePort": 3306,
                    "Type": "tcp"
                }
            ],
            "Status": "Up 4 minutes"
        },
        {
            "Command": "/bin/bash",
            "Created": 1445838032,
            "HostConfig": {
                "NetworkMode": "default"
            },
            "Id": "3f471e1ddeefc13b11ab15161df96ca62a29d4f7654f65284a59e71702c8c43f",
            "Image": "ubuntu:14.04",
            "Labels": {},
            "Names": [
                "/testme"
            ],
            "Ports": [],
            "Status": "Up 2 weeks"
        }
    ],
    "/agent/ee80061b-0d11-4b7a-aeeb-f8cd4ddbd9b8": [
        {
            "Command": "/bin/bash",
            "Created": 1445865257,
            "HostConfig": {
                "NetworkMode": "default"
            },
            "Id": "e34a55220f69f6ced1bccf0b4606db73baabd72fddbb2e65224c9a06d6524c08",
            "Image": "ubuntu:14.04",
            "Labels": {},
            "Names": [
                "/testme"
            ],
            "Ports": [],
            "Status": "Up 12 days"
        }
    ]
}
```

2) Start a container migration

```bash
POST /cargo
```

Example:
```bash
curl -i -H "Content-Type: application/json" -H "Accept: application/json" -X POST http://9.0.0.5:5000/cargo -d 
'{
    "source":"9.0.0.2", 
    "target":"9.0.0.1", 
    "container":"boring_kilby", 
    "rootfs":false
}'
```

Example Response:
```bash
HTTP/1.1 200 OK
Content-Type: application/json
```

3) Get the status of the lazy copy
```bash
GET /cargo/replication/<containerid>
```

Example:
```bash
# curl -H "Content-Type: application/json" -H "Accept: application/json" -X GET http://9.0.0.5:5000/cargo/replication/mysqldemo | python -mjson.tool
{
    "complete": "2015-11-13 21:59:09",
    "completed": true,
    "curr": 137,
    "start": "2015-11-12 05:38:21",
    "total": 137,
    "update": "2015-11-13 21:58:46"
}

```

4) Failover a container
```bash
POST /cargo/failover/<nodeid>/<containerid>
```

Example:
```bash
# curl -H "Content-Type: application/json" -H "Accept: application/json" -X GET \
 >http://9.0.0.5:5000/cargo/failover/ee80061b-0d11-4b7a-aeeb-f8cd4ddbd9b8/mysqldemo | python -mjson.tool

HTTP/1.1 200 OK
Content-Type: application/json
```
