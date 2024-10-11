#!/bin/bash

echo "Starting Federated Server with: port=$1 --- epochs=$2"

python3 server.py --port=$1 --epochs=$2