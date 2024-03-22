# This class process 2 commands:
# start/stop fed server and queue for monitoring

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
import uuid
from threading import Thread
import docker
import psutil
import qoa4ml.qoaUtils as utils
from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml.connector.amqp_connector import Amqp_Connector
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


class FedServerOrchestrator(object):
    def __init__(self, config, ):
        self.config = utils.load_config(config)
        self.docker_client = None
        self.edge_id = self.config['edge_id']
        self.containers = {}
        self.amqp_queue_in = Amqp_Collector(self.config['amqp_in'], self)
        self.amqp_queue_out = Amqp_Connector(self.config['amqp_out'], self)
        self.amqp_thread = Thread(target=self.start)
        # Thread(target=self.health_report).start()

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        # check if server sends command to this edge
        if req_msg['edge_id'] == self.edge_id or req_msg['edge_id'] == '*':
            logging.info("Received a request [{}] for [{}]".format(req_msg['request_id'], req_msg['command']))
            response = None
            if req_msg['command'].lower() == 'docker':
                # {
                #     "edge_id": "specific resource id or *",
                #     "command": "docker",
                #     "params": "start",
                #     "config":[
                #         {
                #             "image": "repo:docker_image_rabbitmq",
                #             "container_name": "rabbit_container_01",
                #             "detach": "True",
                #             "binding_port":{
                #                 "5672/tcp":"5672",
                #                 "5671/tcp":"5671",
                #                 "25672/tcp":"25672",
                #                 "15672/tcp":"15672"}
                #         },
                #         {
                #             "image": "repo:docker_image_fedserver",
                #             "container_name": "fedserver_container_01",
                #             "detach": "True",
                #             "binding_port":{
                #                 "1111/tcp":"2222",
                #                 "3333/tcp":"4444"}
                #         }
                #     ],
                #     "conf_path": "configuration path in docker container, optional"
                # }
                self.docker_client = docker.from_env()
                if req_msg['params'].lower() == 'start':
                    for config in req_msg["config"]:
                        self.start_container(config)
                    response = {
                        "edge_id": self.edge_id,
                        "status": "success"
                    }
                # {
                #     "edge_id": "specific resource id or *",
                #     "command": "docker",
                #     "params": "stop",
                #     "containers": ["rabbit_container_01", "fedserver_container_01"]
                # }
                elif req_msg['params'].lower() == 'stop':
                    for container in req_msg["containers"]:
                        self.stop_container(container)
                    response = {
                        "edge_id": self.edge_id,
                        "status": "success"
                    }
            # elif req_msg['command'].lower() == 'data_extract':
            #     response = self.extract_data(req_msg)

            # send response back to server
            if response is not None:
                logging.info("Sending a response for request [{}]".format(req_msg['request_id']))
                # add header of message before responding
                msg = {"type": "response",
                       "response_id": req_msg['request_id'],
                       "responder": self.edge_id,
                       "content": response}
                self.amqp_queue_out.send_data(json.dumps(msg))

    def start(self):
        self.amqp_queue_in.start()

    def start_amqp(self):
        self.amqp_thread.start()

    def start_container(self, config):
        try:
            self.containers[config["container_name"]] = self.docker_client.containers.run(image=config["image"],
                                                                                          detach=bool(config["detach"]),
                                                                                          name=config["container_name"],
                                                                                          ports=config["binding_port"])
        except Exception as e:
            print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())

    def stop_container(self, container_name):
        try:
            self.containers[container_name].stop()
            self.connector.pop(container_name, None)
        except Exception as e:
            print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Federated Server Orchestrator Micro-Service...")
    parser.add_argument('--conf', help='config file', default="../conf/config.json")
    args = parser.parse_args()

    orchestrator = FedServerOrchestrator(args.conf)
    orchestrator.start_amqp()
