#!/bin/bash
#,com.datastax.spark:spark-cassandra-connector_2.12:3.2.0
#--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1
export SPARK_HOME=/Users/Storage/Soft/spark-3.5.1-bin-hadoop3-scala2.13
cd $SPARK_HOME/bin
./spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.1 /Users/dungcao/PycharmProjects/eadran/eadran_cost_service/out/artifacts/eadran_cost_service_jar/eadran_cost_service.jar /Users/Storage/checkpoint localhost:9092 eadran_water_leak eadran_influxdb /Users/dungcao/PycharmProjects/eadran/eadran_cost_service/cost_formula.json