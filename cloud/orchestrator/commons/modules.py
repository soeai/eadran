from abc import ABC, abstractmethod
import qoa4ml.qoaUtils as utils
import traceback, sys
from jinja2 import Environment, FileSystemLoader
import requests, json, os
import docker, threading

template_folder = utils.get_parent_dir(__file__, 1) + "/template"
config_folder = utils.get_parent_dir(__file__, 1) + "/conf"
temporary_folder = utils.get_parent_dir(__file__, 1) + "/temp"
jinja_env = Environment(loader=FileSystemLoader(template_folder))


def docker_build(folder_path, image_repo):
    client = docker.from_env()
    client.images.build(
        path=folder_path,
        dockerfile=folder_path + '/Dockerfile',
        tag=image_repo,
    )


def make_temp_dir(folder_name):
    if not os.path.exists(temporary_folder):
        os.makedirs(temporary_folder)
    folder_path = os.path.join(temporary_folder, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


class Generic(ABC):
    @abstractmethod
    def exec(self, params):
        pass


class StartFedServer(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.server_id = orchestrator.config['server_id']
        self.counter = 0
        self.fed_server_image_port = orchestrator.config['fed_server_image_port']
        self.fed_server_image_name = orchestrator.config['fed_server_image_name']
        self.rabbit_image_name = orchestrator.config['rabbitmq_image_name']
        self.rabbit_image_port = orchestrator.config['rabbitmq_image_port']

    def exec(self, params):
        try:
            # send message to orchestration_at_federated service to start 2 docker: RMQ & Federated Server
            # get queue routine, IP, port
            # optional store in database - configuration service

            # prepare and run command to build docker
            # subprocess.run()
            # report all necessary info for next step
            response = params
            if params is not None:  # check Param
                # check service to make sure server is running well
                url_mgt_service = self.orchestrator.url_mgt_service + "/health?id=" + self.server_id
                server_check = requests.get(url_mgt_service).json()
                if server_check['status'] == 0:
                    command = {
                        "server_id": self.server_id,
                        "command": "docker",
                        "params": "start",
                        "docker": [
                            {
                                "image": self.fed_server_image_name,
                                "options": {
                                    "--name": f"fed_server_container_{params['consumer_id']}",
                                    "-v": "",
                                    "-p": [f"{self.fed_server_image_port}/tcp:{self.fed_server_image_port}"],
                                    "-mount": ""
                                },
                                "epochs": params['model_conf']['train_hyper_param']['epochs']
                            },
                            {
                                "image": self.rabbit_image_name,
                                "options": {
                                    "--name": f"rabbit_container_{params['consumer_id']}",
                                    "-v": "",
                                    "-p": [f"{self.rabbit_image_port}/tcp:{self.rabbit_image_port}"],
                                    "-mount": ""
                                }
                            },
                        ]
                    }
                    try:
                        # asynchronously send
                        self.orchestrator.send(command)
                        fed_server_ip = server_check['result']['ip']

                    except Exception as e:
                        print("[ERROR] - Error {} while send start fed command: {}".format(type(e), e.__traceback__))
                        traceback.print_exception(*sys.exc_info())
                        # response must be dictionary including IP of fed server
                    response["start_fed_resp"] = {
                        "ip": fed_server_ip,
                        "fed_server_port": self.fed_server_image_port,
                        "rabbit_port": self.rabbit_image_port
                    }

        except Exception as e:
            print("[ERROR] - Error {} while start FedServer: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())

        # need to return more info here to build docker
        return response


# SHOULD DISTRIBUTE THIS CLASS TO HANDLE MULTIPLE REQUESTS
def generate_requirements(reqs, folder_path):
    req_text = ""
    for req in reqs:
        req_text = req_text + req["name"] + "==" + req["version"] + "\n"
    with open(folder_path + "/requirements.txt", "w") as f:
        f.write(req_text)


def fetch_source_code(config, folder_path):
    # fetch source code from git/url/object storage to folder_path
    # return True/False
    # download code/module from config['storage_ref_id']
    # rename module to config['module_name'] if its name is not correct
    pass


class ResourceComputingGenerateConfiguration(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def is_edge_ready(self, edge_id):
        try:
            url_mgt_service = self.orchestrator.url_mgt_service + "/health?id=" + edge_id
            edge_check = requests.get(url_mgt_service).json()
            return bool(edge_check['status'])
        except Exception as e:
            print("[ERROR] - Error {} while check dataset status: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())
            return False

    def exec(self, params):
        # report all necessary info for next step
        edge_available = {}
        for edge_id in params['datasets']:
            edge_available[edge_id] = self.is_edge_ready(edge_id)

        response = params
        response["edge_available"] = edge_available
        return response


class StartTrainingContainerEdge(Generic):
    def __init__(self, orchestrator, config=None):
        if config is not None:
            self.config = utils.load_config(config)
        else:
            self.config = None
        self.orchestrator = orchestrator

    def send_command(self, edge_command):
        self.orchestrator.send(edge_command)

    def exec(self, params):
        return pass
