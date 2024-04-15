#!/bin/bash
echo "Starting Federated Client with: port=$1 --- epochs=$2"

#if [ ! -f "$2" ]; then
#  wget https://github.com/dungcao/fedmarketplace.data/raw/main/fraud_detection/$2 .
#fi
#if [ ! -f "$3" ]; then
#  wget https://github.com/dungcao/fedmarketplace.data/raw/main/fraud_detection/$3 .
#fi

wget http://$1/storage/requirements.txt

pip install -r requirements.txt

wget http://training-code

wget http://read_data_code

wget http://config_file

wget http://pre-train_model

python3 client.py --conf=$1