#!/bin/bash

docker build -t rdsea/fed_orchestrator_service:1.0 -f ./Dockerfile .
docker rmi -f $(docker images -q --filter "dangling=true")
docker push rdsea/fed_orchestrator_service:1.0