#!/bin/bash
echo "Starting Federated Client with: --storage=$1 --requirements=$2 --conf=$3"

#get requirements file from storage
if [ ! -f "$2" ]; then
  wget $1/$2
  pip install -r $2
fi

#get config file from storage
if [ ! -f "$3" ]; then
  wget $1/$3
fi

python3 client.py --conf=$3