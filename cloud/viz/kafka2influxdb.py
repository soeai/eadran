import logging
from datetime import datetime, timedelta

from kafka import KafkaConsumer
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

with open("./conf/kafka_influxdb_conf.json") as f:
    connector_conf = json.load(f)

influxdb_conf = connector_conf["influxdb_connector"]
kafka_conf = connector_conf["kafka_connector"]
client = InfluxDBClient(
    url=influxdb_conf["url"],
    token=influxdb_conf["token"],
    org=influxdb_conf["org"]
)

write_api = client.write_api(write_options=SYNCHRONOUS)

consumer = KafkaConsumer(bootstrap_servers=kafka_conf["bootstrap_servers"])
consumer.subscribe(kafka_conf["topic"])
logging.info("Subscribe topic [{}] from [{}]".format(kafka_conf["topic"], kafka_conf["bootstrap_servers"]))
# with open("../CostService/cost_from_spark.txt") as f:
#    for line in f:
#       line = line.replace("\'", "\"")
#       json_obj = json.loads(line)
#       print(json_obj)
#       .tag("run_id", json_obj["run_id"])\
#       .tag("task_id","{:03}".format(json_obj["train_round"]))\
#      + timedelta(days=223)

for msg in consumer:
    json_obj = json.loads(msg.value)
    dt = datetime.fromisoformat(json_obj["timestamp"])
    p = Point(json_obj["model_id"]).time(dt) \
        .tag("dataset_id", json_obj["dataset_id"]) \
        .tag("run_id", json_obj["run_id"]) \
        .tag("task_id", "{:03}".format(json_obj["train_round"])) \
        .field("cost_resource", json_obj["cost_resource"]) \
        .field("cost_qom", json_obj["cost_qom"]) \
        .field("cost_qod", json_obj["cost_qod"]) \
        .field("cost_context", json_obj["cost_context"]) \
        .field("improvement_diff", json_obj["improvement_diff"]) \
        .field("performance", json_obj["performance"])

    write_api.write(bucket=influxdb_conf["bucket"], org=influxdb_conf["org"], record=p)
