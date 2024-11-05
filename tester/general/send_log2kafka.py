import json
import time
from datetime import datetime
import sys

if sys.version_info >= (3, 12, 0):
    import six
    sys.modules['kafka.vendor.six.moves'] = six.moves


from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers="localhost:9092",
                         value_serializer=lambda m: json.dumps(m).encode('ascii'))

with open("../../data_samples/log_water_leak_case3.txt") as f:
    for line in f.readlines():
        body = line.replace("\'", "\"")
        mess = json.loads(body)
        # mess['timestamp'] = datetime.fromtimestamp(mess['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(mess)
        producer.send("eadran_water_leak", mess)
        time.sleep(1)
# print("/".join(["1","2"]))
