import json
import time
from datetime import datetime

from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers="localhost:9092",
                         value_serializer=lambda m: json.dumps(m).encode('ascii'))

with open("../../data_samples/log_from_queue.txt") as f:
    for line in f.readlines():
        body = line.replace("\'", "\"")
        mess = json.loads(body)
        mess['timestamp'] = datetime.fromtimestamp(mess['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(mess)
        producer.send("eadran_water_leak", mess)
        time.sleep(2)
# print("/".join(["1","2"]))
