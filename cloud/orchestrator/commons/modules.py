import logging
import sys
import traceback
from abc import ABC, abstractmethod

import qoa4ml.utils.qoa_utils as utils
import requests
import time

from cloud.commons.default import Protocol

logging.basicConfig(
    filename='orchestrator.logs',  # The file where logs will be saved
    filemode='a',  # 'a' to append, 'w' to overwrite
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)


class Generic(ABC):
    @abstractmethod
    def exec(self, params):
        pass


class FedServerContainer(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.server_id = orchestrator.config["server_id"]
        self.counter = 0
        self.fed_server_image_port = orchestrator.config["fed_server_image_port"]
        self.fed_server_image_name = orchestrator.config["fed_server_image_name"]
        self.rabbit_image_name = orchestrator.config["rabbitmq_image_name"]
        self.rabbit_image_port = orchestrator.config["rabbitmq_image_port"]

    def exec(self, params):
        response = params
        if params is not None:  # check Param
            # check service to make sure server is running well
            self.orchestrator.handling_edges[params["request_id"]] = [self.server_id]
            while True:
                try:
                    url_mgt_service = (
                            self.orchestrator.url_mgt_service + "/health?id=" + self.server_id
                    )
                    server_check = requests.get(url_mgt_service).json()
                    # logging.info("status of federated server: {}".format(not bool(server_check["code"])))
                    if server_check["code"] == 0:
                        command = {
                            "edge_id": self.server_id,
                            "request_id": params["request_id"],
                            "command": "docker",
                            "params": "start",
                            "docker": [
                                {
                                    "image": self.fed_server_image_name,
                                    "options": {
                                        "--name": f"fed_server_container_{params['consumer_id']}",
                                        "-p": [
                                            f"{self.fed_server_image_port}:{self.fed_server_image_port}"
                                        ],
                                    },
                                    "arguments": [
                                        str(self.fed_server_image_port),
                                        str(
                                            params["model_conf"]["train_hyper_param"][
                                                "epochs"
                                            ]
                                        ),
                                    ],
                                },
                                {
                                    "image": self.rabbit_image_name,
                                    "options": {
                                        "--name": f"rabbit_container_{params['consumer_id']}",
                                        "-p": [
                                            f"{self.rabbit_image_port}:{self.rabbit_image_port}"
                                        ],
                                    },
                                },
                            ],
                        }
                        try:
                            logging.info(
                                "Sending command to server {}\n{}".format(
                                    self.server_id, command
                                )
                            )
                            # asynchronously send
                            self.orchestrator.send(command)
                            fed_server_ip = server_check["result"]["ip"]
                            logging.info(
                                "Federated Server is started at: {}:{}".format(
                                    fed_server_ip, self.fed_server_image_port
                                )
                            )
                            response["start_fed_resp"] = {
                                "ip": fed_server_ip,
                                "fed_server_port": self.fed_server_image_port,
                                "rabbit_port": self.rabbit_image_port,
                            }
                        except Exception as e:
                            logging.error(
                                "[ERROR] - Error {} while send start fed command: {}".format(
                                    type(e), e.__traceback__
                                )
                            )
                            traceback.print_exception(*sys.exc_info())

                        logging.info("Waiting federated server response...")
                        flag = 0
                        while len(self.orchestrator.handling_edges[params["request_id"]]) > 0 and flag < 30:
                            time.sleep(10)
                            flag += 1

                        # start qot collector
                        command = {
                            "edge_id": self.server_id,
                            "request_id": params["request_id"],
                            "command": Protocol.QOT_COLLECTOR_COMMAND
                        }
                        self.orchestrator.send(command)

                        break
                    else:
                        logging.info("Waiting 1 minute for starting Cloud Server...")
                        time.sleep(60)

                except Exception as e:
                    logging.error(
                        "[ERROR] - Error {} while start FedServer: {}".format(
                            type(e), e.__traceback__
                        )
                    )
                    traceback.print_exception(*sys.exc_info())
                    break

        # need to return more info here to build docker
        return response


# def upload_config(config, username, url_storage_service):
#     # Specify the file path
#     json_file_path = f"{username}_config_{config['edge_id']}.json"
#
#     # Write the config dictionary to the JSON file
#     with open(json_file_path, "w") as json_file:
#         json.dump(config, json_file)
#
#     uri = f"{url_storage_service}/storage/obj"
#     files = {
#         "file": (json_file_path, open(json_file_path, "rb"), "application/json")
#     }
#     data = {"user": username}
#
#     response = requests.post(uri, files=files, data=data)
#     response.raise_for_status()  # Ensure the request was successful
#
#     storage_id = response.json()["storage_id"]
#     os.remove(json_file_path)
#
#     return storage_id


class Config4Edge(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def exec(self, params):
        config_id = {}

        for dataset in params["datasets"]:
            generated_config = {
                "consumer_id": params["consumer_id"],
                "model_id": params["model_id"],
                "run_id": params['run_id'],
                "dataset_id": dataset["dataset_id"],
                "edge_id": dataset["edge_id"],
                "fed_server": f"{params['start_fed_resp']['ip']}:{params['start_fed_resp']['fed_server_port']}",
                "data_conf": dataset["read_info"],
                "model_conf": params["model_conf"],
                "requirement_libs": params["requirement_libs"],
                "pre_train_model": params["pre_train_model"],
                "amqp_connector": {
                    "name": "amqp_connector",
                    "connector_class": "AMQP",
                    "config": {
                        "end_point": params['start_fed_resp']['ip'],
                        "exchange_name": "fml_model_report",
                        "exchange_type": "topic",
                        "out_routing_key": "service." + params["model_id"] + "." + dataset["edge_id"],
                        "health_check_disable": True
                    }
                }
            }

            if dataset.get("create_qod"):
                generated_config["create_qod"] = dataset["create_qod"]

            # Upload generated config to storage
            config_id[dataset["edge_id"]] = generated_config
            # config_id[dataset["edge_id"]] = upload_config(
            #     generated_config, params["consumer_id"], self.orchestrator.url_storage_service
            # )

        params["config4edge_resp"] = config_id
        return params


class EdgeContainer(Generic):
    def __init__(self, orchestrator, config="cloud/orchestrator/conf/image4edge.json"):
        if config is not None:
            self.config = utils.load_config(config)
        else:
            self.config = None
        self.orchestrator = orchestrator

    def is_edge_ready(self, edge_id):
        try:
            url_mgt_service = (
                    self.orchestrator.url_mgt_service + "/health?id=" + str(edge_id)
            )
            edge_check = requests.get(url_mgt_service).json()
            logging.info("Status of edge [{}]: {}".format(edge_id, not bool(edge_check["code"])))
            return not bool(edge_check["code"])
        except Exception as e:
            logging.error(
                "[ERROR] - Error {} while check dataset status: {}".format(
                    type(e), e.__traceback__
                )
            )
            traceback.print_exception(*sys.exc_info())
            return False

    def send_command(self, edge_command):
        self.orchestrator.send(edge_command)

    def get_image(self, platform):
        if "gpu" in platform:
            if "tensorflow" in platform:
                return self.config["image_tensorflow_gpu"]
            if "pytorch" in platform:
                return self.config["image_pytorch_gpu"]
        else:
            if "tensorflow" in platform:
                return self.config["image_tensorflow_cpu"]
            if "pytorch" in platform:
                return self.config["image_pytorch_cpu"]
        return self.config["image_default"]

    def exec(self, params):
        try:
            configs = params["config4edge_resp"]

            logging.info("Edge id: template id  => ".format(configs))
            container_name = f"fed_worker_container_{params['consumer_id']}_{params['model_id']}"
            command_template = {
                "edge_id": "",
                "request_id": params["request_id"],
                "command": "docker",
                "params": "start",
                "docker": [
                    {
                        "image": None,
                        "options": {
                            "--name": None,
                        },
                        "arguments": [],
                    }
                ],
                "config": ""
            }

            self.orchestrator.handling_edges[params["request_id"]] = list(configs.keys())

            while True:
                for edge_id in self.orchestrator.handling_edges[params["request_id"]]:
                    logging.info("Starting Edge [{}]: ".format(edge_id))
                    if self.is_edge_ready(edge_id):
                        # SEND COMMAND TO START EDGE ---> json
                        command = command_template.copy()
                        command["edge_id"] = edge_id

                        # We now support only CPU tensorflow on Ubuntu for testing
                        # in next version, we analyse info from edge to get correspondent image
                        command["docker"][0]["image"] = self.get_image(params["platform"])
                        command["docker"][0]["arguments"] = [
                            self.orchestrator.url_storage_service,
                            # configs[edge_id],
                        ]
                        command["docker"][0]["options"]["--name"] = container_name + "_" + edge_id
                        command['config'] = configs[edge_id]

                        for d in params["datasets"]:
                            # if dataset on edge is local, we mount it into container
                            if (
                                    d["edge_id"] == edge_id
                                    and d["read_info"]["method"] == "local"
                            ):
                                fullpath = d["read_info"]["location"]
                                filename = fullpath.split("/")[-1]
                                folder_path = fullpath[: fullpath.index(filename)]
                                mount = "type=bind,source={},target={}".format(
                                    folder_path, "/data/"
                                )
                                command["docker"][0]["options"]["--mount"] = mount

                        # send command to edge
                        self.send_command(command)

                        logging.info("Sent command: {} to {}".format(command, edge_id))
                    else:
                        logging.info("waiting edge {} to be available...".format(edge_id))

                if len(self.orchestrator.handling_edges[params["request_id"]]) == 0:
                    self.orchestrator.handling_edges.pop(params["request_id"])
                    break

                # WAIT 5 MINUTES FOR EDGE TO BE AVAILABLE
                logging.info("Waiting to receive {} response(s) from edges".format(
                    len(self.orchestrator.handling_edges[params["request_id"]])))
                time.sleep(5 * 60)

            logging.info("Sent command to all edges.")
        except:
            logging.error("Start container error!")


class QoDContainer(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def send_command(self, edge_command):
        self.orchestrator.send(edge_command)

    def is_edge_ready(self, edge_id):
        try:
            url_mgt_service = (
                    self.orchestrator.url_mgt_service + "/health?id=" + str(edge_id)
            )
            edge_check = requests.get(url_mgt_service).json()
            logging.info("Status of edge [{}]: ".format(edge_id, edge_check["code"]))
            return not bool(edge_check["code"])
        except Exception as e:
            logging.error(
                "[ERROR] - Error {} while check dataset status: {}".format(
                    type(e), e.__traceback__
                )
            )
            traceback.print_exception(*sys.exc_info())
            return False

    def exec(self, params):
        self.orchestrator.handling_edges[params["request_id"]] = [params["edge_id"]]
        # config_id = upload_config(
        #     params, params["consumer_id"], self.orchestrator.url_storage_service
        #
        # )
        command = {
            "edge_id": params["edge_id"],
            "request_id": params["request_id"],
            "command": "docker",
            "params": "start",
            "docker": [
                {
                    "image": self.orchestrator.config["eadran_qod_image_name"],
                    "options": {
                        "--name": f"data_qod_container_{params['consumer_id']}_{params['model_id']}",
                    },
                    "arguments": [
                        self.orchestrator.url_storage_service
                        # params["read_info"]["reader_module"]["storage_ref_id"],
                        # config_id
                    ],
                }
            ],
            "config": {
                "data_conf": params['data_conf'],
                "url_service": self.orchestrator.url_mgt_service
            }
        }
        if params["read_info"]["method"] == "local":
            fullpath = params["read_info"]["location"]
            filename = fullpath.split("/")[-1]
            folder_path = fullpath[: fullpath.index(filename)]
            mount = "type=bind,source={},target={}".format(folder_path, "/data/")
            command["docker"][0]["options"]["--mount"] = mount

        # send command to edge
        while True:
            if self.is_edge_ready(params["edge_id"]):
                self.send_command(command)
                logging.info("Sent QoD evaluation command to edge.")

            if len(self.orchestrator.handling_edges[params["request_id"]]) == 0:
                self.orchestrator.handling_edges.pop(params["request_id"])
                break

            # WAIT 5 MINUTES FOR EDGE TO BE AVAILABLE
            logging.info("Waiting to receive {} response(s) from edges".format(
                len(self.orchestrator.handling_edges[params["request_id"]])))
            time.sleep(5 * 60)
