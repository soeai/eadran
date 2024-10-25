'''
We assume that the data for training is available that can be accessed through a uri
note that other tasks have been done to prepare such a data for the training task
'''
import argparse
import json
import time
from urllib.request import urlretrieve
import flwr as fl
import qoa4ml.utils.qoa_utils as utils
from qoa4ml.qoa_client import QoaClient
from qoa4ml.config.configs import ClientInfo, ClientConfig, ConnectorConfig, AMQPConnectorConfig
import subprocess
import sys


def install_missing(package):
    command = [sys.executable, "-m", "pip", "install"]
    command.extend(package)
    subprocess.call(command)


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
                 qoa_monitor=None,
                 is_tester=False):

        self.model_train = getattr(custom_module, client_profile['model_conf']['function_map']['train'])
        self.model_evaluate = getattr(custom_module, client_profile['model_conf']['function_map']['evaluate'])
        self.model_set_weights = getattr(custom_module, client_profile['model_conf']['function_map']['set_weights'])
        self.model_get_weights = getattr(custom_module, client_profile['model_conf']['function_map']['get_weights'])

        self.client_profile = client_profile
        self.is_tester = is_tester
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
        if not self.is_tester:
            start_time = time.time()
            with open("/share_volume/{}.json".format(self.client_profile['edge_id']), "w") as f:
                json.dump({"train_round": config['fit_round'],
                           "status": "start"}, f)
            # train
            self.model_set_weights(parameters)
            # get performance of first time
            # if self.pre_train_performance == 0:
            self.pre_train_performance, self.pre_train_loss = self.model_evaluate(self.x_train, self.y_train)
            self.post_train_performance, self.post_train_loss = self.model_train(self.x_train, self.y_train)

            # evaluate local model on testset
            if self.x_eval is not None:
                self.test_performance, self.test_loss = self.model_evaluate(self.x_eval, self.y_eval)

            weight = self.model_get_weights()
            end_time = time.time()

            if self.qoa_monitor is not None:
                self.total_time += end_time - start_time
                report = {'post_train_performance': self.post_train_performance,
                          'pre_train_performance': self.pre_train_performance,
                          'pre_loss_value': self.pre_train_loss,
                          'post_loss_value': self.post_train_loss,
                          'test_performance': self.test_performance,
                          'test_loss': self.test_loss,
                          'evaluate_on_test': 1 if self.x_eval is not None else 0,
                          'train_duration': round(self.total_time, 0)}
                self.qoa_monitor.report(report={'train_round': config['fit_round'],
                                                "quality_of_model": report}, submit=True)

            with open("/share_volume/{}.json".format(self.client_profile['edge_id']), "w") as f:
                json.dump({"train_round": config['fit_round'],
                           "status": "end"}, f)

            return weight, len(self.x_train), {"performance": self.post_train_performance}
        else:   # client is tester => without training
            return parameters, 0, {}

    def evaluate(self, parameters, config):  # type: ignore
        if self.is_tester and self.x_eval is not None:
            with open("/share_volume/{}.json".format(self.client_profile['edge_id']), "w") as f:
                json.dump({"train_round": config['val_round'],
                           "status": "end"}, f)
            self.model_set_weights(parameters)
            self.test_performance, self.test_loss = self.model_evaluate(self.x_eval, self.y_eval)
            datasize = len(self.x_eval)

            report = {'post_train_performance': 0,
                      'pre_train_performance': 0,
                      'pre_loss_value': 0,
                      'post_loss_value': 0,
                      'test_performance': self.test_performance,
                      'test_loss': self.test_loss,
                      'evaluate_on_test': 1,
                      'train_duration': 0}

            self.qoa_monitor.report(report={'train_round': config['val_round'],
                                            "quality_of_model": report}, submit=True)

            # with open("/share_volume/{}.json".format(self.client_profile['edge_id']), "w") as f:
            #     json.dump({"train_round": config['val_round'],
            #                "status": "end"}, f)
            return self.test_loss, datasize, {"performance": self.test_performance}
        else:
            return -1, 1, {"performance": 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Client Federated Learning")
    parser.add_argument('--service', help='http://ip:port of storage service')
    parser.add_argument('--sessionid', help='The request Id from orchestrator')
    parser.add_argument('--conf', help='Client config file')

    args = parser.parse_args()

    url_service = args.service + "/storage/obj?key="
    client_conf = utils.load_config("/conf/" + args.conf)

    if client_conf is not None:
        print(client_conf)

        if len(client_conf['requirement_libs']) > 0:
            install_missing(client_conf['requirement_libs'])

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

        validate_file = None
        if "validate_data" in client_conf['data_conf'].keys():
            validate_file = client_conf['data_conf']['validate_data']

        if client_conf['data_conf']['method'] == 'local':
            filename = client_conf['data_conf']['location'].split('/')[-1]
            X, y, X_val, y_val = dps_read_data_module("/data/" + filename,
                                                      validate_file)
        else:
            X, y, X_val, y_val = dps_read_data_module(client_conf['data_conf']['location'],
                                                      validate_file)

        # Create reporter
        client_info = ClientInfo(
            name=client_conf['edge_id'],
            user_id=client_conf['consumer_id'],
            username="edge_container",
            instance_name=args.sessionid,
            stage_id="eadran:" + client_conf['edge_id'],
            functionality=client_conf['dataset_id'],
            application_name=client_conf['model_id'],
            role='eadran:mlm_performance',
            run_id=str(client_conf['run_id']),
            custom_info=""
        )

        connector_config = ConnectorConfig(
            name=client_conf['amqp_connector']['name'],
            connector_class=client_conf['amqp_connector']['connector_class'],
            config=AMQPConnectorConfig(**client_conf['amqp_connector']['config'])
        )

        cconfig = ClientConfig(
            client=client_info,
            connector=[connector_config]
            )

        qoa_client = QoaClient(
            config_dict=cconfig
        )

        tester = False
        if "tester" in client_conf.keys():
            tester = bool(client_conf['tester'])

        fed_client = FedMarkClient(client_profile=client_conf,
                                   custom_module=mcs_custom_module,
                                   x_train=X,
                                   y_train=y,
                                   x_eval=X_val,
                                   y_eval=y_val,
                                   qoa_monitor=qoa_client,
                                   is_tester=tester).to_client()

        fl.client.start_client(server_address=client_conf['fed_server'], client=fed_client)
