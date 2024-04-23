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


# class BuildDocker(Generic):
#     #   "requirement_libs": [{
#     #     "name": "tensorflow",
#     #     "version": "2.10"
#     #   }],
#     #   "model_conf":{
#     #         "storage_ref_id":"id of code that manages in storage service"
#     #     },
#     # build docker from user config source code + library (from storage service - MinIO)
#     # push docker
#     # return docker name:tag:version
#     def __init__(self, config=None):
#         if config is not None:
#             self.config = utils.load_config(config)
#         else:
#             self.config = None
#
#     def generate_dockerfile(self, folder_path):
#         # Example:
#         # docker_config = {
#         #     "base_image": "python@latest",
#         #     "work_folder": "workspace",
#         #     "source_code": folder_path,
#         #     "ports": [5000,5001],
#         #     "cmd": "python service.py"
#         # }
#         # init config for RMQ
#         tem_doc = jinja_env.get_template("Dockerfile")
#         docker_file = tem_doc.render(self.config['docker_config'])
#         with open(folder_path + "/Dockerfile", "w") as f:
#             f.write(docker_file)
#
#     def exec(self, params):
#         # prepare and run command to build docker
#         # report all necessary info for next step
#         temp_folder = make_temp_dir(params["consumer_id"] + "_folder")
#         generate_requirements(params["requirement_libs"], temp_folder)
#
#         # THERE IS NO DOCKER_CONFIG IN PARAMS
#         self.generate_dockerfile(params["docker_config"], temp_folder)
#
#         image_repo = params["consumer_id"] + "_" + params['model_id']
#
#         if fetch_source_code(params["model_conf"], temp_folder):
#             sub_thread = threading.Thread(target=docker_build, args=(temp_folder, image_repo))
#             sub_thread.start()
#
#         response = params
#         # Add more info here
#         response["build_docker"] = {"image": image_repo}
#         return response
#

class ResourceComputing(Generic):
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


class GenerateConfiguration(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def get_fed_server_url(self, params):
        # To do
        pass

    def generate_model_id(self, params):
        # To do
        pass

    def get_run_th(self, params):
        # To do
        pass

    def get_monitor_interval(self, params):
        # To do
        pass

    def get_rmq_config(self, params):

        # To do
        # return rmq_config = {
        #     "url": "",
        #     "exchange_name": "",
        #     "our_routing": "",
        #     "queue_name": "" 
        # }
        pass

    def generate_data_configuration(self, params):
        # To do
        pass

    def exec(self, params):
        # report all necessary info for next step
        if params["resource_response"]:  # if dataset and resource ready
            dataset = params["datasets"]
            for data in dataset:
                jinja_var = {}
                # init config for RMQ
                tem_conf = jinja_env.get_template("config4edge.json")
                jinja_var["fed_server_url"] = self.get_fed_server_url(params)
                jinja_var["model_id"] = self.generate_model_id(params)
                jinja_var["run_th"] = self.get_run_th(params)
                jinja_var["monitor_interval"] = self.get_monitor_interval(params)

                jinja_var["rmq_conf"] = self.get_rmq_config(params)

                configuration = tem_conf.render(jinja_var)
                configuration["fedml_info"]["model_conf"] = params["model_conf"]
                configuration["fedml_info"]["pre_train_model"] = params["pre_train_model"]
                configuration["data"] = self.generate_data_configuration(params)
                temp_f_name = "edge_configurations"
                make_temp_dir(temp_f_name)
                folder_path = temporary_folder + "/" + temp_f_name

                with open(folder_path + "/configuration" + data["dataset_id"] + ".json",
                          "w") as f:  # data must have feature name
                    f.write(configuration)

        response = {}
        return response


class StartTrainingContainerEdge(Generic):
    # start edge <-> config file
    # send to orchestration at edge
    # {
    #     "edge_id": "specific resource id or *",
    #     "command": "docker",
    #     "params": "start",
    #     "config":[
    #         {
    #             "image": "repo:docker_image_ML_client",
    #             "container_name": "ML_client_container_01",
    #             "detach": "True",
    #             "binding_port":{
    #                 "1111/tcp":"2222",
    #                 "3333/tcp":"4444"}
    #         }
    #     ],
    #     "conf_path": "configuration path in docker container, optional"
    # }
    def __init__(self, orchestrator, config=None):
        if config is not None:
            self.config = utils.load_config(config)
        else:
            self.config = None
        self.orchestrator = orchestrator

    def generate_config(self, params):
        config = {}
        # Example config
        # config = {
        #     "edge_id": "",
        #     "image_repo":"",
        #     "container_name": "",
        #     "port_mapping" : [{
        #         "con_port": 4002,
        #         "phy_port": 4002,
        #         "port_protocol": "tcp"
        #     },{
        #         "con_port": 4003,
        #         "phy_port": 4003,
        #         "port_protocol": "tcp"
        #     }],
        #     "conf_path": ""
        # }
        return config

    def get_edge_resource(self, params):
        # To do
        return []

    def send_command(self, edge_command):
        # asynchronously send
        self.orchestrator.send(edge_command)

    def exec(self, params):
        # prepare and run command to build docker
        # subprocess.run()

        # report all necessary info for next step
        temp_conf = jinja_env.get_template("docker_edge.json")
        edges = self.get_edge_resource(params)  # list of edge resources
        for edge in edges:
            config = self.generate_config(params)

            edge_command = temp_conf.render(config)
            self.send_command(edge_command)

        response = {}
        return response
