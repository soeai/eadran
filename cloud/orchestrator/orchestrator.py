import argparse
import json
import uuid

from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml.connector.amqp_connector import Amqp_Connector
import qoa4ml.qoaUtils as utils
from threading import Thread
from cloud.commons.default import ServiceConfig
from commons.pipeline import Pipeline
from commons.modules import (ResourceComputing, GenerateConfiguration,
                             StartFedServer, StartTrainingContainerEdge)
import logging
import requests

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


def start_train(params, _orchestrator=None):
    logging.info("Request content: {}".format(params))
    pipeline = Pipeline(task_list=[StartFedServer(_orchestrator),
                                   ResourceComputing(),
                                   GenerateConfiguration(),
                                   StartTrainingContainerEdge(_orchestrator)],
                        params=params)
    pipeline.exec()

    # send something to others if needed
    # if orchestrator is not None:
    #     orchestrator.send("")


def start_edge(params, _orchestrator=None):
    pipeline = Pipeline([ResourceComputing(), GenerateConfiguration()], params)
    pipeline.exec()
    # send something to others if needed
    if _orchestrator is not None:
        _orchestrator.send("")


def stop_edge(params):
    pass


def request_data(params, request_id, orchestrator_obj=None):
    if orchestrator_obj is not None:
        url_mgt_service = orchestrator_obj.url_mgt_service + "/health?id=" + params['edge_id']
        edge_check = requests.get(url_mgt_service).json()
        # print(edge_check)
        if not edge_check['status'] == 1:
            routing = edge_check['status']['routing_key']
            params['request_id'] = request_id
            logging.info("Sending a request [{}] to [{}]".format(request_id, params['edge_id']))
            orchestrator_obj.send(params, routing_key=routing)


class Orchestrator(object):
    def __init__(self, config):
        self.config = utils.load_config(config)
        self.amqp_queue_in = Amqp_Collector(self.config['amqp_in'], self)
        self.amqp_queue_out = Amqp_Connector(self.config['amqp_out'], self)
        self.thread = Thread(target=self.start_receive)
        self.url_mgt_service = self.config['url_mgt_service'] + ServiceConfig.MGT_SERVICE_HOST + ":" \
                               + str(ServiceConfig.MGT_SERVICE_PORT)
        self.url_storage_service = self.config['url_storage_service'] + ServiceConfig.STORAGE_SERVICE_HOST \
                                   + ":" + str(ServiceConfig.STORAGE_SERVICE_PORT)

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        msg_type = req_msg['type']
        if msg_type == 'request':
            logging.info("Received a message from [{}] for [{}]".format(req_msg['requester'], req_msg['command']))
            # WILL DETAIL LATER
            request_id = str(uuid.uuid4())
            if req_msg['command'] == 'train_model':
                start_train(req_msg['content'], self)
            elif req_msg['command'] == 'start_edge':
                start_edge(req_msg['content'], self)
            elif req_msg['command'] == 'stop_edge':
                stop_edge(req_msg['content'])
            elif req_msg['command'] == 'request_data':
                request_data(req_msg['content'], request_id, self)

        elif msg_type == 'response':
            logging.info(
                "Received a response of request: [{}] from [{}]".format(req_msg['response_id'], req_msg['responder']))

    def send(self, msg, routing_key=None):
        self.amqp_queue_out.send_data(json.dumps(msg), routing_key=routing_key)

    def start_receive(self):
        self.amqp_queue_in.start()

    def start(self):
        self.thread.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Orchestrator')
    parser.add_argument('--conf', type=str, default='conf/config.json')
    args = parser.parse_args()

    orchestrator = Orchestrator(args.conf)
    orchestrator.start()
