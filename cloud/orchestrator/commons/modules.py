from abc import ABC, abstractmethod
import requests
import json
import os
import qoa4ml.qoaUtils as utils
import traceback, sys
from jinja2 import Environment, FileSystemLoader
import requests, json, os
import docker, threading


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


class GenerateConfiguration(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def upload_config(self, config, username):
        # Specify the file path
        json_file_path = "config.json"

        # Write the config dictionary to the JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(config, json_file)

        # uri = "http://192.168.10.234:8081/storage/obj"
        uri = "{}/{}/{}".format(self.orchestrator.url_storage_service, 'storage', 'obj')
        files = {'file': (json_file_path, open(json_file_path, 'rb'), 'application/json')}
        data = {'user': username}

        response = requests.post(uri, files=files, data=data)

        storage_id = response.json()['storage_id']
        os.remove(json_file_path)

        return storage_id

    def exec(self, params):
        template_id = []
        for dataset in params['datasets']:
            generated_config = {}
            edge_id = dataset['edge_id']
            generated_config['consumer_id'] = params['consumer_id']
            generated_config['model_id'] = params['model_id']
            generated_config['dataset_id'] = dataset['dataset_id']
            generated_config['edge_id'] = edge_id
            generated_config['monitor_interval'] = 10
            generated_config['fed_server_id'] = (params['start_fed_resp']['ip'] + ':'
                                                 + str(params['start_fed_resp']['port']))
            generated_config['read_info'] = dataset['read_info']
            generated_config['model_conf'] = params['model_conf']
            generated_config['requirement_libs'] = params['requirement_libs']
            generated_config['pre_train_model'] = params['pre_train_model']

            # UPLOAD GENERATED CONFIG TO STORAGE
            temp_id = self.upload_config(generated_config, params['consumer_id'])
            template_id.append(temp_id)
        response = params
        response['template_id'] = template_id

        return response


class StartTrainingContainerEdge(Generic):
    def __init__(self, orchestrator, config=None):
        if config is not None:
            self.config = utils.load_config(config)
        else:
            self.config = None
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

    def send_command(self, edge_command):
        self.orchestrator.send(edge_command)

    def exec(self, params):
        pass
