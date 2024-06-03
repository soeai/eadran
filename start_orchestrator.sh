#!/bin/bash
echo "Starting Orchestrator of EADRAN"

export PYTHONPATH="${PYTHONPATH}:$PWD"

python3 cloud/orchestrator/orchestrator.py --conf=cloud/orchestrator/conf/config.json --image=cloud/orchestrator/conf/image4edge.json &
