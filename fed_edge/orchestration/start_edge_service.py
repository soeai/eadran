# This class process 3 commands:
# 1. start/stop docker (including: fed_worker and DoD)
# 2. reported its health every 5 minutes
# 3. process data extraction (require module installed on Edge)

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
import qoa4ml.utils.qoa_utils as utils
from cloud.commons.default import Protocol
from qoa4ml.collector.amqp_collector import (
    AmqpCollector,
    AMQPCollectorConfig,
    HostObject,
)
from qoa4ml.qoa_client import QoaClient
from qoa4ml.connector.amqp_connector import AmqpConnector, AMQPConnectorConfig
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


class EdgeOrchestrator(HostObject):
    def __init__(
            self,
            config,
    ):
        self.config = utils.load_config(config)
        self.edge_id = self.config["edge_id"]
        self.containers = []
        self.amqp_queue_in = AmqpCollector(
            AMQPCollectorConfig(**self.config["amqp_in"]["amqp_collector"]["conf"]),
            self
        )
        self.amqp_queue_out = AmqpConnector(
            AMQPConnectorConfig(**self.config["amqp_out"]["amqp_connector"]["conf"]),
            health_check_disable=True
        )
        self.amqp_thread = Thread(target=self.start)
        Thread(target=self.health_report).start()

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("'", '"'))
        # check if server sends command to this edge
        if req_msg["edge_id"] == self.edge_id or req_msg["edge_id"] == "*":
            response = None
            logging.info(
                "Received a request [{}] for [{}]".format(
                    req_msg["request_id"], req_msg["command"]
                )
            )
            if req_msg["command"].lower() == "docker":
                if req_msg["params"].lower() == "start":
                    status = []
                    for config in req_msg["docker"]:
                        status.append(
                            self.start_container(config, req_msg["request_id"])
                        )
                        # start monitor
                        Thread(
                            target=container_monitor,
                            args=(
                                req_msg["amqp_connector"],
                                config["options"]["--name"],
                                req_msg["request_id"],
                                self.config["qoa_client"]
                            ),
                        ).start()
                    response = {
                        "edge_id": self.edge_id,
                        "status": int(sum(status)),
                        "detail": status,
                    }
                elif req_msg["params"].lower() == "stop":
                    status = []
                    for container in req_msg["containers"]:
                        self.stop_container(container)
                    response = {
                        "edge_id": self.edge_id,
                        "status": int(sum(status)),
                        "detail": status,
                    }
            elif req_msg["command"].lower() == Protocol.DATA_EXTRACTION_COMMAND:
                response = self.extract_data(req_msg)

            logging.info(f"Response: {response}")

            # send response back to server
            if response is not None:
                logging.info(
                    "Sending a response for request [{}]".format(req_msg["request_id"])
                )
                # add header of message before responding
                msg = {
                    "type": Protocol.MSG_RESPONSE,
                    "response_id": req_msg["request_id"],
                    "responder": self.edge_id,
                    "content": response,
                }
                logging.info(f"Response message: {msg}")
                self.amqp_queue_out.send_report(json.dumps(msg))
            else:
                logging.info("Response message is None")

    def start(self):
        self.amqp_queue_in.start_collecting()

    def start_amqp(self):
        self.amqp_thread.start()

    def start_container(self, config, request_id):
        try:
            # check container is running with the same name, stop it
            logging.info(
                "Checking if a running container with the same name exists ..."
            )
            res = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    "name=" + config["options"]["--name"],
                ],
                capture_output=True,
            )

            if res.returncode == 0 and config["options"]["--name"] in str(res.stdout):
                logging.info("Stopping the running container...")
                subprocess.run(["docker", "stop", config["options"]["--name"]])
                subprocess.run(["docker", "remove", config["options"]["--name"]])

            logging.info("Starting a new container...")
            command = ["docker", "run", "-d"]
            for k, v in config["options"].items():
                if v is not None and len(v) > 0:
                    if k == "-p":
                        for port in v:
                            command.extend(["-p", port])
                    elif k != "-d":
                        command.extend([k, v])
                else:
                    command.append(k)
            command.append(config["image"])

            if "arguments" in config.keys():
                command.extend(config["arguments"])

            command.append(request_id)  # will be attached in report model performance

            res = subprocess.run(command, capture_output=True)
            logging.info("Start container result: {}".format(res))

            self.containers.append(config["options"]["--name"])

            if asyncio.run(check_docker_running(config["options"]["--name"])):
                return 0

        except Exception as e:
            logging.error(
                "[ERROR] - Error {} while estimating contribution: {}".format(
                    type(e), e.__traceback__
                )
            )
            traceback.print_exception(*sys.exc_info())
            return 1

    def stop_container(self, container_name):
        try:
            # if container_name in self.containers:
            logging.info(
                "Checking if the container [{}] is running ...".format(container_name)
            )
            res = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=" + container_name],
                capture_output=True,
            )
            if res.returncode == 0 and str(res.stdout).find(container_name) >= 0:
                logging.info("Stopping the running container...")
                subprocess.run(["docker", "stop", container_name])
                subprocess.run(["docker", "remove", container_name])
                self.containers.pop(container_name)
                logging.info(
                    "The container [{}] has been stopped...".format(container_name)
                )
        except Exception as e:
            logging.error(
                "[ERROR] - Error {} while estimating contribution: {}".format(
                    type(e), e.__traceback__
                )
            )
            traceback.print_exception(*sys.exc_info())
            return 1
        return 0

    # this module is implemented by DP and install on edge
    def extract_data(self, req_msg):
        if not os.path.isdir("temp"):
            os.mkdir("temp")
        uuids = uuid.uuid4()
        # save request command to file
        request_filename = "temp/request_{}.json".format(uuids)
        with open(request_filename, "w") as f:
            json.dump(req_msg["data_request"], f)

        # save data config to file
        data_conf_filename = "temp/data_conf_{}.json".format(uuids)
        with open(data_conf_filename, "w") as f:
            json.dump(self.config['extracted_data_conf'], f)

        # execute data extraction module
        command = self.config["extracted_data_conf"]['extract_module']["command"]
        module_name = self.config["extracted_data_conf"]['extract_module']["module_name"]
        rep_msg = subprocess.run(
            [command, module_name, '--request', request_filename, "--conf", data_conf_filename], capture_output=True
        )
        # cleanup
        os.remove(request_filename)
        os.remove(data_conf_filename)
        try:
            # logging.info(rep_msg.stdout)
            response = {"status": 1, "description": "Error while extracting data."}
            if rep_msg.returncode == 0:
                response = json.loads(rep_msg.stdout)
            return response
        except:
            logging.error(rep_msg.stderr)
            return {"status": rep_msg.stderr, "description": "Error while extracting data."}

    def health_report(self):
        try:
            docker_res = docker.from_env().version()
        except:
            logging.warning(
                "Docker is not installed. Thus service cannot serve fully function!"
            )
            docker_res = {}

        health_post = {
            "edge_id": self.edge_id,
            "routing_key": self.config["amqp_in"]["amqp_collector"]["conf"][
                "in_routing_key"
            ],
            "health": {
                "mem": psutil.virtual_memory()[1],
                "cpu": psutil.cpu_count(),
                "gpu": -1,  # code to get GPU device here
            },
            "docker_available": docker_res,  # code to check docker available or not
        }

        while True:
            self.amqp_queue_out.send_report(
                json.dumps(health_post), routing_key=self.config["amqp_health_report"]
            )
            time.sleep(self.config["report_delay_time"])

            health_post["health"]["mem"] = psutil.virtual_memory()[1]
            health_post["health"]["cpu"] = psutil.cpu_count()


