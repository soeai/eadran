import pika
import json
from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml.connector.amqp_connector import Amqp_Connector
import qoa4ml.utils as utils
from threading import Thread


class DataService_Simulation(object):
    def __init__(self):
        self.config = utils.load_config('../fed_edge/data_extraction/temp/config.json')
        # self.amqp_collector = Amqp_Collector(self.config['amqp_in'],self)
        self.amqp_connector = Amqp_Connector(self.config['amqp_out'],self)
        # self.thread = Thread(target=self.start_receive)
        # self.thread.start()

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        print(req_msg)

    def send(self, msg):
        self.amqp_connector.send_data(json.dumps(msg))

    # def start_receive(self):
    #     self.amqp_collector.start()


client = DataService_Simulation()
with open('data_request.json') as f:
    req = json.load(f)
    # msg = {
    #     "edge_id": "DE001",
    #     "command":"ping"
    #        }
    # add message header
    msg = {"type":"request",
           "requester":"dataservice",
            "command": "request_on_data",
            "content": req}
    client.send(msg)