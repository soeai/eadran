#!/bin/bash
echo "Starting Federated Client with: --storage=$1 --requirements=$2 --conf="

#get requirements file from storage
#if [ ! -f "$2" ]; then
#  wget $1/$2
#  pip install -r $2
#fi

#get config file from storage
if [ ! -f "$2" ]; then
  wget $1?id=$2
fi

python client.py