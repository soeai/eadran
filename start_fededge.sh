#!/bin/bash
echo "Starting Edge Orchestration Service of EADRAN"

export PYTHONPATH="${PYTHONPATH}:$PWD"

python3 fed_edge/orchestration/start_edge_service.py --conf=fed_edge/conf/config.json &
