import time
import uuid
import pika
import json
# from qoa4ml.collector.amqp_collector import AmqpCollector, HostObject
from qoa4ml.config.configs import AMQPConnectorConfig
from qoa4ml.connector.amqp_connector import AmqpConnector
import qoa4ml.utils.qoa_utils as utils
from threading import Thread
from cloud.commons.default import Protocol


class DataService_Simulation(object):
    def __init__(self):
        self.config = utils.load_config('../../fed_edge/conf/config.json')
        # self.amqp_collector = Amqp_Collector(self.config['amqp_in'],self)
        self.amqp_connector = AmqpConnector(AMQPConnectorConfig(**self.config["amqp_out"]["amqp_connector"]["conf"]))
        # self.thread = Thread(target=self.start_receive)
        # self.thread.start()

    # def message_processing(self, ch, method, props, body):
    #     req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
    #     print(req_msg)

    def send(self, msg):
        self.amqp_connector.send_report(json.dumps(msg))

    # def start_receive(self):
    #     self.amqp_collector()


client = DataService_Simulation()
with open('../../apps/water_leak/scenario_base/data_extract_jsons/edge01.json') as f:
    req = json.load(f)
    # add message header
    msg = {"type": Protocol.MSG_REQUEST,
           "requester": Protocol.ACTOR_DATA_SERVICE,
           "command": Protocol.DATA_EXTRACTION_COMMAND,
           "request_id": str(uuid.uuid4()),
           "content": req}
    client.send(msg)

# time.sleep(5)
# with open('../../apps/water_leak/scenario_base/data_extract_jsons/edge02.json') as f:
#     req = json.load(f)
#     # add message header
#     msg = {"type": Protocol.MSG_REQUEST,
#            "requester": Protocol.ACTOR_DATA_SERVICE,
#            "command": Protocol.DATA_EXTRACTION_COMMAND,
#            "request_id": str(uuid.uuid4()),
#            "content": req}
#     client.send(msg)
