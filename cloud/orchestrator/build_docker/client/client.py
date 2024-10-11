'''
We assume that the data for training is available that can be accessed through a uri
note that other tasks have been done to prepare such a data for the training task
'''
import argparse
import time
from urllib.request import urlretrieve
import flwr as fl
import qoa4ml.utils.qoa_utils as utils
from qoa4ml.qoa_client import QoaClient
from qoa4ml.config.configs import ClientInfo, ClientConfig
import numpy as np
# from qoa4ml.reports.rohe_reports import RoheReport
# from qoa4ml.config.configs import MetricConfig


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
            report = {'post_train_performance': self.post_train_performance,
                      'pre_train_performance': self.pre_train_performance,
                      'pre_loss_value': self.pre_train_loss,
                      'post_loss_value': self.post_train_loss,
                      'train_round': config['fit_round'],
                      'train_duration': np.round(self.total_time, 0)}
            self.qoa_monitor.report(report=report,submit=True)

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
    parser.add_argument('--service', help='http://ip:port of storage service')
    parser.add_argument('--sessionid', help='The request Id from orchestrator')
    parser.add_argument('--conf', help='Client config file')

    args = parser.parse_args()

    url_service = args.service + "/storage/obj?key="
    client_conf = utils.load_config("conf/" + args.conf)

    print(client_conf)

    # download code of DPs to read data
    urlretrieve(url_service + client_conf['data_conf']['reader_module']['storage_ref_id'],
                client_conf['data_conf']['reader_module']['module_name'] + ".py")

    # model
    urlretrieve(url_service + client_conf['model_conf']['storage_ref_id'],
                client_conf['model_conf']['module_name'] + ".py")

    # import custom code of market consumer -- model
    mcs_custom_module = __import__(client_conf['model_conf']['module_name'])

    print("OK-->: " + str(mcs_custom_module))
    # import code of data provider to read data
    dps_read_data_module = getattr(__import__(client_conf['data_conf']['reader_module']['module_name']),
                                   client_conf['data_conf']['reader_module']["function_map"])

    filename = client_conf['data_conf']['location'].split('/')[-1]
    X, y = dps_read_data_module("/data/" + filename)

    # # Create reporter

    client_info = ClientInfo(
        name=client_conf['edge_id'],
        user_id=client_conf['consumer_id'],
        username="edge_container",
        instance_name=args.sessionid,
        stage_id="eadran:" + client_conf['edge_id'],
        functionality=client_conf['dataset_id'],
        application_name=client_conf['model_id'],
        role='eadran:edge',
        run_id=str(client_conf['run_id']),
        custom_info=""
    )

    cconfig = ClientConfig(
        client=client_info,
        connector=client_conf['amqp_connector']
        )

    qoa_client = QoaClient(
        config_dict=cconfig
    )

    fed_client = FedMarkClient(client_profile=client_conf,
                               custom_module=mcs_custom_module,
                               x_train=X,
                               y_train=y,
                               qoa_monitor=qoa_client)

    fl.client.start_numpy_client(server_address=client_conf['fed_server'], client=fed_client)
