import json
import logging
import os
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from qoa4ml.connector.amqp_connector import Amqp_Connector

from helpers.custom_logger import CustomLogger
logger = CustomLogger().get_logger().setLevel(logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)

app = Flask(__name__)
api = Api(app)

mongo_client = None
orchestrator_queue = """{'end_point':'amqps://schhmhpp:acDe6WuRj-sP0NtVIs5pE8wkroPnx0w-@armadillo.rmq.cloudamqp.com/schhmhpp',
                  'exchange_name': 'fedmarketplace',
                  'exchange_type': 'topic',
                  'out_routing_key': 'orchestrator.dataservice',
                  'out_queue': 'orchestrator.queue.out'
                }"""

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
    # edge_service = os.environ.get('EDGE_SERVICE')
    # edge_service_port = os.environ.get("EDGE_SERVICE_PORT")
    # mongo_user = os.environ.get("MONGO_USER")
    # mongo_pass = os.environ.get("MONGO_PASS")
    # mongo_host = os.environ.get("MONGO_HOST")
    pass


class DataService(Resource):
    def __init__(self, queue):
        self.queue = queue

    def get(self):
        return jsonify({'status': True})

    def post(self):
        if request.is_json:
            json_msg = request.get_json(force=True)
            # send the command to orchestrator
            orchestrator_command = {
                "type":"request",
                "requester":"dataservice",
                "command": "request_on_data",
                "content": json_msg}
            self.queue.send(orchestrator_command)
            return jsonify({'status': "starting"})
        return jsonify({'status': 'request must enclose a json object'}), 400


class Queue(object):
    def __init__(self, config):
        self.amqp_queue_out = Amqp_Connector(config, self)

    def send(self, msg):
        self.amqp_queue_out.send_data(json.dumps(msg))

# may be read from config file
orchestrator_config = json.loads(orchestrator_queue.replace("\'","\""))
queue = Queue(orchestrator_config)

api.add_resource(DataService, '/dataservice',resource_class_args=(queue,))

if __name__ == '__main__':
    init_env_variables()

    app.run(debug=True, port=5000)