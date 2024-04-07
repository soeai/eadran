# We handle all management utilities service, including:
# 1. metadata (dataset info)
# 2. edge computing
# 3. training model
# 4. user/stakeholder
# 5. edge and federated server health info

import argparse
import json
import logging
import time
from threading import Thread
import pymongo
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Resource, Api
from qoa4ml.collector.amqp_collector import Amqp_Collector

from cloud.commons.default import ServiceConfig
from helpers.custom_logger import CustomLogger

app = Flask(__name__)
api = Api(app)

logger = CustomLogger().get_logger().setLevel(logging.INFO)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

# fedmarketplace_service = "management_service"
# fedmarketplace_service_port= "8006"
# mongo_conn = None


# def get_node_name():
#     node_name = os.environ.get('NODE_NAME')
#     if not node_name:
#         print("NODE_NAME is not defined")
#         node_name = "Empty"
#     return node_name
#
#
# def get_instance_id():
#     pod_id = os.environ.get('POD_ID')
#     if not pod_id:
#         print("POD_ID is not defined")
#         pod_id = "Empty"
#     return pod_id
#
#
# def init_env_variables():
#     edge_service = os.environ.get('FEDMARKETPLACE_SERVICE')
#     edge_service_port = os.environ.get("FEDMARKETPLACE_SERVICE_PORT")
#     # mongo_user = os.environ.get("MONGO_USER")
#     # mongo_pass = os.environ.get("MONGO_PASS")
#     # mongo_host = os.environ.get("MONGO_HOST")
#     # uri = "mongodb://%s:%s@%s" % (quote_plus(mongo_user), quote_plus(mongo_pass), mongo_host)
#     # mongo_conn = pymongo.MongoClient(uri)
#
#     if not edge_service:
#         logger.error("FEDMARKETPLACE_SERVICE is not defined")
#         raise Exception("FEDMARKETPLACE_SERVICE is not defined")
#     if not edge_service_port:
#         logger.error("FEDMARKETPLACE_SERVICE_PORT is not defined")
#         raise Exception("FEDMARKETPLACE_SERVICE_PORT is not defined")
#     # if not mongo_conn:
#     #     logger.error("Failed to MongoDB...{}".format(mongo_host))
#     #     raise Exception("Failed to MongoDB...{}".format(mongo_host))


class EdgeMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["edge_computing"]["db_name"]]) \
            if self.mongo_client[kwargs["edge_computing"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["edge_computing"]["db_name"]]
        self.collection = self.db[kwargs["edge_computing"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"edge_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
                    return jsonify({'result': response})

        return jsonify({"message": "missing query: id=???"}), 404

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
                    "edge_id": "12345",
                    "edge_name": "Edge 1",
                    "status": "active"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                        "edge_id": "edge001",
                        "edge_name": "Edge 1",
                        "status": "active"
                    },
                    {
                        "edge_id": "edge002",
                        "edge_name": "Edge 2",
                        "status": "active"
                    }
                ]
            }
            """
            # response = "false"
            if args['action'] == 1:
                data = args['data']
                # Check if edge_id already exists in the database
                if self.collection.find_one({"edge_id": data["edge_id"]}):
                    response = {"error": "Edge ID already exists"}
                else:
                    response = {"insert_id": str(self.collection.insert_one(data).inserted_id)}
            elif args['action'] == 2:
                data_list = args['data']
                # Check if any edge_id already exists in the database
                existing_ids = [edge["edge_id"] for edge in self.collection.find({}, {"_id": 0, "edge_id": 1})]
                duplicate_ids = [edge["edge_id"] for edge in data_list if edge["edge_id"] in existing_ids]
                if duplicate_ids:
                    response = {"error": f"Duplicated edge IDs: {', '.join(duplicate_ids)}"}
                else:
                    inserted_ids = [str(self.collection.insert_one(edge).inserted_id) for edge in data_list]
                    response = {"insert_ids": inserted_ids}
            else:
                response = {"error": f"Action {args['action']} is not supported"}
        else:
            response = {"error": "Request data must be in JSON format"}
            # get param from args here
        return jsonify({'status': "success", "response": response})

    def put(self):
        if request.is_json:
            args = request.get_json(force=True)
            """
            {
                "edge_id": "edge001",
                "update_data": {
                    "edge_name": "Updated Edge 1"
                }
            }
            """
            # Check if edge_id exists in the request
            if 'edge_id' not in args:
                return jsonify({"error": "Edge ID is missing in the request"}), 400

            edge_id = args['edge_id']
            update_data = args.get('update_data', {})

            # Check if edge_id exists in the database
            existing_edge = self.collection.find_one({"edge_id": edge_id})
            if existing_edge:
                # Update the edge with the provided data
                self.collection.update_one({"edge_id": edge_id}, {"$set": update_data})
                return jsonify({"message": f"Edge with ID {edge_id} updated successfully"}), 200
            else:
                return jsonify({"error": f"Edge with ID {edge_id} not found"}), 404
        else:
            return jsonify({"error": "Request data must be in JSON format"}), 400

    def delete(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                r = self.collection.find_one_and_delete({"edge_id": query[1]})
                return jsonify({"message": "deleted \'{}\'".format(r.get("edge_id"))})

        return jsonify({"message": "missing query: id=???"}), 404


class ComputingResourceHealth(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["edge_health_log"]["db_name"]]) \
            if self.mongo_client[kwargs["edge_health_log"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["edge_health_log"]["db_name"]]
        self.collection = self.db[kwargs["edge_health_log"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"edge_id":query[1],"timestamp": {"$gt": time.time() - 600}}).sort([('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
                    return jsonify({'result': response})

        return jsonify({"message": "missing query: id=???"}), 404


class FedServerHealth(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["fedserver_health_log"]["db_name"]]) \
            if self.mongo_client[kwargs["fedserver_health_log"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["fedserver_health_log"]["db_name"]]
        self.collection = self.db[kwargs["fedserver_health_log"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"server_id":query[1],"timestamp": {"$gt": time.time() - 600}}).sort([('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0] #get ip from query result
                    response.pop('_id', None)
                    return jsonify({'result': response})

        return jsonify({"message": "missing query: id=???"}), 404


class EdgeHealthReport(object):
    def __init__(self, config):
        self.amqp_collector = Amqp_Collector(config['amqp_health_report'], self)
        Thread(target=self.start_amqp).start()
        self.mongo_client = pymongo.MongoClient(config['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[config["edge_health_log"]["db_name"]]) \
            if self.mongo_client[config["edge_health_log"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[config["edge_health_log"]["db_name"]]
        self.collection = self.db[config["edge_health_log"]["db_col"]]

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("\'", "\""))
        req_msg['timestamp'] = time.time()
        self.collection.insert_one(req_msg)

    def start_amqp(self):
        self.amqp_collector.start()


class MetadataMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.mongo_client = pymongo.MongoClient(config['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["metadata"]["db_name"]]) \
            if self.mongo_client[kwargs["metadata"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["metadata"]["db_name"]]
        self.collection = self.db[kwargs["metadata"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"dataset_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
                    return jsonify({'result': response})

        return jsonify({"message": "missing query: id=???"}), 404

    # add new dataset info
    def post(self):
        if request.is_json:
            req_args = request.get_json(force=True)
            print(req_args)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "dataset_id": "ds001",
                    "description": "fraud",
                    "no_of_samples": 123,
                    "qod_ref": {
                        "_comment": "metric of quality of data",
                        "ref": "http://...",
                        "values": {}
                    },
                    "cxt_ref": {
                        "_comment": "metric of data in context",
                        "ref": "http://...",
                        "values": {}
                    },
                    "qod_weight": {},
                    "cxt_weight": {},
                    "qod_unit_price": 1.0,
                    "cxt_unit_price": 1.0,
                    "cost_formula": "formula to evaluate the cost",
                    "features": [],
                    "edge_computings": [],
                    "data_access": {
                        "type": "file (database|cloud)",
                        "location": "user@ip:/home/data.csv",
                        "key": ""
                    },
                    "owner": "dp123"
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data": [
                    {
                        "dataset_id": "ds001",
                        "description": "fraud",
                        "no_of_samples": 123,
                        "qod_ref": {
                            "_comment": "metric of quality of data",
                            "ref": "http://...",
                            "values": {}
                        },
                        "cxt_ref": {
                            "_comment": "metric of data in context",
                            "ref": "http://...",
                            "values": {}
                        },
                        "qod_weight": {},
                        "cxt_weight": {},
                        "qod_unit_price": 1.0,
                        "cxt_unit_price": 1.0,
                        "cost_formula": "formula to evaluate the cost",
                        "features": [],
                        "edge_computings": [],
                        "data_access": {
                            "type": "file (database|cloud)",
                            "location": "user@ip:/home/data.csv",
                            "key": ""
                        },
                        "owner": "dp123"
                    },
                    {
                        "dataset_id": "ds002",
                        "description": "another dataset",
                        "no_of_samples": 200,
                        "qod_ref": {
                            "_comment": "metric of quality of data",
                            "ref": "http://...",
                            "values": {}
                        },
                        "cxt_ref": {
                            "_comment": "metric of data in context",
                            "ref": "http://...",
                            "values": {}
                        },
                        "qod_weight": {},
                        "cxt_weight": {},
                        "qod_unit_price": 1.0,
                        "cxt_unit_price": 1.0,
                        "cost_formula": "formula to evaluate the cost",
                        "features": [],
                        "edge_computings": [],
                        "data_access": {
                            "type": "file (database|cloud)",
                            "location": "user@ip:/home/data2.csv",
                            "key": ""
                        },
                        "owner": "dp456"
                    }
                ]
            }
            """
            # response = "false"
            if (req_args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(req_args['data']).inserted_id)}
            elif (req_args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(req_args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(req_args['action'])
        else:
            response = "Invalid JSON format"
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # update dataset info
    def put(self):
        pass
        # if request.is_json:
        #     args = request.get_json(force=True)
        # # get param from args here
        # return jsonify({'status': True})

    def delete(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                r = self.collection.find_one_and_delete({"dataset_id": query[1]})
                return jsonify({"message": "deleted \'{}\'".format(r.get("dataset_id"))})

        return jsonify({"message": "missing query: id=???"}), 404


class ModelMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["model_management"]["db_name"]]) \
            if self.mongo_client[kwargs["model_management"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["model_management"]["db_name"]]
        self.collection = self.db[kwargs["model_management"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                result = list(self.collection.find({"model_id": query[1]}).sort(
                    [('timestamp', pymongo.DESCENDING)]).limit(1))
                if len(result) > 0:
                    response = result[0]
                    response.pop('_id', None)
                    return jsonify({'result': response})

        return jsonify({"message": "missing query: id=???"}), 404

    # insert new model info
    def post(self):
        if request.is_json:
            req_args = request.get_json(force=True)
            print(req_args)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    "model_id": "model001",
                    "name": "Detection Model",
                    "description": "detection",
                    "owner": "user123",
                    "created_at": "2024-03-26 11:30:00",
                    "training_code": {
                        "module_name": "code for training at edges",
                        "function_map": {
                            "train": "fit",
                            "evaluate": "evaluate",
                            "set_weights": "set_weights",
                            "get_weights": "get_weights"
                        },
                        "train_hyper_param": {
                            "epochs": 10,
                            "batch_size": 32
                        }
                    },
                    "pre_train_model": {
                        "url": "link to get pre-train model",
                        "name": "pre-trained model name",
                        "params": "optional params to download"
                    }
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                    "model_id": "model001",
                    "name": "Detection Model",
                    "description": "detection",
                    "owner": "user123",
                    "created_at": "2024-03-26 11:30:00",
                    "training_code": {
                        "module_name": "code for training at edges",
                        "function_map": {
                            "train": "fit",
                            "evaluate": "evaluate",
                            "set_weights": "set_weights",
                            "get_weights": "get_weights"
                        },
                        "train_hyper_param": {
                            "epochs": 10,
                            "batch_size": 32
                        }
                    },
                    "pre_train_model": {
                        "url": "link to get pre-train model",
                        "name": "pre-trained model name",
                        "params": "optional params to download"
                    }
                },
                {
                    "model_id": "model002",
                    "name": "Another Model",
                    "description": "Another description",
                    "owner": "user456",
                    "created_at": "2024-03-27 13:45:00",
                    "training_code": {
                        "module_name": "code for training at edges",
                        "function_map": {
                            "train": "fit",
                            "evaluate": "evaluate",
                            "set_weights": "set_weights",
                            "get_weights": "get_weights"
                        },
                        "train_hyper_param": {
                            "epochs": 15,
                            "batch_size": 64
                        }
                    },
                    "pre_train_model": {
                        "url": "link to get pre-train model",
                        "name": "pre-trained model name",
                        "params": "optional params to download"
                    }
                }
            ]
        }
            """
            # response = "false"
            if (req_args['action'] == 1):
                response = {"insert_id":str(self.collection.insert_one(req_args['data']).inserted_id)}
            elif (req_args['action'] == 2):
                response = {"insert_ids":str(self.collection.insert_many(req_args['data']).inserted_ids)}
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(req_args['action'])
        # get param from args here
        return jsonify({'status': "success", "response":response})

    # update an existing model info
    def put(self):
        #pass
        # if request.is_json:
        #     args = request.get_json(force=True)
        # # get param from args here
        # return jsonify({'status': True})
        if request.is_json:
            req_args = request.get_json(force=True)
            if 'model_id' in req_args:
                updated_model = self.collection.find_one_and_update(
                    {"model_id": req_args['model_id']},
                    {"$set": req_args['update_data']},
                    return_document=True
                )
                if updated_model:
                    return jsonify({'status': "success", "response": updated_model})
                else:
                    return jsonify({'status': "error", "response": "Model not found."}), 404
            else:
                return jsonify({'status': "error", "response": "Missing model_id in request."}), 400
        return jsonify({'status': "error", "response": "Invalid JSON payload."})

    def delete(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                r = self.collection.find_one_and_delete({"model_id": query[1]})
                return jsonify({"message": "deleted \'{}\'".format(r.get("model_id"))})

        return jsonify({"message": "missing query: id=???"}), 404


class UserMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["user_management"]["db_name"]]) \
            if self.mongo_client[kwargs["user_management"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["user_management"]["db_name"]]
        self.collection = self.db[kwargs["user_management"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
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
    def delete(self):
        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                r = self.collection.find_one_and_delete({"user_id": query[1]})
                return jsonify({"message": "deleted \'{}\'".format(r.get("user_id"))})

        return jsonify({"message": "missing query: id=???"}), 404


if __name__ == '__main__': 
    # init_env_variables()
    parser = argparse.ArgumentParser(description="Arguments for Management Service")
    parser.add_argument('--conf', help='configuration file', default="./conf/config.json")
    args = parser.parse_args()
    with open(args.conf) as f:
        config = json.loads(f.read())

    # queue to get health info from edge and federated server
    queue = EdgeHealthReport(config)

    # service to check health of edge and federated server
    api.add_resource(ComputingResourceHealth, '/edgehealth', resource_class_kwargs=config)
    api.add_resource(FedServerHealth, '/serverhealth', resource_class_kwargs=config)

    # management service
    api.add_resource(EdgeMgt, '/edge', resource_class_kwargs=config)
    api.add_resource(MetadataMgt, '/metadata',resource_class_kwargs=config)
    api.add_resource(ModelMgt, '/model',resource_class_kwargs=config)
    api.add_resource(UserMgt, '/user',resource_class_kwargs=config)

    # run service
    app.run(debug=True, port=ServiceConfig.MGT_SERVICE_PORT)