#!/bin/bash
echo "Starting Orchestrator of EADRAN"

export PYTHONPATH="${PYTHONPATH}:$PWD"

python3 fed_edge/orchestrator/start_edge_service.py --conf=fed_edge/conf/config.json &
