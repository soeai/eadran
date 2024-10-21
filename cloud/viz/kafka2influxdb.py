import logging
from datetime import datetime
import sys
import json
from influxdb_client_3 import InfluxDBClient3, Point

if sys.version_info >= (3, 12, 0):
    import six
    sys.modules['kafka.vendor.six.moves'] = six.moves

from kafka import KafkaConsumer

with open("conf/kafka_influxdb_conf.json") as f:
    connector_conf = json.load(f)

influxdb_conf = connector_conf["influxdb_connector"]
kafka_conf = connector_conf["kafka_connector"]
client = InfluxDBClient3(
    host=influxdb_conf["url"],
    token=influxdb_conf["token"],
    org=influxdb_conf["org"],
    database=influxdb_conf["bucket"]
)

consumer = KafkaConsumer(bootstrap_servers=kafka_conf["bootstrap_servers"])
consumer.subscribe(kafka_conf["topic"])
logging.info("Subscribe topic [{}] from [{}]".format(kafka_conf["topic"], kafka_conf["bootstrap_servers"]))

for msg in consumer:
    json_obj = json.loads(msg.value)
    print(json_obj)
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
        .field("performance_post", json_obj["performance_post"]) \
        .field("performance_test", json_obj["performance_test"])
    client.write(p)
