import argparse
import json
import time
import uuid
import datetime as dt
from qoa4ml.collector.amqp_collector import AmqpCollector, HostObject, AMQPCollectorConfig
from qoa4ml.connector.amqp_connector import AmqpConnector, AMQPConnectorConfig
import qoa4ml.utils.qoa_utils as utils
from threading import Thread
from cloud.commons.default import Protocol
from cloud.orchestrator.commons.pipeline import Pipeline
from cloud.orchestrator.commons.modules import (
    Config4Edge,
    FedServerContainer,
    EdgeContainer,
    QoDContainer,
)
import logging
import requests

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


def start_training_process(params, request_id, _orchestrator=None):
    params["request_id"] = request_id
    pipeline = Pipeline(
        task_list=[
            FedServerContainer(_orchestrator),
            Config4Edge(_orchestrator),
            EdgeContainer(_orchestrator, config=_orchestrator.docker_image_conf),
        ],
        params=params,
    )
    pipeline.exec()


def start_container_at_edge(params, request_id, _orchestrator=None):
    params["request_id"] = request_id
    pipeline = Pipeline([Config4Edge(_orchestrator)], params)
    pipeline.exec()


def stop_container_at_edge(params, request_id, _orchestrator=None):
    params["request_id"] = request_id
    pass


def start_qod_container_at_edge(params, request_id, _orchestrator=None):
    params["request_id"] = request_id
    pipeline = Pipeline([QoDContainer(_orchestrator)], params)
    pipeline.exec()


def data_extraction(params, request_id, _orchestrator=None):
    if _orchestrator is not None:
        count = 0
        while True:
            url_mgt_service = (
                    _orchestrator.url_mgt_service + "/health?id=" + params["edge_id"]
            )
            edge_check = requests.get(url_mgt_service).json()
            if edge_check["code"] == 0:
                routing = edge_check["result"]["routing_key"]
                params["request_id"] = request_id
                params["command"] = Protocol.DATA_EXTRACTION_COMMAND
                logging.info(
                    "Sending a request [{}] to [{}]".format(
                        request_id, params["edge_id"]
                    )
                )
                _orchestrator.send(params, routing_key=routing)
                _orchestrator.handling_edges[request_id] = [params["edge_id"]]
                break
            elif count < 5:
                logging.info("Edge is not available, sleeping 5 minutes to retry.")
                time.sleep(5 * 60)
            else:
                break


class Orchestrator(HostObject):
    def __init__(self, config, docker_image_conf):
        self.config = utils.load_config(config)
        self.amqp_queue_in = AmqpCollector(AMQPCollectorConfig(**self.config['amqp_in']['amqp_collector']['conf']),
                                           self)
        self.amqp_queue_out = AmqpConnector(AMQPConnectorConfig(**self.config['amqp_out']['amqp_connector']['conf']),
                                            health_check_disable=True)
        self.thread = Thread(target=self.start_receive)
        self.url_mgt_service = self.config["url_mgt_service"]
        self.url_storage_service = self.config["url_storage_service"]
        self.docker_image_conf = docker_image_conf
        self.processing_tasks = {}
        self.handling_edges = {}

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("'", '"'))
        msg_type = req_msg["type"]
        if msg_type == Protocol.MSG_REQUEST:
            logging.info(
                "Received a message from [{}] for [{}]".format(
                    req_msg["requester"], req_msg["command"]
                )
            )
            request_id = req_msg['request_id']
            self.processing_tasks[request_id] = (time.time(), req_msg['content'], req_msg["requester"])
            if req_msg["command"] == Protocol.TRAIN_MODEL_COMMAND:
                Thread(target=start_training_process, args=(req_msg["content"], request_id, self)).start()
            elif req_msg["command"] == Protocol.START_CONTAINER_COMMAND:
                Thread(target=start_container_at_edge, args=(req_msg["content"], request_id, self)).start()
            elif req_msg["command"] == Protocol.STOP_CONTAINER_COMMAND:
                Thread(target=stop_container_at_edge, args=(req_msg["content"], request_id, self)).start()
            elif req_msg["command"] == Protocol.DATA_EXTRACTION_COMMAND:
                Thread(target=data_extraction, args=(req_msg["content"], request_id, self)).start()
            elif req_msg["command"] == Protocol.DATA_QOD_COMMAND:
                Thread(target=start_qod_container_at_edge, args=(req_msg["content"], request_id, self)).start()

        # {'type': 'response',
        #  'response_id': '54b8ed47-82e9-4e78-9efc-610728484dfa',
        #  'responder': 'edge002',
        #  'content':
        #      {'edge_id': 'edge002',
        #       'status': 0,
        #       'detail': [0]}
        #  }
        elif msg_type == Protocol.MSG_RESPONSE:
            logging.info(
                "Received a response of request: [{}] from [{}]".format(
                    req_msg["response_id"], req_msg["responder"]
                )
            )
            if req_msg["responder"] in self.handling_edges[req_msg["response_id"]]:
                self.handling_edges[req_msg["response_id"]].remove(req_msg["responder"])

            if req_msg["response_id"] in self.processing_tasks.keys():
                _, msg_task, requestor = self.processing_tasks.pop(req_msg["response_id"])
                logging.info("Responding request [{}] of [{}]".format(req_msg["response_id"], requestor))
                # CALL POST TO SERVICE HERE
                requests.post(self.url_mgt_service + "/service/report",
                              {"code": 0,
                               "request_id": req_msg["response_id"]})
                # self.send({"code": 0,
                #            "timestamp": str(dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S')),
                #            "request_id": req_msg["response_id"]},
                #           requestor + ".#")

                if msg_task["command"] == Protocol.DATA_EXTRACTION_COMMAND:
                    # if consumer as to evaluate qod while sending a data query, DO IT
                    if msg_task["data_request"]["qod"]["evaluate"]:
                        # Build config for edge here from msg_task and res_msg (response from edge data extraction)
                        # send command to QoD Evaluation
                        resp_content = req_msg["content"]
                        params = {
                            "edge_id": msg_task["edge_id"],
                            "model_id": msg_task["model_id"],
                            "consumer_id": Protocol.ACTOR_ORCHESTRATOR,
                            "data_conf": resp_content["read_info"],
                        }

                        request_id = str(uuid.uuid4())
                        self.processing_tasks[request_id] = (time.time(), req_msg, )
                        Thread(target=start_qod_container_at_edge, args=(params, request_id, self)).start()

    def send(self, msg, routing_key=None):
        self.amqp_queue_out.send_report(json.dumps(msg), routing_key=routing_key)

    def start_receive(self):
        self.amqp_queue_in.start_collecting()

    def start(self):
        self.thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrator")
    parser.add_argument("--conf", type=str, default="conf/config.json")
    parser.add_argument("--image", type=str, default="conf/image4edge.json")
    args = parser.parse_args()

    orchestrator = Orchestrator(args.conf, args.image)
    orchestrator.start()
