'''
We assume that the data for training is available that can be accessed through a uri
note that other tasks have been done to prepare such a data for the training task
'''
import argparse
import json
import time
import uuid

import docker
import flwr as fl
import numpy as np
import qoa4ml.utils.qoa_utils as utils
from qoa4ml.config.configs import ClientInfo, ClientConfig, ConnectorConfig, AMQPConnectorConfig, ProbeConfig, \
    DockerProbeConfig
from qoa4ml.qoa_client import QoaClient


class FedMarkClient(fl.client.NumPyClient):
    ########
    # Model:
    #       train/fit:
    #           output: tuple eg. (performance metric, loss)
    #       evaluate
    #           output: tuple eg. (performance metric, loss)
    #       get/set_weights
    #

    def __init__(self, client_profile, custom_module,
                 x_train, y_train,
                 x_eval=None, y_eval=None,
                 qoa_monitor=None):

        self.model_train = getattr(custom_module, client_profile['model_conf']['function_map']['train'])
        self.model_evaluate = getattr(custom_module, client_profile['model_conf']['function_map']['evaluate'])
        self.model_set_weights = getattr(custom_module, client_profile['model_conf']['function_map']['set_weights'])
        self.model_get_weights = getattr(custom_module, client_profile['model_conf']['function_map']['get_weights'])

        self.client_profile = client_profile
        self.x_train = x_train
        self.y_train = y_train
        self.x_eval = x_eval
        self.y_eval = y_eval
        self.qoa_monitor = qoa_monitor
        self.post_train_performance = 0
        self.post_train_loss = 0
        self.pre_train_performance = 0
        self.pre_train_loss = 0
        self.test_performance = 0
        self.test_loss = 0
        self.total_time = 0

    def get_parameters(self, config):

        ##########################################
        # TO DO:
        # get model weights
        ##########################################
        return self.model_get_weights()

    def set_parameters(self, config):

        ##########################################
        # TO DO:
        # set model weights
        ##########################################
        pass

    def fit(self, parameters, config):  # type: ignore
        # if self.qoa_monitor is not None:
        #     # System monitoring
        #     # self.qoa_monitor.get()['train_round'] = config['fit_round']
        #     qoa_utils.procMonitorFlag = True
        #     qoa_utils.docker_monitor(self.qoa_monitor, self.monitor_interval, self.metrics)

        start_time = time.time()
        # train
        self.model_set_weights(parameters)
        # get performance of first time
        if self.pre_train_performance == 0:
            self.pre_train_performance, self.pre_train_loss = self.model_evaluate(self.x_train, self.y_train)
        self.post_train_performance, self.post_train_loss = self.model_train(self.x_train, self.y_train)

        weight = self.model_get_weights()
        end_time = time.time()

        if self.qoa_monitor is not None:
            self.total_time += end_time - start_time
            # Report metric via QoA4ML
            self.qoa_monitor.observe_metric('post_train_performance', self.post_train_performance)
            self.qoa_monitor.observe_metric('pre_train_performance', self.pre_train_performance)
            self.qoa_monitor.observe_metric('pre_loss_value', self.pre_train_loss)
            self.qoa_monitor.observe_metric('post_loss_value', self.post_train_loss)
            self.qoa_monitor.observe_metric('train_round', config['fit_round'])
            self.qoa_monitor.observe_metric('duration', np.round(self.total_time, 0))
            self.qoa_monitor.report()

        return weight, len(self.x_train), {"performance": self.post_train_performance}

    def evaluate(self, parameters, config):  # type: ignore
        datasize = len(self.x_train)
        start_time = time.time()
        self.model_set_weights(parameters)
        if self.x_eval is not None:
            self.test_performance, self.test_loss = self.model_evaluate(self.x_eval, self.y_eval)
            datasize = len(self.x_eval)
        else:
            self.test_performance, self.test_loss = self.model_evaluate(self.x_train, self.y_train)
        end_time = time.time()
        self.total_time = end_time - start_time
        return self.test_loss, datasize, {"performance": self.test_performance}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Client Federated Learning")
    # parser.add_argument('--service', help='http://ip:port of storage service', default='http://192.168.80.79:8081')
    parser.add_argument('--conf', help='Client config file', default="./conf/client_template.json")
    # parser.add_argument('--conf', help='Client config file', default="./conf/client.json")

    parser.add_argument('--sessionid', help='The request Id from orchestrator')

    args = parser.parse_args()

    # url_service = args.service + "/storage/obj?id="
    client_conf = utils.load_config(args.conf)

    # print(client_conf)

    # download code of DPs to read data
    # urlretrieve(url_service + client_conf['read_info']['reader_module']['storage_ref_id'],
    #             client_conf['read_info']['reader_module']['module_name'] + ".py")
    #
    # # model
    # urlretrieve(url_service + client_conf['model_conf']['storage_ref_id'],
    #             client_conf['model_conf']['module_name'] + ".py")

    # import custom code of market consumer -- model
    # mcs_custom_module = __import__(client_conf['model_conf']['module_name'])

    # print("OK-->: " + str(mcs_custom_module))
    # import code of data provider to read data
    # dps_read_data_module = getattr(__import__(client_conf['read_info']['reader_module']['module_name']),
    #                                client_conf['read_info']['reader_module']["function_map"])
    #
    # filename = client_conf['read_info']['location'].split('/')[-1]
    # # X, y = dps_read_data_module("/data/" + filename)
    # X, y = dps_read_data_module("/home/longnguyen/Downloads/Fraud_Data/" + filename)

    docker_res = docker.from_env().version()
    print(docker_res)

    # client_info = ClientInfo(
    #     name=client_conf['edge_id'],
    #     user_id=client_conf['consumer_id'],
    #     username=client_conf['dataset_id'],
    #     instance_id=str(uuid.uuid4()),
    #     instance_name='session_001',
    #     stage_id="version:1",
    #     functionality="test",
    #     application_name=client_conf['model_id'],
    #     role='fml:eadran',
    #     run_id=str(client_conf['run_id']),
    #     custom_info=""
    # )
    #
    # connector_config = ConnectorConfig(
    #     name=client_conf['consumer_id'],
    #     connector_class="AMQP",
    #     config=AMQPConnectorConfig(**client_conf['amqp_connector']['conf'])
    # )
    #
    # probe_config = ProbeConfig(
    #     probe_type="docker",
    #     frequency=10,
    #     require_register=False,
    #     log_latency_flag=False,
    #     environment="Edge",
    #     container_name=["rabbitmq"]
    # )
    # cconfig = ClientConfig(
    #     client=client_info,
    #     connector=[connector_config],
    #     # probes=[probe_config]
    #     # probes=[{"probe_type": "docker",
    #     #          "frequency": 30,
    #     #          "require_register": False,
    #     #          "log_latency_flag": False,
    #     #          "environment": "Edge",
    #     #          "container_name": ["rabbitmq"]}]
    # )
    client_conf['qoa_client']['connector'] = [{
        "name": "amqp_connector",
        "connector_class": "AMQP",
        "config": {
          "end_point": "128.214.255.226",
          "exchange_name": "fml_model_report",
          "exchange_type": "topic",
          "out_routing_key": "service.edge02",
          "health_check_disable": True
        }
      }]
    client_conf['qoa_client']['probes'] = [{
        "probe_type": "docker",
        "frequency": 1000,
        "require_register": False,
        "log_latency_flag": False,
        "environment": "Edge",
        "container_name": ["rabbitmq"]
      }]
    # with open("temp_conf.json", 'w') as f:
    #     json.dump(client_conf['qoa_client'],f)
    #
    # qoa4ml_conf = utils.load_config("temp_conf.json")
    # print(type(client_conf['qoa_client']))
    print(client_conf['qoa_client'])
    qoa_client = QoaClient(
        config_dict=client_conf['qoa_client']
    )

    # qoa_client.observe_metric('post_train_performance', 0.9)
    # qoa_client.observe_metric('pre_train_performance', 0.9)
    # qoa_client.observe_metric('pre_loss_value', 2)
    # qoa_client.observe_metric('post_loss_value', 4)
    # qoa_client.observe_metric('train_round', 13)
    # qoa_client.observe_metric('duration', 34.8)

    # qoa_client.qoa_report.report.metadata = {"client_config": client_info}
    # qoa_client.inference_flag = True
    # qoa_client.observe_inference_metric("accuracy", 1)
    # qoa_client.timer()
    # print(qoa_client.qoa_report.report)
    # for i in range(5):
    #     print(qoa_client.report(report={'post_train_performance': 0.9,
    #                                     'pre_train_performance': 0.91,
    #                                     'pre_loss_value': 2,
    #                                     'post_loss_value': 4,
    #                                     'train_round': (i+1),
    #                                     'train_duration': 34},submit=True))
    #     time.sleep(5)
    # print(qoa_client.qoa_report.report)

    # print(amqp_connector)
    # qoa_client_config["connector"] = [amqp_connector]
    # qoa_client_config["client"]["instance_name"] = request_id
    # for probe_config in qoa_client_config["probes"]:
    #     if probe_config["probe_type"] == "docker":
    #         probe_config["container_name"] = [container_name]
    # print(qoa_client)
    # client = QoaClient(config_dict=qoa_client)
    qoa_client.start_all_probes()
    while True:
        pass

