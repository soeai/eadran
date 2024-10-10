#!/bin/bash
echo "Starting Federated Client with: --service=$1 --request_id=$2 --conf=$3"

#get requirements file from storage
#if [ ! -f "$2" ]; then
#  wget $1/$2
#  pip install -r $2
#fi

#get config file from storage
#if [ ! -f "$2" ]; then
#  wget $1/storage/obj?id=$2 -O ./conf/client.json
#fi

# check python3 vs current environment from the docker instance
python client.py --service=$1 --sessionid=$2 --conf=./conf/$3
