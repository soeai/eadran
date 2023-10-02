#!/bin/bash

docker build -t rdsea/fed_storage_service:1.0 -f ./Dockerfile .
docker rmi -f $(docker images -q --filter "dangling=true")
docker push rdsea/fed_storage_service:1.0