async def check_docker_running(container_name: str):
    """Verify the status of a container by its name

    :param container_name: the name of the container
    :return: boolean or None
    """
    RUNNING = "running"
    # Connect to Docker using the default socket or the configuration
    # in your environment
    docker_client = docker.from_env()

    await asyncio.sleep(5)

    try:
        container = docker_client.containers.get(container_name)
        container_state = container.attrs["State"]
        return container_state["Status"] == RUNNING
    except docker.errors.NotFound:
        logging.info(f"Container '{container_name}' not found.")
        return False
    except docker.errors.APIError as e:
        logging.info(f"Error communicating with Docker API: {e}")
        return False
    finally:
        docker_client.close()


def container_monitor(
        amqp_connector: dict, container_name, request_id, qoa_client_config
):
    print(amqp_connector)
    qoa_client_config["connector"] = [amqp_connector]
    qoa_client_config["client"]["instance_name"] = request_id
    for probe_config in qoa_client_config["probes"]:
        if probe_config["probe_type"] == "docker":
            probe_config["container_name"] = [container_name]
    client = QoaClient(config_dict=qoa_client_config)
    client.start_all_probes()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge Orchestrator Micro-Service...")
    parser.add_argument("--conf", help="config file", default="../conf/config.json")
    args = parser.parse_args()

    orchestrator = EdgeOrchestrator(args.conf)
    orchestrator.start_amqp()
