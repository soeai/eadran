# This class process 2 commands:
# start/stop fed server and queue for monitoring

import argparse
import json
import logging
import subprocess
import sys
import time
import traceback
from threading import Thread
from cloud.commons.default import Protocol
import docker
import psutil
import socket
import qoa4ml.qoaUtils as utils
from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml.connector.amqp_connector import Amqp_Connector

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


class FedServerOrchestrator(object):
    def __init__(self, config, ip=None):
        self.ip = ip
        self.config = utils.load_config(config)
        self.edge_id = self.config['edge_id']
        self.containers = []
        self.amqp_queue_in = Amqp_Collector(self.config['amqp_in'], self)
        self.amqp_queue_out = Amqp_Connector(self.config['amqp_out'], self)
        self.amqp_thread = Thread(target=self.start)
        Thread(target=self.health_report).start()

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        # check if server sends command to this edge
        if req_msg['edge_id'] == self.edge_id or req_msg['edge_id'] == '*':
            logging.info("Received a request [{}] for [{}]".format(req_msg['request_id'], req_msg['command']))
            response = None
            if req_msg['command'].lower() == 'docker':
                if req_msg['params'].lower() == 'start':
                    status = []
                    for config in req_msg["docker"]:
                        status.append(self.start_container(config))
                    response = {
                        "edge_id": self.edge_id,
                        "status": int(sum(status)),
                        "detail": status
                    }

                elif req_msg['params'].lower() == 'stop':
                    status = []
                    for container in req_msg["containers"]:
                        status.append(self.stop_container(container))
                    response = {
                        "edge_id": self.edge_id,
                        "status": int(sum(status)),
                        "detail": status
                    }

            if response is not None:
                logging.info("Sending a response for request [{}]".format(req_msg['request_id']))
                # add header of message before responding
                msg = {"type": Protocol.MSG_RESPONSE,
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
            # check container is running with the same name, stop it
            logging.info('Checking if a running container with the same name exists ...')
            res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + config["options"]["--name"]],
                                 capture_output=True)

            if res.returncode == 0 and config['options']['--name'] in str(res.stdout):
                logging.info("Stopping the running container...")
                subprocess.run(["docker", "stop", config["options"]["--name"]])
                subprocess.run(["docker", "remove", config["options"]["--name"]])

            logging.info("Starting a new container...")
            command = ["docker", "run", "-d"]
            for (k, v) in config["options"].items():
                if v is not None and len(v) > 0:
                    if k == "-p":
                        for port in v:
                            command.extend(["-p", port])
                    elif k != "-d":
                        command.extend([k, v])
                else:
                    command.append(k)
            command.append(config["image"])

            if 'arguments' in config.keys():
                command.extend(config['arguments'])
            res = subprocess.run(command, capture_output=True)
            logging.info("Start container result: {}".format(res))
            self.containers.append(config["options"]["--name"])
            return res.returncode
        except Exception as e:
            logging.error("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())
        return 1

    def stop_container(self, container_name):
        try:
            logging.info('Checking if the container [{}] is running ...'.format(container_name))
            res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + container_name],
                                 capture_output=True)
            if res.returncode == 0 and str(res.stdout).find(container_name) >= 0:
                logging.info("Stopping the running container...")
                subprocess.run(["docker", "stop", container_name])
                subprocess.run(["docker", "remove", container_name])
                self.containers.pop(container_name, None)
                logging.info("The container [{}] has been stopped...".format(container_name))
        except Exception as e:
            logging.error("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())
            return 1
        return 0

    def health_report(self):
        try:
            docker_res = docker.from_env().version()
        except Exception as e:
            docker_res = {}
            print(e.__traceback__)

        health_post = {
            "edge_id": self.edge_id,
            "ip": self.config['ip'] if self.ip is None else self.ip,
            "routing_key": self.config['amqp_in']['in_routing_key'],
            "health": {
                "mem": psutil.virtual_memory()[1],
                "cpu": psutil.cpu_count(),
                "gpu": -1  # code to get GPU device here
            },
            "docker_available": docker_res  # code to check docker available or not
        }

        while True:
            # check how many container running
            self.amqp_queue_out.send_data(json.dumps(health_post), routing_key=self.config['amqp_health_report'])
            time.sleep(self.config['report_delay_time'])

            health_post['health']['mem'] = psutil.virtual_memory()[1]
            health_post['health']['cpu'] = psutil.cpu_count()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Federated Server Orchestrator Micro-Service...")
    parser.add_argument('--conf', help='config file', default="../conf/config.json")
    args = parser.parse_args()
    IPAddr = socket.gethostbyname(socket.gethostname())
    orchestrator = FedServerOrchestrator(args.conf)
    orchestrator.start_amqp()
