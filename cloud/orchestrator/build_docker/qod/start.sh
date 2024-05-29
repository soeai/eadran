#!/bin/bash
echo "QoD Evaluation Module with: --service=$1 --conf=$2"

#get requirements file from storage
#if [ ! -f "$2" ]; then
#  wget $1/$2
#  pip install -r $2
#fi

#get config file from storage
if [ ! -f "$2" ]; then
  wget $1/storage/obj?id=$2 -O ./conf/client.json
fi

python3 evaluate.py --service=$1