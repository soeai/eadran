import uuid

import pika
import json
from qoa4ml.collector.amqp_collector import AmqpCollector
from qoa4ml.connector.amqp_connector import AmqpConnector
import qoa4ml.utils as utils
from threading import Thread


class Simulation(object):
    def __init__(self):
        # self.config = utils.load_config('../../fed_server/conf/config.json')
        # self.amqp_collector = Amqp_Collector(self.config['amqp_in'],self)
        # self.amqp_connector = Amqp_Connector(self.config['amqp_out'],self)
        # self.thread = Thread(target=self.start_receive)
        # self.thread.start()
        self.config = {
                "end_point":"...",
                "exchange_name": "fedmarketplace",
                "exchange_type": "topic",
                "out_routing_key": "edge.fedserver001"
              }
        self.amqp_connector = AmqpConnector(self.config, self)

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        print(req_msg)

    def send(self, msg):
        self.amqp_connector.send_data(json.dumps(msg))

    def start_receive(self):
        self.amqp_collector.start()


client = Simulation()
with open('request.json') as f:
    req = json.load(f)
    # msg = {
    #     "edge_id": "DE001",
    #     "command":"ping"
    #        }
    # add message header
    msg = {"type":"request",
           "requester":"orchestrator",
            "command": "docker",
            "content": req}
    req["request_id"] = request_id = str(uuid.uuid4())
    client.send(req)
    print(req)









    # session_id: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImxvbmciLCJwYXNzd29yZCI6InNkYWRhIiwicm9sZSI6IjEifQ.g0qUNqUVtaQTGgMxokH1rCPl4PnxsH4mHo7M0H8w_7E