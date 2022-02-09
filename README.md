# envoytun

This repo is for testing wireguard and envoy. the `docker-compose.yml` deploys a wireguard/envoy container alongside two flask webservers. Each web server hosts static website that identifies which container it is on. This is to test loadbalancing in envoy.

![envoytun](https://user-images.githubusercontent.com/26353407/130336756-103fb5ef-e357-4ef1-9fe2-d1fc4184c80d.png)

## Prerequisites

On the host that will run the boringtun/envoy docker compose stack, make sure the following steps are performed:

```bash
apt update && \
apt install -y \
  docker.io \
  git \
  curl \
  iputils-ping && \
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
sudo chmod +x /usr/local/bin/docker-compose  

# Clone the project to the host
git clone git@github.com:gregnrobinson/envoytun.git
```

[![asciicast](https://asciinema.org/a/RvQnN4jh5MQmod8yRtyFxefuI.svg)](https://asciinema.org/a/RvQnN4jh5MQmod8yRtyFxefuI)

Create a `./wg0.conf` file at the root of the repository with working a working peer configuration...

## Hot to Build/Deploy

```bash
# change into the repo directory
cd ./envoytun

# At the root of the repo run. (Good for seeing live output)
sudo docker-compose up --build

# If you want to run in background run
sudo docker-compose up --build -d

# If you want to enter the wireguard container run
sudo ./helper.sh enter
```

[![asciicast](https://asciinema.org/a/ttwuyybEHErw1PmntWk0qluoC.svg)](https://asciinema.org/a/ttwuyybEHErw1PmntWk0qluoC)

## Build/Push Boringtun

```bash
docker build -t boringtun . -t gregnrobinson/envoytun
docker push gregnrobinson/envoytun
```

## Troubleshooting

```bash
# Get container ID of mesh gateway
docker ps

docker exec -it <container_id> /bin/bash

# Show active Wireguard configuration
wg

# Show iptables on container
iptables -t nat -nvL

# ping target
ping <TARGET_HOST>

# Execute TCP/HTTP Request
curl <TARGET_URL>

# get system info for all load balancer backends
curl -s http://10.0.0.7:10000/getinfo | jq '.'

# get hit counts for all load balancer backends
curl -s http://10.0.0.7:10000/hits | jq '.'
```

## Trigger CloudFunction on BigQuery Load Events

```bash
resource.type="bigquery_resource"
protoPayload.methodName="jobservice.jobcompleted"
protoPayload.serviceData.jobCompletedEvent.eventName="load_job_completed"
protoPayload.authenticationInfo.principalEmail="analytics-processing-dev@system.gserviceaccount.com"
NOT
protoPayload.serviceData.jobCompletedEvent.job.jobConfiguration.load.destinationTable.tableId:"wireguard.peers"
```

## Loadbalancing Breakdown

![envoytun_loadbalancing](https://user-images.githubusercontent.com/26353407/130380669-3a0c7b83-87e4-4b39-88aa-b02e23124f63.png)
