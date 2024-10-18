#!/bin/bash
echo "QoD Evaluation Module with: --sessionid=$1 --conf=$2"

#get requirements file from storage
#if [ ! -f "$2" ]; then
#  wget $1/$2
#  pip install -r $2
#fi

#get config file from storage
#if [ ! -f "$2" ]; then
#  wget $1/storage/obj?id=$2 -O ./conf/qod.json
#fi

python3 evaluate.py ---sessionid=$1 --conf=$2