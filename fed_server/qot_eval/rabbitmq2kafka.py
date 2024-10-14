import argparse
import json
from threading import Thread

import qoa4ml.utils.qoa_utils as utils
from kafka import KafkaProducer
from qoa4ml.collector.amqp_collector import AmqpCollector
from qoa4ml.collector.host_object import HostObject
from qoa4ml.config.configs import AMQPCollectorConfig


class MessageProxy(HostObject):
    def __init__(self, proxy_ip, topic):
        self.config = utils.load_config('fed_server/conf/queue2kafka.json')
        self.config['amqp_connector']['conf'] = str(proxy_ip)
        self.topic = topic
        self.amqp_queue_in = AmqpCollector(AMQPCollectorConfig(**self.config['amqp_in']['amqp_collector']['conf']),
                                           self)
        self.file = open("qot_result.log", "w")
        # self.producer = KafkaProducer(bootstrap_servers=self.config['kafka_connector']['bootstrap_servers'],
        #                  value_serializer=lambda m: json.dumps(m).encode('ascii'))

        self.thread = Thread(target=self.start_receive)

    def message_processing(self, ch, method, props, body):
        mess = json.loads(str(body.decode("utf-8")).replace("'", '"'))
        self.file.writelines(mess)
        # self.producer.send(self.topic, mess)

    def start_receive(self):
        self.amqp_queue_in.start_collecting()

    def start(self):
        self.thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receive from edge")
    parser.add_argument("--proxy", type=str)
    parser.add_argument("--topic", type=str)
    args = parser.parse_args()

    proxy = MessageProxy(args.proxy, args.topic)
    proxy.start()
