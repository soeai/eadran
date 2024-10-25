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

logging.basicConfig(
    filename='eadran_edge.logs',  # The file where logs will be saved
    filemode='a',  # 'a' to append, 'w' to overwrite
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


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
            AMQPConnectorConfig(**self.config["amqp_out"]["amqp_connector"]["conf"])
        )
        self.amqp_thread = Thread(target=self.start)
        Thread(target=self.health_report).start()

        if not os.path.isdir("working"):
            os.mkdir("working")
        if not os.path.isdir("working/{}_conf".format(self.edge_id)):
            os.mkdir("working/{}_conf".format(self.edge_id))
        if not os.path.isdir("working/{}_share".format(self.edge_id)):
            os.mkdir("working/{}_share".format(self.edge_id))

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

            if req_msg["command"].lower() == Protocol.DOCKER_COMMAND:
                if req_msg["params"].lower() == "start":
                    if "config" in req_msg.keys():
                        file_config_name = "working/{}_conf/config_{}.json".format(self.edge_id, req_msg["request_id"])
                        with open(file_config_name, 'w') as f:
                            json.dump(req_msg['config'], f)
                        status = []
                        run_code = 0
                        for config in req_msg["docker"]:
                            r = self.start_container(config, req_msg["request_id"], file_config_name)
                            run_code += r
                            if r == 0 and req_msg['monitor']:
                                Thread(
                                    target=self.container_monitor,
                                    args=(
                                        req_msg['config'],
                                        req_msg["request_id"],
                                        config["options"]["--name"]
                                    ),
                                    name="monitor_edge_container_process"
                                ).start()
                            status.append({config["options"]["--name"]: r})
                        response = {
                            "edge_id": self.edge_id,
                            "status": int(run_code),
                            "detail": status,
                        }
                        # clean config
                        os.remove(file_config_name)

                elif req_msg["params"].lower() == "stop":
                    status = []
                    for container in req_msg["containers"]:
                        status.append({"container": self.stop_container(container)})
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
                    "content": response
                }
                logging.info(f"Response message: {msg}")
                self.amqp_queue_out.send_report(json.dumps(msg))
            else:
                logging.info("Response message is None")

    def start(self):
        self.amqp_queue_in.start_collecting()

    def start_amqp(self):
        self.amqp_thread.start()

    def start_container(self, config, request_id, conf_file):
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
            folder_path = conf_file.split("/")[:-1]
            filename = conf_file.split("/")[-1]
            folder_path = os.path.abspath("/".join(folder_path))
            mount_conf = "type=bind,source={},target={}".format(
                folder_path, "/conf/"
            )
            command.extend(["--mount", mount_conf])
            command.extend(["-v", os.path.abspath("working/{}_share:/share_volume".format(self.edge_id))])

            command.append(config["image"])

            if "arguments" in config.keys():
                command.extend(config["arguments"])

            command.append(request_id)  # will be attached in report model performance
            command.append(filename)

            logging.info("Start container with command: {}".format(command))

            res = subprocess.run(command, capture_output=True)
            logging.info("Start container result: {}".format(res))

            self.containers.append(config["options"]["--name"])

            if asyncio.run(check_docker_running(config["options"]["--name"])):
                return 0
            return 1

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
        if not os.path.isdir("working/{}_data".format(self.edge_id)):
            os.mkdir("working/{}_data".format(self.edge_id))

        uuids = uuid.uuid4()
        # save request command to file
        request_filename = "working/{}_data/request_{}.json".format(self.edge_id,uuids)
        with open(request_filename, "w") as f:
            json.dump(req_msg["data_request"], f)

        # save data config to file
        data_conf_filename = "working/{}_data/conf_{}.json".format(self.edge_id, uuids)
        with open(data_conf_filename, "w") as f:
            json.dump(self.config['extracted_data_conf'], f)

        # execute data extraction module
        command = self.config["extracted_data_conf"]['extract_module']["command"]
        module_name = self.config["extracted_data_conf"]['extract_module']["module_name"]
        rep_msg = subprocess.run(
            [command, module_name, '--request', request_filename, "--conf", data_conf_filename], capture_output=True
        )
        try:
            logging.info(rep_msg.stdout)
            response = {"status": 1, "description": "Error while extracting data."}
            if rep_msg.returncode == 0:
                response = json.loads(rep_msg.stdout)
            # cleanup
            # os.remove(request_filename)
            # os.remove(data_conf_filename)
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
            "type": "edge",
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

    def container_monitor(self, client_conf, request_id, container_name):
        BYTES_TO_MB = 1024.0 * 1024.0

        client_info = {
            "name" : client_conf['edge_id'],
            "user_id" :client_conf['consumer_id'],
            "username": "edge_container",
            "instance_name": request_id,
            "stage_id": "eadran:" + client_conf['edge_id'],
            "functionality": client_conf['dataset_id'],
            "application_name": client_conf['model_id'],
            "role": 'eadran:mlm_resource',
            "run_id": str(client_conf['run_id']),
            "custom_info": ""
        }

        qoa4ml_conf = {
            "client": client_info,
            "connector": [client_conf["amqp_connector"]]
        }

        # logging.info("monitoring: ", qoa4ml_conf)
        qoa4ml_client = QoaClient(config_dict=qoa4ml_conf)
        docker_client = docker.from_env()  # Create a Docker client from environment variables
        try:
            container = docker_client.containers.get(container_name)  # Get the container by name
            logging.info(f"Monitoring stats for container '{container_name}'...")

            while True:
                if asyncio.run(check_docker_running(container_name)):
                    stats = container.stats(stream=False)  # Get stats once

                    usage_delta = (
                            stats["cpu_stats"]["cpu_usage"]["total_usage"]
                            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    )
                    system_delta = (
                            stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    )
                    len_cpu = stats["cpu_stats"]["online_cpus"]
                    cpu_percentage = (usage_delta / system_delta) * len_cpu * 100

                    share_variables = None
                    if os.path.exists("working/{}_share/{}.json".format(self.edge_id, self.edge_id)):
                        with open("working/{}_share/{}.json".format(self.edge_id, self.edge_id)) as f:
                            share_variables = json.load(f)

                    if share_variables is not None and share_variables['status'] == 'start':
                        report = {"cpu_percentage": cpu_percentage,
                                  "memory_usage": stats["memory_stats"]["usage"] / BYTES_TO_MB
                                  }
                        qoa4ml_client.report(report={"train_round": share_variables['train_round'],
                                                     "resource_monitor": report}, submit=True)
                        # print(f"CPU Percentage: {stats['cpu_stats']['cpu_usage']['total_usage']}")
                        # print(f"Memory Usage: {stats['memory_stats']['usage']} bytes")
                        # print(f"Memory Limit: {stats['memory_stats']['limit']} bytes")
                        # print(f"Network I/O: {stats['networks']}")
                else:
                    break
                time.sleep(self.config['monitor_frequency'])  # Wait before getting stats again

        except docker.errors.NotFound:
            print(f"Container '{container_name}' not found.")
        except KeyboardInterrupt:
            print("Monitoring stopped.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge Orchestrator Micro-Service...")
    parser.add_argument("--conf", help="config file", default="../conf/config.json")
    args = parser.parse_args()

    orchestrator = EdgeOrchestrator(args.conf)
    orchestrator.start_amqp()
