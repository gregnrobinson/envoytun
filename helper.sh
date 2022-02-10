#!/bin/bash
#sysinfo=$(docker exec -it 9f93cdb1c2f9 curl -s http://10.0.0.7:10000/getinfo | jq '.')
#hits=$(docker exec -it 9f93cdb1c2f9 curl -s http://10.0.0.7:10000/getinfo | jq '.')

container=envoytun-envoytun-1
containers_all=$(docker ps -a -q)

init(){
    git pull
    docker-compose up --build -d
}

up(){
    docker-compose up -d
}

build(){
    git pull
    docker-compose build
}

run(){
    docker run -it dev_dev /bin/bash
}

enter(){
    docker exec -it ${container} /bin/bash
}

$1
