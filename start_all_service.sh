#!/bin/bash
echo "Starting services of EADRAN"

export PYTHONPATH="${PYTHONPATH}:$PWD"

python3 cloud/services/service.py --conf=cloud/services/conf/config.json &
python3 cloud/services/storage.py --conf=cloud/services/conf/storage_config.json &