import argparse
import json
import time
import uuid

from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml.connector.amqp_connector import Amqp_Connector
import qoa4ml.qoaUtils as utils
from threading import Thread
from cloud.commons.default import Protocol
from cloud.orchestrator.commons.pipeline import Pipeline
from cloud.orchestrator.commons.modules import Config4Edge, FedServerContainer, EdgeContainer

import logging
import requests

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


def start_training_process(params, request_id, _orchestrator=None):
    params['request_id'] = request_id
    pipeline = Pipeline(task_list=[FedServerContainer(_orchestrator),
                                   Config4Edge(_orchestrator),
                                   EdgeContainer(_orchestrator)],
                        params=params)
    pipeline.exec()


def start_container_at_edge(params, request_id, _orchestrator=None):
    params['request_id'] = request_id
    pipeline = Pipeline([Config4Edge(_orchestrator)], params)
    pipeline.exec()


def stop_container_at_edge(params, request_id, _orchestrator=None):
    params['request_id'] = request_id
    pass


def start_qod_container_at_edge(params, request_id, _orchestrator=None):
    params['request_id'] = request_id
    pass


def data_extraction(params, request_id, _orchestrator=None):
    if _orchestrator is not None:
        count = 0
        while True:
            url_mgt_service = _orchestrator.url_mgt_service + "/health?id=" + params['edge_id']
            edge_check = requests.get(url_mgt_service).json()
            if edge_check['status'] == 0:
                routing = edge_check['status']['routing_key']
                params['request_id'] = request_id
                params['command'] = Protocol.DATA_EXTRACTION_COMMAND
                logging.info("Sending a request [{}] to [{}]".format(request_id, params['edge_id']))
                _orchestrator.send(params, routing_key=routing)
                break
            elif count < 5:
                logging.info("Edge is not available, sleeping 5 minutes to retry.")
                time.sleep(5 * 60)
            else:
                break


class Orchestrator(object):
    def __init__(self, config):
        self.config = utils.load_config(config)
        self.amqp_queue_in = Amqp_Collector(self.config['amqp_in'], self)
        self.amqp_queue_out = Amqp_Connector(self.config['amqp_out'], self)
        self.thread = Thread(target=self.start_receive)
        self.url_mgt_service = self.config['url_mgt_service']
        self.url_storage_service = self.config['url_storage_service']

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        msg_type = req_msg['type']
        if msg_type == Protocol.MSG_REQUEST:
            logging.info("Received a message from [{}] for [{}]".format(req_msg['requester'], req_msg['command']))
            # WILL DETAIL LATER
            request_id = str(uuid.uuid4())
            if req_msg['command'] == Protocol.TRAIN_MODEL_COMMAND:
                start_training_process(req_msg['content'], self)
            elif req_msg['command'] == Protocol.START_CONTAINER_COMMAND:
                start_container_at_edge(req_msg['content'], self)
            elif req_msg['command'] == Protocol.STOP_CONTAINER_COMMAND:
                stop_container_at_edge(req_msg['content'])
            elif req_msg['command'] == Protocol.DATA_EXTRACTION_COMMAND:
                data_extraction(req_msg['content'], request_id, self)
            elif req_msg['command'] == Protocol.DATA_QOD_COMMAND:
                start_qod_container_at_edge(req_msg['content'], self)

        elif msg_type == Protocol.MSG_RESPONSE:
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

