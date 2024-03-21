# We handle all management utilities service, including:
# 1. metadata
# 2. resource computing
# 3. training model
# 4. user/stakeholder
import json
import os
import time
from threading import Thread
from urllib.parse import quote_plus

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import pymongo
import json, argparse
from qoa4ml.collector.amqp_collector import Amqp_Collector
from cloud.commons.default import ServiceConfig

from helpers.custom_logger import CustomLogger
import logging
app = Flask(__name__)
api = Api(app)

logger = CustomLogger().get_logger().setLevel(logging.INFO)

fedmarketplace_service = "management_service"
fedmarketplace_service_port= "8006"
mongo_conn = None


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
    edge_service = os.environ.get('FEDMARKETPLACE_SERVICE')
    edge_service_port = os.environ.get("FEDMARKETPLACE_SERVICE_PORT")
    # mongo_user = os.environ.get("MONGO_USER")
    # mongo_pass = os.environ.get("MONGO_PASS")
    # mongo_host = os.environ.get("MONGO_HOST")
    # uri = "mongodb://%s:%s@%s" % (quote_plus(mongo_user), quote_plus(mongo_pass), mongo_host)
    # mongo_conn = pymongo.MongoClient(uri)

    if not edge_service:
        logger.error("FEDMARKETPLACE_SERVICE is not defined")
        raise Exception("FEDMARKETPLACE_SERVICE is not defined")
    if not edge_service_port:
        logger.error("FEDMARKETPLACE_SERVICE_PORT is not defined")
        raise Exception("FEDMARKETPLACE_SERVICE_PORT is not defined")
    # if not mongo_conn:
    #     logger.error("Failed to MongoDB...{}".format(mongo_host))
    #     raise Exception("Failed to MongoDB...{}".format(mongo_host))


class ComputingResourceMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.conf = kwargs
        self.mongo_url = kwargs['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[kwargs["computing_resource"]["db_name"]]
        self.collection = self.db[kwargs["computing_resource"]["db_col"]]

    def get(self):
        args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(args) > 0:
            # get param from args here
            query = args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"edge_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
        return jsonify({'result': response})

    def post(self):
        if request.is_json:
            args = request.get_json(force=True)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "attributes": "sample"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                        "attributes": "sample"
                    },
                    {
                        "attributes": "sample2"
                    }
                ]
            }
            """
            # response = "false"
            if (args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(args['data']).inserted_id)}
            elif (args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(args['action'])
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # def put(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': "Not support yet!"})
    #
    # def delete(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': "Not support yet!"})


class ComputingResourceHealth(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.conf = kwargs
        self.mongo_url = kwargs['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[kwargs["computing_health_log"]["db_name"]]
        self.collection = self.db[kwargs["computing_health_log"]["db_col"]]

    def get(self):
        response = "false"
        args = request.query_string.decode("utf-8").split("&")
        if len(args) > 0:
            # get param from args here
            query = args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"edge_id":query[1],"timestamp": {"$gt": time.time() - 600}}).sort([('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
        return jsonify({'status': response})


class Configuration(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.conf = kwargs
        self.mongo_url = kwargs['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[kwargs["computing_resource"]["db_name"]]
        self.collection = self.db[kwargs["computing_resource"]["db_col"]]

    def get(self):
        args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(args) > 0:
            # get param from args here
            query = args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"config_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
        return jsonify({'result': response})


    def post(self):
        if request.is_json:
            args = request.get_json(force=True)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "attributes": "sample"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                        "attributes": "sample"
                    },
                    {
                        "attributes": "sample2"
                    }
                ]
            }
            """
            # response = "false"
            if (args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(args['data']).inserted_id)}
            elif (args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(args['action'])
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # def put(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': "Not support yet!"})
    #
    # def delete(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': "Not support yet!"})


class EdgeHealthReport(object):
    def __init__(self, config):
        self.amqp_collector = Amqp_Collector(config['amqp_health_report'], self)
        Thread(target=self.start_amqp).start()
        self.mongo_url = config['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[config["computing_health_log"]["db_name"]]
        self.collection = self.db[config["computing_health_log"]["db_col"]]

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        req_msg['timestamp'] = time.time()
        self.collection.insert_one(req_msg)

    def start_amqp(self):
        self.amqp_collector.start()


class MetadataMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.conf = kwargs
        self.mongo_url = kwargs['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[kwargs["metadata"]["db_name"]]
        self.collection = self.db[kwargs["metadata"]["db_col"]]


    def get(self):
        args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(args) > 0:
            # get param from args here
            query = args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"dataset_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
        return jsonify({'result': response})

    def post(self):
        if request.is_json:
            args = request.get_json(force=True)
            print(args)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "attributes": "sample"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                        "attributes": "sample"
                    },
                    {
                        "attributes": "sample2"
                    }
                ]
            }
            """
            # response = "false"
            if (args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(args['data']).inserted_id)}
            elif (args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(args['action'])
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # def put(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': True})
    #
    # def delete(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': True})


class ModelMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.conf = kwargs
        self.mongo_url = kwargs['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[kwargs["model_management"]["db_name"]]
        self.collection = self.db[kwargs["model_management"]["db_col"]]

    def get(self):
        args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(args) > 0:
            # get param from args here
            query = args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"model_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
        return jsonify({'result': response})

    def post(self):
        if request.is_json:
            args = request.get_json(force=True)
            print(args)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "attributes": "sample"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                        "attributes": "sample"
                    },
                    {
                        "attributes": "sample2"
                    }
                ]
            }
            """
            # response = "false"
            if (args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(args['data']).inserted_id)}
            elif (args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(args['action'])
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # def put(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': True})
    #
    # def delete(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': True})


class UserMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.conf = kwargs
        self.mongo_url = kwargs['mongo_url']
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[kwargs["user_management"]["db_name"]]
        self.collection = self.db[kwargs["user_management"]["db_col"]]

    def get(self):
        args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(args) > 0:
            # get param from args here
            query = args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"user_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
        return jsonify({'result': response})

    def post(self):
        if request.is_json:
            args = request.get_json(force=True)
            print(args)
            """
            Action table:
            0 - drop all collection
            # no data require
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "attributes": "sample"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                        "attributes": "sample"
                    },
                    {
                        "attributes": "sample2"
                    }
                ]
            }
            """
            response = "false"
            if (args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(args['data']).inserted_id)}
            elif (args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(args['action'])
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # def put(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': True})
    #
    # def delete(self):
    #     if request.is_json:
    #         args = request.get_json(force=True)
    #     # get param from args here
    #     return jsonify({'status': args})


if __name__ == '__main__': 
    # init_env_variables()
    parser = argparse.ArgumentParser(description="Argument for Management Service")
    parser.add_argument('--conf', help='configuration file', default="./conf/config.json")
    args = parser.parse_args()
    conf_file = args.conf
    with open(conf_file) as f:
        config = json.loads(f.read())

    queue = EdgeHealthReport(config)
    api.add_resource(Configuration, '/resource', resource_class_kwargs=config)
    api.add_resource(ComputingResourceHealth, '/health', resource_class_kwargs=config)
    api.add_resource(MetadataMgt, '/metadata',resource_class_kwargs=config)
    api.add_resource(ModelMgt, '/model',resource_class_kwargs=config)
    api.add_resource(UserMgt, '/user',resource_class_kwargs=config)
    # api.add_resource(Configuration, '/config', resource_class_kwargs=config)
    app.run(debug=True, port=ServiceConfig.MGT_SERVICE_PORT)