import argparse
import json
# import time
# import uuid

from qoa4ml.collector.amqp_collector import AmqpCollector, HostObject, AMQPCollectorConfig
# from qoa4ml.connector.amqp_connector import AmqpConnector, AMQPConnectorConfig
import qoa4ml.utils.qoa_utils as utils
from threading import Thread
# from cloud.commons.default import Protocol
# from cloud.orchestrator.commons.pipeline import Pipeline
# from cloud.orchestrator.commons.modules import (
#     Config4Edge,
#     FedServerContainer,
#     EdgeContainer,
#     QoDContainer,
# )

import logging
# import requests

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


class Receiver(HostObject):
    def __init__(self, config):
        self.config = utils.load_config(config)
        self.amqp_queue_in = AmqpCollector(AMQPCollectorConfig(**self.config['amqp_in']['amqp_collector']['conf']), self)
        self.thread = Thread(target=self.start_receive)

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("'", '"'))
        print(req_msg)

    def start_receive(self):
        self.amqp_queue_in.start_collecting()

    def start(self):
        self.thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receive from edge")
    parser.add_argument("--conf", type=str, default="config.json")
    args = parser.parse_args()

    receiver = Receiver(args.conf)
    receiver.start()
