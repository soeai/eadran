# This class process 3 commands:
# 1. start/stop docker
# 2. reported its health every 5 minutes
# 3. process data extraction

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


class EdgeOrchestrator(object):
    def __init__(self, config, ):
        self.config = utils.load_config(config)
        # self.docker_client = None
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
                if req_msg['command'].lower() == 'docker':


        # {'edge_id': 'edge001', 'command': 'docker', 'params': 'start', 'docker': [
        #     {'image': 'trungdonggg/edge:latest',
        #      'options': {'--name': 'fed_worker_container_dungcao_tensorflow001',
        #                  '-mount': 'type=bind,src=/home/labsoe/Downloads/Fraud_Date/fraudTrain_processed_SMOTE_1.csv,target=/data'},
        #      'arguments': ['http://192.168.10.234:8081', '664c66d62f5b6370d9e1e716']}]}


                    if req_msg['params'].lower() == 'start':
                        status = 1
                        for config in req_msg["docker"]:
                            status = self.start_container(config)
                        response = {
                            "edge_id": self.edge_id,
                            "status": status
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
            elif req_msg['command'].lower() == 'extract_data':
                response = self.extract_data(req_msg)

            elif req_msg['command'].lower() == 'process_data':
                response = self.data_processing(req_msg)

            elif req_msg['command'].lower() == 'eval_qod':
                response = self.qod_eval(req_msg)

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

     # {'image': 'trungdonggg/edge:latest',
     #      'options': {'--name': 'fed_worker_container_dungcao_tensorflow001',
     #                  '-mount': 'type=bind,src=/home/labsoe/Downloads/Fraud_Date/fraudTrain_processed_SMOTE_1.csv,target=/data'},
     #      'arguments': ['http://192.168.10.234:8081', '664c66d62f5b6370d9e1e716']}

            # check container is running with the same name, stop it

            res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + config["options"]["--name"]],
                                 capture_output=True)
            print('check point...')
            if res.returncode == 0 and config['options']['--name'] in str(res.stdout):
                print('joined to condition...')
                subprocess.run(["docker", "stop", config["options"]["--name"]])
                subprocess.run(["docker", "remove", config["options"]["--name"]])

            command = ["docker", "run", "-d"]
            fed_port = None
            for (k, v) in config["options"].items():
                if v is not None and len(v) > 0:
                    if k == "-p":
                        for port in v:
                            command.extend(["-p", port])
                        fed_port = v[0]
                    elif k != "-d":
                        command.extend([k, v])
                else:
                    command.append(k)
            command.append(config["image"])

            # if fed_port is not None:
            #     command.append(fed_port)

            if 'arguments' in config.keys():
                command.extend(config['arguments'])
            res = subprocess.run(command, capture_output=True)
            print(res)
            self.containers.append(config["options"]["--name"])
            return res.returncode
            # self.containers[config["container_name"]] = self.docker_client.containers.run(image=config["image"],
            #                                                                               detach=bool(config["detach"]),
            #                                                                               name=config["container_name"],
            #                                                                               ports=config["binding_port"])
        except Exception as e:
            print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())
        return 1

    def stop_container(self, container_name):
        try:
            # if container_name in self.containers:
            res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + container_name],
                                 capture_output=True)
            if res.returncode == 0 and str(res.stdout).find(container_name) >= 0:
                subprocess.run(["docker", "stop", container_name])
                subprocess.run(["docker", "remove", container_name])

            # self.containers[container_name].stop()
            self.containers.pop(container_name, None)
        except Exception as e:
            print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())
            return 1
        return 0

    def extract_data(self, req_msg):
        if not os.path.isdir("temp"):
            os.mkdir('temp')
        fname = "temp/request_{}.json".format(uuid.uuid4())
        with open(fname, 'w') as f:
            # save data request to file
            json.dump(req_msg['data_request'], f)
            # execute data extraction module
        command = self.config['modules']['extract_data']['command']
        module_name = self.config['modules']['extract_data']['module_name']
        params = self.config['modules']['extract_data']['params']
        rep_msg = subprocess.run([command, module_name, params, fname], capture_output=True)
        print(rep_msg.stdout)
        response = json.loads(rep_msg.stdout)
        # cleanup
        os.remove(fname)
        return response

    def qod_eval(self, req_msg):
        if not os.path.isdir("temp"):
            os.mkdir('temp')
        fname = "temp/request_{}.json".format(uuid.uuid4())
        with open(fname, 'w') as f:
            # save data request to file
            json.dump(req_msg['data_request'], f)
            # execute data extraction module
        command = self.config['modules']['qod_eval']['command']
        module_name = self.config['modules']['qod_eval']['module_name']
        params = self.config['modules']['qod_eval']['params']
        rep_msg = subprocess.run([command, module_name, params, fname], capture_output=True)
        response = json.loads(rep_msg.stdout)
        # cleanup
        os.remove(fname)
        return response

    def data_processing(self, req_msg):
        if not os.path.isdir("temp"):
            os.mkdir('temp')
        fname = "temp/request_{}.json".format(uuid.uuid4())
        with open(fname, 'w') as f:
            # save data request to file
            json.dump(req_msg['data_request'], f)
            # execute data extraction module
        command = self.config['modules']['process_data']['command']
        module_name = self.config['modules']['process_data']['module_name']
        params = self.config['modules']['process_data']['params']
        rep_msg = subprocess.run([command, module_name, params, fname], capture_output=True)
        response = json.loads(rep_msg.stdout)
        # cleanup
        os.remove(fname)
        return response

    def health_report(self):
        while True:
            try:
                docker_res = docker.from_env().version()
            except:
                docker_res = {}

            health_post = {
                    "edge_id": self.edge_id,
                    "routing_key": self.config['amqp_in']['in_routing_key'],
                    "health": {
                        "mem": psutil.virtual_memory()[1],
                        "cpu": psutil.cpu_count(),
                        "gpu": -1  # code to get GPU device here
                    },
                    "docker_available": docker_res  # code to check docker available or not
                }
            self.amqp_queue_out.send_data(json.dumps(health_post), routing_key=self.config['amqp_health_report'])
            time.sleep(self.config['report_delay_time'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Edge Orchestrator Micro-Service...")
    parser.add_argument('--conf', help='config file', default="../conf/config.json")
    args = parser.parse_args()

    orchestrator = EdgeOrchestrator(args.conf)
    # orchestrator.start_container({'image': 'rabbitmq', 'options': {'--name': 'rabbit_container_dungcao', '-p': ['5672:5672']}})
    orchestrator.start_amqp()
