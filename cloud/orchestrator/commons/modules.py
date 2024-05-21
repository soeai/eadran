from abc import ABC, abstractmethod
import qoa4ml.qoaUtils as utils
import traceback, sys
import requests, json, os, time
import logging


class Generic(ABC):
    @abstractmethod
    def exec(self, params):
        pass


class FedServerContainer(Generic):
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
                # print("Server check:", server_check)
                if server_check['status'] == 0:
                    command = {
                        "edge_id": self.server_id,
                        "command": "docker",
                        "params": "start",
                        "docker": [
                            {
                                "image": self.fed_server_image_name,
                                "options": {
                                    "--name": f"fed_server_container_{params['consumer_id']}",
                                    "-p": [f"{self.fed_server_image_port}/tcp:{self.fed_server_image_port}"],
                                },
                                "arguments": [params['model_conf']['train_hyper_param']['epochs']]
                            },
                            {
                                "image": self.rabbit_image_name,
                                "options": {
                                    "--name": f"rabbit_container_{params['consumer_id']}",
                                    "-p": [f"{self.rabbit_image_port}/tcp:{self.rabbit_image_port}"],
                                }
                            },
                        ]
                    }
                    try:
                        logging.debug("Sending command to server {}\n{}".format(self.server_id, command))
                        # asynchronously send
                        self.orchestrator.send(command)
                        fed_server_ip = server_check['result']['ip']
                        print("FED SERVER", fed_server_ip)

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


class Config4Edge(Generic):
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def upload_config(self, config, username):
        # Specify the file path
        json_file_path = "{}_config_{}.json".format(username, config['edge_id'])

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
        config_id = {}
        for dataset in params['datasets']:
            # this is a single template
            generated_config = {}

            generated_config['consumer_id'] = params['consumer_id']
            generated_config['model_id'] = params['model_id']
            generated_config['dataset_id'] = dataset['dataset_id']
            generated_config['edge_id'] = dataset['edge_id']
            generated_config['monitor_interval'] = 10
            generated_config['fed_server_id'] = (params['start_fed_resp']['ip'] + ':'
                                                 + str(params['start_fed_resp']['fed_server_port']))
            generated_config['data_conf'] = dataset['read_info']['module_conf']
            generated_config['model_conf'] = params['model_conf']
            generated_config['requirement_libs'] = params['requirement_libs']
            generated_config['pre_train_model'] = params['pre_train_model']

            # UPLOAD GENERATED CONFIG TO STORAGE
            config_id[dataset['edge_id']] = self.upload_config(generated_config, params['consumer_id'])
        response = params
        response['configs'] = config_id
        # print(response)
        return response


class EdgeContainer(Generic):
    def __init__(self, orchestrator, config='./conf/image4edge.json'):
        if config is not None:
            self.config = utils.load_config(config)
        else:
            self.config = None
        self.orchestrator = orchestrator

    def is_edge_ready(self, edge_id):
        try:
            url_mgt_service = self.orchestrator.url_mgt_service + "/health?id=" + str(edge_id)
            edge_check = requests.get(url_mgt_service).json()
            return bool(edge_check['status'])
        except Exception as e:
            print("[ERROR] - Error {} while check dataset status: {}".format(type(e), e.__traceback__))
            traceback.print_exception(*sys.exc_info())
            return False

    def send_command(self, edge_command):
        self.orchestrator.send(edge_command)

    def exec(self, params):
        # print("Test:", params)
        # 'configs': {'edge001': '664329d0489dd2fcd9da397b', 'edge004': '664329d0489dd2fcd9da397c'}
        configs = params['configs']
        temps = configs.copy()

        command_template = {
            "edge_id": "",
            "command": "docker",
            "params": "start",
            "docker": [
                {
                    "image": None,
                    "options": {
                        "--name": f"fed_worker_container_{params['consumer_id']}_{params['model_id']}",
                        "-mount": ""
                    },
                    "arguments": []
                }]
        }
        print('Check point')    #test...

        while True:
            for edge_id in temps:
                if self.is_edge_ready(edge_id):
                    # SEND COMMAND TO START EDGE ---> json
                    command = command_template.copy()
                    command['edge_id'] = edge_id

                    # We now support only CPU tensorflow on Ubuntu for testing
                    # in next version, we analyse info from edge to get correspondent image
                    command['docker'][0]['image'] = self.config['image_tensorflow_cpu']
                    command['docker'][0]['arguments'] = [self.orchestrator.url_storage_service, temps[edge_id]]

                    for d in params['datasets']:
                        # if dataset on edge is local, we mount it into container
                        if d['edge_id'] == edge_id and d['read_info']['method'] == 'local':
                            mount = 'type=bind,src={},target={}'.format(d['read_info']['location'], '/data')
                            command['docker'][0]['options']['-mount'] = mount

                    # logging.DEBUG(f"Sending command to edge {str(edge_id)}\n{command}")
                    # send command to edge
                    self.send_command(command)

                    # print("Temp:", temps)  # testing purposes
                    print(command)
                    # remove edge_id
                    temps.pop(edge_id, None)
                # else:
                #     pass
            if len(temps) == 0:
                break
            # WAIT 5 MINUTES FOR EDGE TO BE AVAILABLE
            print("Sleeping 5 minutes")
            time.sleep(5 * 60)

        print('Done Starting All Edges')
