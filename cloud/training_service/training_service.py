import json
import os
import parser

from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse

from helpers.custom_logger import CustomLogger
import logging
from qoa4ml.connector.amqp_connector import Amqp_Connector
import qoa4ml.utils as utils

app = Flask(__name__)
api = Api(app)
logger = CustomLogger().get_logger().setLevel(logging.INFO)

# headers = {'content-type': 'application/json'}
metadata_service = "metadata_service"
metadata_service_port= "8001"
data_service = "data_service"
data_service_port= "8002"
resource_service = "resource_service"
resource_service_port= "8003"
storage_service = "storage_service"
storage_service_port= "8004"
orchestrator_queue = """{'end_point':'amqps://schhmhpp:acDe6WuRj-sP0NtVIs5pE8wkroPnx0w-@armadillo.rmq.cloudamqp.com/schhmhpp',
                  'exchange_name': 'fedmarketplace.com',
                  'exchange_type': 'topic',
                  'out_routing_key': 'in.orchestrator.fedmarketplace.com',
                  'out_queue': 'orchestrator.queue.in'
                }"""
# orchestrator_service_port= "8005"

def get_node_name():
    node_name = os.environ.get('NODE_NAME')
    if not node_name:
        print("NODE_NAME is not defined")
        node_name = "Empty"
    return node_name

def get_instance_id():
    pod_id = os.environ.get('POD_ID')
    if not pod_id:
        print("POD_ID is not defined")
        pod_id = "Empty"
    return pod_id

def init_env_variables():
    metadata_service = os.environ.get('METADATA_SERVICE')
    metadata_service_port = os.environ.get("METADATA_SERVICE_PORT")
    data_service = os.environ.get('DATA_SERVICE')
    data_service_port = os.environ.get("DATA_SERVICE_PORT")
    resource_service = os.environ.get('RESOURCE_SERVICE')
    resource_service_port = os.environ.get("RESOURCE_SERVICE_PORT")
    storage_service = os.environ.get('STORAGE_SERVICE')
    storage_service_port = os.environ.get("STORAGE_SERVICE_PORT")
    orchestrator_queue = os.environ.get('ORCHESTRATOR_QUEUE_CONFIG')
    # orchestrator_service_port = os.environ.get("ORCHESTRATOR_SERVICE_PORT")
    if not metadata_service:
        logger.error("METADATA_SERVICE is not defined")
        raise Exception("METADATA_SERVICE is not defined")
    if not metadata_service_port:
        logger.error("METADATA_SERVICE_PORT is not defined")
        raise Exception("METADATA_SERVICE_PORT is not defined")
    if not data_service:
        logger.error("DATA_SERVICE is not defined")
        raise Exception("DATA_SERVICE is not defined")
    if not data_service_port:
        logger.error("DATA_SERVICE_PORT is not defined")
        raise Exception("DATA_SERVICE_PORT is not defined")
    if not resource_service:
        logger.error("RESOURCE_SERVICE is not defined")
        raise Exception("RESOURCE_SERVICE is not defined")
    if not resource_service_port:
        logger.error("RESOURCE_SERVICE_PORT is not defined")
        raise Exception("RESOURCE_SERVICE_PORT is not defined")
    if not storage_service:
        logger.error("STORAGE_SERVICE is not defined")
        raise Exception("STORAGE_SERVICE is not defined")
    if not storage_service_port:
        logger.error("STORAGE_SERVICE_PORT is not defined")
        raise Exception("STORAGE_SERVICE_PORT is not defined")
    if not orchestrator_queue:
        logger.error("ORCHESTRATOR_QUEUE_CONFIG is not defined")
        raise Exception("ORCHESTRATOR_QUEUE_CONFIG is not defined")


class TrainModel(Resource):
    def __init__(self, queue):
        self.queue = queue

    def get(self):
        return jsonify({'Working': True})

    def post(self):
        # ======================= MESSAGE RECEIVE FROM CLIENT
        # {
        #   "consumer_id": "who request",
        #   "model_id": "",
        #   "datasets": [{
        #     "dataset_id": "uuid of dataset",
        #     "resource_id": "specific computing infrastructure for this training",
        #     "extract_response_id": "response id from data service (file data_response_v0.1.json)"
        #   }],
        #   "requirement_libs": [{
        #     "name": "tensorflow",
        #     "version": "2.10"
        #   }],
        #   "model_conf":{
        #         "storage_ref_id":"id of code that manages in storage service",
        #         "module_name": "code for training at edges, must be attached",
        #         "function_map":{
        #             "train": "fit",
        #             "evaluate": "evaluate",
        #             "set_weights": "set_weights",
        #             "get_weights": "get_weights"
        #         },
        #         "train_hyper_param":{
        #             "epochs": 10,
        #             "batch_size": 32
        #         }
        #     },
        #   "pre_train_model": {
        #       "url": "link to get pre-train model from storage service",
        #       "name": "name of model on model management module/service",
        #       "params": "optional params to download"
        #     }
        # }
        # ============== END OF MESSAGE
        if request.is_json:
            json_msg = request.get_json(force=True)
            # send the command to orchestrator
            orchestrator_command = {"command": "train_model",
                                    "params":json_msg}
            self.queue.send(orchestrator_command)
            return jsonify({'status': "starting"})
        return jsonify({'status': 'request must enclose a json object'}),400


# in case of client want to start more edges/datasets
class StartEdge(Resource):
    def __init__(self, queue):
        self.queue = queue

    def get(self):
        return jsonify({'Working': True})

    def post(self):
        # {
        #   "consumer_id": "who request",
        #   "model_id": "",
        #   "datasets": [{
        #     "dataset_id": "uuid of dataset",
        #     "resource_id": "specific computing infrastructure for this training",
        #     "extract_response_id": "response id from data service (file data_response_v0.1.json)"
        #   }],
        # }
        # get param from args here
        if request.is_json:
            json_msg = request.get_json(force=True)
            orchestrator_command = {"command": "start_edge",
                                    "params": json_msg}
            self.queue.send(orchestrator_command)
            return jsonify({'status': "starting"})
        return jsonify({'status': 'request must enclose a json object'}),400


# in case of client want to stop the edges/datasets since expectation doesn't reach'
class StopEdge(Resource):
    def __init__(self, queue):
        self.queue = queue

    def get(self):
        return jsonify({'Working': True})

    def post(self):
        if request.is_json:
            json_msg = request.get_json(force=True)
            orchestrator_command = {"command": "stop_edge",
                                    "params": json_msg}
            self.queue.send(orchestrator_command)
            return jsonify({'status': "stopping"})
        return jsonify({'status': 'request must enclose a json object'}), 400


class Queue(object):
    def __init__(self, config):
        self.amqp_connector = Amqp_Connector(config,self)

    def send(self, msg):
        self.amqp_connector.send_data(json.dumps(msg))

# may be read from config file
orchestrator_config = json.loads(orchestrator_queue.replace("\'","\""))
queue = Queue(orchestrator_config)

api.add_resource(TrainModel, '/trainmodel',resource_class_args=(queue,))
api.add_resource(StartEdge, '/startedge',resource_class_args=(queue,))
api.add_resource(StopEdge, '/stopedge',resource_class_args=(queue,))

if __name__ == '__main__': 
    # init_env_variables()
    app.run(debug=True, port=5000)