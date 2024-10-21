#!/bin/bash

echo "Starting Federated Server with: port=$1 --- epochs=$2 --min_client=$3"

python3 server.py --port=$1 --epochs=$2 --clients=$3