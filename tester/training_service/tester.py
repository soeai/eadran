import json
# import os
# import parser

from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
from cloud.commons.default import ServiceConfig
# from helpers.custom_logger import CustomLogger
import logging
from qoa4ml.connector.amqp_connector import Amqp_Connector
# import qoa4ml.utils as utils

app = Flask(__name__)
api = Api(app)
# logger = CustomLogger().get_logger().setLevel(logging.INFO)


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


with open("config.json") as f:
    orchestrator_config = json.load(f)['orchestrator']
queue = Queue(orchestrator_config)

api.add_resource(TrainModel, '/trainmodel',resource_class_args=(queue,))
api.add_resource(StartEdge, '/startedge',resource_class_args=(queue,))
api.add_resource(StopEdge, '/stopedge',resource_class_args=(queue,))

if __name__ == '__main__':
    # init_env_variables()
    app.run(debug=True, port=ServiceConfig.TRAINING_SERVICE_PORT)