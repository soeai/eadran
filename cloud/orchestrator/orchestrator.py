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

logging.basicConfig(
    filename='orchestrator.logs',  # The file where logs will be saved
    filemode='a',  # 'a' to append, 'w' to overwrite
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    level=logging.INFO)
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
    pipeline = Pipeline(
        task_list=[Config4Edge(_orchestrator),
                   EdgeContainer(_orchestrator, config=_orchestrator.docker_image_conf)],
        params=params)
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
        self.amqp_queue_out = AmqpConnector(AMQPConnectorConfig(**self.config['amqp_out']['amqp_connector']['conf']))
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
            logging.info("Received a message from [{}] for [{}]".format(req_msg["requester"], req_msg["command"]))

            # {
            #     "type": Protocol.MSG_REQUEST,
            #     "requester": Protocol.ACTOR_DATA_SERVICE,
            #     "command": Protocol.DATA_QOD_COMMAND,
            #     "request_id": request_id,
            #     "content": json_msg,
            # }

            request_id = req_msg['request_id']
            self.processing_tasks[request_id] = (req_msg['content'],
                                                 req_msg["requester"],
                                                 req_msg["command"])
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

        # {
        #     "type": Protocol.MSG_RESPONSE,
        #     "response_id": req_msg['request_id'],
        #     "responder": edge_id,
        #     "content": response
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
                _, requestor, command = self.processing_tasks.pop(req_msg["response_id"])
                # CALL POST TO SERVICE HERE
                if command != Protocol.DATA_QOD_COMMAND:
                    r = requests.post(url=self.url_mgt_service + "/service/report",
                                      json={"type": "response",
                                            "code": 0,
                                            "request_id": req_msg["response_id"],
                                            "result": req_msg['content']})
                    logging.info("Respond request [{}] of [{}]: {}".format(req_msg["response_id"],
                                                                           requestor,
                                                                           r.status_code))
                # self.send({"code": 0,
                #            "timestamp": str(dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S')),
                #            "request_id": req_msg["response_id"]},
                #           requestor + ".#")

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
