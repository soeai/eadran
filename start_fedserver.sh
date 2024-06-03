#!/bin/bash
echo "Starting Fed Server of EADRAN"

export PYTHONPATH="${PYTHONPATH}:$PWD"

python3 fed_server/orchestration/start_fed_server_service.py --conf=fed_server/conf/config.json &
