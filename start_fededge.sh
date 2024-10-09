#!/bin/bash
if [ "$1" ]; then
  echo "Starting Edge Orchestration Service of EADRAN with conf=$1"

  export PYTHONPATH="${PYTHONPATH}:$PWD"

  python3 fed_edge/orchestration/start_edge_service.py --conf=$1 &
else
  echo "Missing config file!!!!"
fi
