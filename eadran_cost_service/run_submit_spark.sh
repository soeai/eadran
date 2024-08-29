#!/bin/bash
#,com.datastax.spark:spark-cassandra-connector_2.12:3.2.0
#--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1
export SPARK_HOME=/Users/Storage/Soft/spark-3.0.1-bin-hadoop3.2
cd $SPARK_HOME/bin
./spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
/Users/dungcao/IdeaProjects/FedMarket/out/artifacts/FedMarket_jar/FedMarket.jar \
/Users/Storage/checkpoint \
192.168.90.54:9092 \
fedmarketplace-spark \
fedmarketplace-influxdb \
/Users/dungcao/IdeaProjects/FedMarket/fraud_cost_formula.csv