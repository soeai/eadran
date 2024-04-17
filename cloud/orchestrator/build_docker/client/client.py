'''
We assume that the data for training is available that can be accessed through a uri
note that other tasks have been done to prepare such a data for the training task
'''
import argparse
import time
from urllib.request import urlretrieve
import flwr as fl
import qoa4ml.qoaUtils as qoa_utils
# from qoa4ml import QoaClient
import numpy as np

# quality_of_model_conf = {}
# resource_monitor_conf = {}


class FedMarkClient(fl.client.NumPyClient):
    ########
    # Model:
    #       train/fit:
    #           output: tuple eg. (performance metric, loss)
    #       evaluate
    #           output: tuple eg. (performance metric, loss)
    #       get/set_weights
    #

    def __init__(self, client_profile, custom_module, x_train, y_train,
                 qoa_monitor=None,
                 monitor_interval=1):

        self.model_train = getattr(custom_module, client_profile['model_conf']['function_map']['train'])
        self.model_evaluate = getattr(custom_module, client_profile['model_conf']['function_map']['evaluate'])
        self.model_set_weights = getattr(custom_module, client_profile['model_conf']['function_map']['set_weights'])
        self.model_get_weights = getattr(custom_module, client_profile['model_conf']['function_map']['get_weights'])

        self.client_profile = client_profile
        self.x_train = x_train
        self.y_train = y_train

        if qoa_monitor is not None:
            self.qoa_monitor = qoa_monitor
            self.train_performance = 0
            self.train_loss = 0
            self.test_performance = 0
            self.test_loss = 0
            self.monitor_interval = monitor_interval
            self.total_time = 0
            self.metrics = self.qoa_monitor.get_metric()

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
        if self.qoa_monitor is not None:
            # System monitoring
            self.qoa_monitor.get()['train_round']=config['fit_round']
            qoa_utils.procMonitorFlag = True
            qoa_utils.docker_monitor(self.qoa_monitor, self.monitor_interval, self.metrics)

        start_time = time.time()
        # train
        self.model_set_weights(parameters)
        # get performance of first time
        if self.test_performance == 0:
            self.test_performance, self.test_loss = self.model_evaluate(self.x_train, self.y_train)
        self.train_performance, self.train_loss = self.model_train(self.x_train, self.y_train)

        weight = self.model_get_weights()
        end_time = time.time()

        if self.qoa_monitor is not None:

            self.total_time += end_time - start_time

            # Report metric via QoA4ML
            self.metrics['train_performance_after'].set(self.train_performance)
            self.metrics['train_performance_before'].set(self.test_performance)
            self.metrics['loss_value_before'].set(self.test_loss)
            self.metrics['loss_value_after'].set(self.train_loss)

            self.metrics['duration'].set(np.round(self.total_time, 0))
            # Stop monitoring
            qoa_utils.proc_monitor_flag = False

        return weight, len(self.x_train), {"performance": self.train_performance}

    def evaluate(self, parameters, config): # type: ignore
        start_time = time.time()
        self.model_set_weights(parameters)
        self.test_performance, self.test_loss = self.model_evaluate(self.x_train, self.y_train)
        end_time = time.time()
        self.total_time = end_time - start_time
        return self.test_loss, len(self.x_train), {"performance": self.test_performance}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Client Federated Learning")
    parser.add_argument('--service', help='ip:port of storage service', default='127.0.0.1:8081')
    parser.add_argument('--conf', help='Client config file', default="./conf/client.json")
    # parser.add_argument('--connector', help='Connector config file', default="./conf/connector.json")
    # parser.add_argument('--metric', help='Connector config file', default="./conf/metrics.json")

    args = parser.parse_args()
    # print(args.)
    # print(args.conf)
    url_service = "http://" + args.service + "/storage/obj?id="
    client_conf = qoa_utils.load_config(args.conf)

    print(client_conf)

    # download code of DPs to read data
    urlretrieve(url_service + client_conf['data_conf']['storage_ref_id'],
                client_conf['data_conf']['module_name']+".py")
    urlretrieve(url_service + client_conf['model_conf']['storage_ref_id'],
                client_conf['model_conf']['module_name'] + ".py")

    # import custom code of market consumer
    mcs_custom_module = __import__(client_conf['model_conf']['module_name'])

    print("OK-->: " + str(mcs_custom_module))
    # import code of data provider to read data
    dps_read_data_module = getattr(__import__(client_conf['data_conf']['module_name']),
                                   client_conf['data_conf']["function_map"])

    X, y = dps_read_data_module(client_conf['data_conf']['data_path'])

    # Create monitor
    # qoa_client = QoaClient(client_conf={"consumer_id":client_conf['consumer_id']
    #                                      "model_id":client_conf['model_id'],
    #                                      "run_id": client_conf['run_id'],
    #                                      "dataset_id": client_conf['dataset_id'],
    #                                      "edge_id": client_conf['edge_id'],
    #                                      "train_round": 1},
    #                                      connector_conf=connector_conf)
    # qoa_client.add_metric(metric_conf['quality_of_model'], category='quality_of_model')
    # qoa_client.add_metric(metric_conf['edge_monitor'], category='edge_monitor')

    # temporary does not monitor and report to assessment service
    fed_client = FedMarkClient(custom_module=mcs_custom_module,
                               client_profile=client_conf,
                               x_train=X,
                               y_train=y)
                               # ,
                               # qoa_monitor=qoa_client,
                               # monitor_interval=int(client_conf['monitor_interval']))

    fl.client.start_numpy_client(server_address=client_conf['fed_server'], client=fed_client)