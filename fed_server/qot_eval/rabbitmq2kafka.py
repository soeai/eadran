import json
from qoa4ml.collector.amqp_collector import Amqp_Collector
from kafka import KafkaProducer
import logging


class MessageProxy(object):
    # Client can define any class as long as it has "message_processing" method
    def __init__(self, kafka, topic):
        # TO DO
        self.kafka = kafka
        self.topic = topic
        logging.info("Adaptor RabbitMQ_2_Kafka started ....")

    def message_processing(self, ch, method, props, body):
        # This is a call back function form Amqp_Collector
        # Report processing here
        # current processing is print to console
        body = body.replace("\'", "\"")
        mess = json.loads(str(body.decode("utf-8")))
        # print(mess)
        # current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.kafka.send(self.topic, mess)


with open("../conf/queue2kafka.json") as f:
    connector_conf = json.load(f)
producer = KafkaProducer(bootstrap_servers=connector_conf['kafka_connector']['bootstrap_servers'],
                         value_serializer=lambda m: json.dumps(m).encode('ascii'))

client = MessageProxy(producer, connector_conf['kafka_connector']['topic'])
collector = Amqp_Collector(connector_conf['amqp_connector']['conf'], host_object=client)
collector.start()
