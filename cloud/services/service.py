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
import uuid
import jwt
import pymongo
from flask import Flask, request
from flask_cors import CORS
from flask_restful import Resource, Api
from qoa4ml.collector.amqp_collector import AmqpCollector, HostObject, AMQPCollectorConfig
from qoa4ml.connector.amqp_connector import AmqpConnector, AMQPConnectorConfig
import hashlib
from cloud.commons.default import Service, Protocol

app = Flask(__name__)
api = Api(app)

cors = CORS(app, resources={r"/*": {"origins": "*"}})
mongo_client = None
auth_collection = None


class EdgeMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.db = (
            mongo_client.get_database(kwargs["edge_computing"]["db_name"])
            if kwargs["edge_computing"]["db_name"] in mongo_client.list_database_names()
            else mongo_client[kwargs["edge_computing"]["db_name"]]
        )
        self.collection = self.db[kwargs["edge_computing"]["db_col"]]

    def get(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                result = list(
                    self.collection.find({"edge_id": query[1]})
                        .sort([("timestamp", pymongo.DESCENDING)])
                        .limit(1)
                )
                if len(result) > 0:
                    response = result[0]
                    response.pop("_id", None)
                    return {"code": 0, "result": response}
                else:
                    return {"status": 1, "message": "your edge does not exist."}, 404
            if query[0] == "owner":
                result = list(
                    self.collection.find({"owner": query[1]}).sort(
                        [("timestamp", pymongo.DESCENDING)]
                    )
                )
                if len(result) > 0:
                    for r in result:
                        r.pop("_id", None)
                    return {"code": 0, "result": result}
                else:
                    return {"code": 0, "result": []}
        return {"code": 1, "message": "missing query: id=???"}, 404

    def post(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login

        if request.is_json:
            req_args = request.get_json(force=True)
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
            if req_args["action"] == 1:
                data = req_args["data"]
                # Check if edge_id already exists in the database
                if self.collection.find_one({"edge_id": data["edge_id"]}):
                    return {"code": 1, "message": "Edge ID already exists"}, 400
                else:
                    return {
                        "code": 0,
                        "result": str(self.collection.insert_one(data).inserted_id),
                    }
            elif req_args["action"] == 2:
                data_list = req_args["data"]
                # Check if any edge_id already exists in the database
                existing_ids = [
                    edge["edge_id"] for edge in self.collection.find({}, {"_id": 0, "edge_id": 1})
                ]
                duplicate_ids = [
                    edge["edge_id"] for edge in data_list if edge["edge_id"] in existing_ids
                ]
                if duplicate_ids:
                    return {
                               "code": 1,
                               "message": f"Duplicated edge IDs: {', '.join(duplicate_ids)}",
                           }, 400
                else:
                    inserted_ids = [
                        str(self.collection.insert_one(edge).inserted_id)
                        for edge in data_list
                    ]
                    return {"code": 0, "result": inserted_ids}
            else:
                return {
                           "code": 1,
                           "message": f"Action {req_args['action']} is not supported",
                       }, 400
        return {"code": 1, "message": "Request data must be in JSON format"}, 400

    def put(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login

        if request.is_json:
            req_args = request.get_json(force=True)
            """
            {
                "edge_id": "edge001",
                "update_data": {
                    "edge_name": "Updated Edge 1"
                }
            }
            """
            # Check if edge_id exists in the request
            if "edge_id" not in req_args:
                return {
                           "code": 1,
                           "message": "Edge ID is missing in the request",
                       }, 400

            edge_id = req_args["edge_id"]
            update_data = req_args.get("update_data", {})

            # Check if edge_id exists in the database
            existing_edge = self.collection.find_one({"edge_id": edge_id})
            if existing_edge:
                # Update the edge with the provided data
                self.collection.update_one({"edge_id": edge_id}, {"$set": update_data})
                return {
                    "code": 0,
                    "result": f"Edge with ID {edge_id} updated successfully",
                }
            else:
                return {
                           "code": 1,
                           "message": f"Edge with ID {edge_id} not found",
                       }, 404

        return {"code": 1, "message": "Request data must be in JSON format"}, 400

    def delete(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login

        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                r = self.collection.find_one_and_delete({"edge_id": query[1]})
                return {"code": 0, "result": "deleted '{}'".format(r.get("edge_id"))}

        return {"code": 1, "message": "missing query: id=???"}, 404


class ComputingResourceHealth(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.db = (
            mongo_client.get_database(kwargs["health_log"]["db_name"])
            if kwargs["health_log"]["db_name"] in mongo_client.list_database_names()
            else mongo_client[kwargs["health_log"]["db_name"]]
        )
        self.collection = self.db[kwargs["health_log"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                result = list(
                    self.collection.find(
                        {"edge_id": query[1], "timestamp": {"$gt": time.time() - 600}}
                    )
                        .sort([("timestamp", pymongo.DESCENDING)])
                        .limit(1)
                )
                if len(result) > 0:
                    response = result[0]
                    response.pop("_id", None)
                    return {"code": 0, "result": response}

        return {"code": 1, "message": "missing query: id=???"}, 404


class ResourceHealthReport(HostObject):
    def __init__(self, _config):
        self.amqp_collector_config = AMQPCollectorConfig(
            **_config["amqp_health_report"]['amqp_in']['amqp_collector']['conf'])
        self.amqp_collector = AmqpCollector(self.amqp_collector_config, self)
        Thread(target=self.start_amqp).start()

        db_edge = (
            mongo_client.get_database(_config["health_log"]["db_name"])
            if _config["health_log"]["db_name"] in mongo_client.list_database_names()
            else mongo_client[_config["health_log"]["db_name"]]
        )
        self.collection_edge = db_edge[_config["health_log"]["db_col"]]

        db_service = (
            mongo_client.get_database(_config["service_log"]["db_name"])
            if _config["service_log"]["db_name"]
               in mongo_client.list_database_names()
            else mongo_client[_config["service_log"]["db_name"]]
        )
        self.collection_service = db_service[_config["service_log"]["db_col"]]

    def message_processing(self, ch, method, props, body):
        req_msg = json.loads(str(body.decode("utf-8")).replace("'", '"'))
        if req_msg['type'] == "edge":
            req_msg.pop('type', None)
            req_msg["timestamp"] = time.time()
            self.collection_edge.insert_one(req_msg)
        elif req_msg['type'] == "service":
            req_msg.pop('type', None)
            self.collection_service.find_one_and_update(
                    {"request_id": req_msg["request_id"]},
                    {"$set": {"status": "finished" if req_msg['code'] == 0 else "error", "finish_at": time.time()}}
                )

    def start_amqp(self):
        self.amqp_collector.start_collecting()


class MetadataMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.db = (
            mongo_client.get_database(kwargs["metadata"]["db_name"])
            if kwargs["metadata"]["db_name"] in mongo_client.list_database_names()
            else mongo_client[kwargs["metadata"]["db_name"]]
        )
        self.collection = self.db[kwargs["metadata"]["db_col"]]

    def get(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                result = list(
                    self.collection.find({"dataset_id": query[1]})
                        .sort([("timestamp", pymongo.DESCENDING)])
                        .limit(1)
                )
                if len(result) > 0:
                    response = result[0]
                    response.pop("_id", None)
                    return {"code": 0, "result": response}
                else:
                    return {"code": 1, "message": "your dataset does not exist."}, 404
            if query[0] == "owner":
                result = list(
                    self.collection.find({"owner": query[1]}).sort(
                        [("timestamp", pymongo.DESCENDING)]
                    )
                )
                if len(result) > 0:
                    for r in result:
                        r.pop("_id", None)
                    return {"code": 0, "result": result}
                else:
                    return {"code": 0, "result": []}
        return {"code": 1, "message": "missing query: id=???"}, 404

    # add new dataset info
    def post(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        if request.is_json:
            req_args = request.get_json(force=True)
            # print(req_args)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    data object
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data": [
                    {
                        data object
                    },
                    {
                        data object
                    }
                ]
            }
            """
            # response = "false"
            if req_args["action"] == 1:
                response = str(self.collection.insert_one(req_args["data"]).inserted_id)
            elif req_args["action"] == 2:
                response = str(
                    self.collection.insert_many(req_args["data"]).inserted_ids
                )
            else:
                # self.collection.drop()
                response = "Action {} Not support Yet!".format(req_args["action"])
        else:
            response = "Invalid JSON format"
        # get param from args here
        return {"code": 0, "result": response}

    # update dataset info
    def put(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        if request.is_json:
            req_args = request.get_json(force=True)
            if "dataset_id" in req_args:
                updated_dataset = self.collection.find_one_and_update(
                    {"dataset_id": req_args["dataset_id"]},
                    {"$set": req_args["update_data"]},
                    return_document=True,
                )
                if updated_dataset:
                    return {"code": 0, "result": updated_dataset}
                else:
                    return {"code": 1, "message": "Data not found."}, 404
            else:
                return {"code": 1, "message": "Missing dataset_id in request."}, 400
        return {"code": 1, "message": "Invalid JSON payload."}

    def delete(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login

        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            query = req_args[0].split("=")
            if query[0] == "id":
                r = self.collection.find_one_and_delete({"dataset_id": query[1]})
                return {
                    "code": 0,
                    "message": "deleted '{}'".format(r.get("dataset_id")),
                }
            elif query[0] == "owner":
                result = self.collection.delete_many({"owner": query[1]})
                return {
                    "code": 0,
                    "message": "deleted {} records for owner '{}'".format(result.deleted_count, query[1]),
                }

        return {"code": 1, "message": "missing query: id=??? or owner=???"}, 404


class ModelMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.db = (
            mongo_client.get_database(kwargs["model_management"]["db_name"])
            if kwargs["model_management"]["db_name"]
               in mongo_client.list_database_names()
            else mongo_client[kwargs["model_management"]["db_name"]]
        )
        self.collection = self.db[kwargs["model_management"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")

        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                result = list(
                    self.collection.find({"model_id": query[1]})
                        .sort([("timestamp", pymongo.DESCENDING)])
                        .limit(1)
                )
                if len(result) > 0:
                    response = result[0]
                    response.pop("_id", None)
                    return {"code": 0, "result": response}
                else:
                    return {"code": 1, "message": "your model does not exist!"}, 404
            if query[0] == "owner":
                result = list(
                    self.collection.find({"owner": query[1]}).sort(
                        [("timestamp", pymongo.DESCENDING)]
                    )
                )
                if len(result) > 0:
                    for r in result:
                        r.pop("_id", None)
                    return {"code": 0, "result": result}
                else:
                    return {"code": 0, "result": []}

        return {"code": 1, "message": "missing query: id=???"}, 404

    # insert new model info
    def post(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        if request.is_json:
            req_args = request.get_json(force=True)
            """
            Action table:
            1 - insert one 
            Example:
            {
                "action": 1,
                "data":{
                    data object
                }
            }
            2 - insert many
            Example:
            {
                "action": 2,
                "data":[
                    {
                    data object
                },
                {
                    data object
                }
            ]
        }
            """
            if req_args["action"] == 1:
                response = str(self.collection.insert_one(req_args["data"]).inserted_id)
            elif req_args["action"] == 2:
                response = str(
                    self.collection.insert_many(req_args["data"]).inserted_ids
                )
            else:
                response = "Action {} Not support Yet!".format(req_args["action"])

        return {"code": 0, "result": response}

    # update an existing model info
    def put(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login, 401

        if request.is_json:
            req_args = request.get_json(force=True)
            if "model_id" in req_args:
                updated_model = self.collection.find_one_and_update(
                    {"model_id": req_args["model_id"]},
                    {"$set": req_args["update_data"]},
                    return_document=True,
                )
                if updated_model:
                    return {"code": 0, "message": updated_model}
                else:
                    return {"code": 1, "message": "Model not found."}, 404
            else:
                return {"code": 0, "message": "Missing model_id in request."}, 400
        return {"code": 1, "message": "Invalid JSON payload."}

    def delete(self):
        check_login = required_auth()
        if check_login is not None:
            return check_login

        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                r = self.collection.find_one_and_delete({"model_id": query[1]})
                return {
                    "code": 0,
                    "message": "deleted '{}'".format(r.get("model_id")),
                }

        return {"code": 1, "message": "missing query: id=???"}, 404


class UserMgt(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.db = (
            mongo_client.get_database(kwargs["user_management"]["db_name"])
            if kwargs["user_management"]["db_name"]
               in mongo_client.list_database_names()
            else mongo_client[kwargs["user_management"]["db_name"]]
        )
        self.collection = self.db[kwargs["user_management"]["db_col"]]

    def get(self):
        # check_login = required_auth()
        # if check_login is not None:
        #     return check_login

        req_args = request.query_string.decode("utf-8").split("&")

        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                result = list(
                    self.collection.find({"username": query[1]})
                        .sort([("timestamp", pymongo.DESCENDING)])
                        .limit(1)
                )
                if len(result) > 0:
                    response = result[0]
                    response.pop("_id", None)
                    response.pop("password", None)
                else:
                    return {"code": 1, "message": "user does not exist."}, 404

                return {"code": 0, "result": response}
        return {"code": 1, "message": "query string must provided."}, 400

    def post(self):
        # check_login = required_auth()
        # if check_login is not None:
        #     return check_login

        if request.is_json:
            req_args = request.get_json(force=True)
            """
            Example:
            {
                "username": "",
                "email": "",
                "fullname": "",
                "password": "",
                "role": ""
            }
            """
            # encrypt password
            req_args["password"] = hashlib.md5(
                str(req_args["password"]).encode()
            ).hexdigest()

            response = str(self.collection.insert_one(req_args).inserted_id)

            return {"code": 0, "message": response}
        return {"code": 1, "message": "content must be JSON."}, 400

    def put(self):
        if request.is_json:
            req_args = request.get_json(force=True)
            if "username" in req_args:
                update_fields = {}
                if "email" in req_args:
                    update_fields["email"] = req_args["email"]
                if "fullname" in req_args:
                    update_fields["fullname"] = req_args["fullname"]
                if "role" in req_args:
                    update_fields["role"] = req_args["role"]

                if update_fields:
                    updated_user = self.collection.find_one_and_update(
                        {"username": req_args["username"]},
                        {"$set": update_fields},
                        return_document=pymongo.ReturnDocument.AFTER,
                    )
                    if updated_user:
                        updated_user.pop("_id", None)
                        updated_user.pop("password", None)
                        return {"code": 0, "result": updated_user}
                    else:
                        return {"code": 1, "message": "User not found."}, 404
                else:
                    return {"code": 1, "message": "No fields to update."}, 400
            else:
                return {"code": 1, "message": "Missing username in request."}, 400

        return {"code": 1, "message": "Invalid JSON payload."}

    def delete(self):
        # check_login = required_auth()
        # if check_login is not None:
        #     return check_login

        req_args = request.query_string.decode("utf-8").split("&")
        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                r = self.collection.find_one_and_delete({"username": query[1]})
                return {
                    "code": 0,
                    "message": "deleted '{}'".format(r.get("username")),
                }

        return {"code": 1, "message": "missing query: id=???"}, 404


class Authentication(Resource):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config = kwargs
        self.db = (
            mongo_client.get_database(kwargs["user_management"]["db_name"])
            if kwargs["user_management"]["db_name"]
               in mongo_client.list_database_names()
            else mongo_client[kwargs["user_management"]["db_name"]]
        )
        self.collection = self.db[kwargs["user_management"]["db_col"]]

    def post(self):
        if request.is_json:
            """
            {
                "username": "",
                "password": "",
                "role": ""
            }
            """
            req_args = request.get_json(force=True)
            # ADD CODE TO CHECK USER:PASS CORRECT
            if "username" in req_args.keys() and "password" in req_args.keys():
                result = list(self.collection.find({"username": req_args["username"]}))
                if len(result) > 0:
                    # encrypt password
                    pwd = hashlib.md5(str(req_args["password"]).encode()).hexdigest()
                    if result[0]["password"] == pwd:
                        session_id = jwt.encode(req_args, self.config["secret_key"])
                        auth_collection.insert_one({"session_id": session_id})
                        return {"code": 0, "session_id": session_id}
                else:
                    return {
                               "code": 1,
                               "message": "username or password is not correct",
                           }, 401
        return {
                   "code": 1,
                   "message": "request body must be in JSON format. {username: xxx, password: yyy}",
               }, 401


class EADRANService(Resource):
    def __init__(self, queue_out, **kwargs) -> None:
        super().__init__()
        self.config = kwargs
        self.queue = queue_out
        self.db = (
            mongo_client.get_database(kwargs["service_log"]["db_name"])
            if kwargs["service_log"]["db_name"]
               in mongo_client.list_database_names()
            else mongo_client[kwargs["service_log"]["db_name"]]
        )
        self.collection = self.db[kwargs["service_log"]["db_col"]]

    def get(self,op):
        req_args = request.query_string.decode("utf-8").split("&")

        # get param from args here
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == "id":
                if op == 'model':
                    result = list(
                        self.collection.find({"content.model_id": query[1]})
                            .sort([("init_at", pymongo.DESCENDING)])
                    )
                elif op == "edge":
                    result = list(
                        self.collection.find({"content.edge_id": query[1]})
                            .sort([("init_at", pymongo.DESCENDING)])
                    )
                elif op == "status":
                    result = list(
                        self.collection.find({"request_id": query[1]})
                            .sort([("init_at", pymongo.DESCENDING)])
                    )
                if len(result) > 0:
                    for r in result:
                        r.pop("_id", None)
                    return {"code": 0, "result": result}
                else:
                    return {"code": 1, "message": "*_id does not exist."}, 404

            return {"code": 1, "message": "query string must provide (id=?? or id=??)."}, 404

    def post(self, op):
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
            if op in ['trainml', 'data', 'qod']:
                request_id = str(uuid.uuid4())
                # send the command to orchestrator
                if op == "trainml":
                    orchestrator_command = {
                        "type": Protocol.MSG_REQUEST,
                        "requester": Protocol.ACTOR_TRAINING_SERVICE,
                        "command": Protocol.TRAIN_MODEL_COMMAND,
                        "request_id": request_id,
                        "content": json_msg,
                    }

                elif op == "data":
                    orchestrator_command = {
                        "type": Protocol.MSG_REQUEST,
                        "requester": Protocol.ACTOR_DATA_SERVICE,
                        "command": Protocol.DATA_EXTRACTION_COMMAND,
                        "request_id": request_id,
                        "content": json_msg,
                    }
                elif op == "qod":
                    orchestrator_command = {
                        "type": Protocol.MSG_REQUEST,
                        "requester": Protocol.ACTOR_DATA_SERVICE,
                        "command": Protocol.DATA_QOD_COMMAND,
                        "request_id": request_id,
                        "content": json_msg,
                    }
                self.queue.send(orchestrator_command)
                db_msg = orchestrator_command.copy()
                db_msg.pop("type")
                db_msg.pop("requester")
                db_msg['status'] = "initializing"
                db_msg["init_at"] = time.time()
                self.collection.insert_one(db_msg)
                return {"code": 0,
                        "message": "initializing",
                        "request_id": request_id,
                        "comment": "Get the status of the process /service/status?id=request_id"}
            elif op == 'report':
                if json_msg['type'] == "response":
                    self.collection.find_one_and_update(
                        {"request_id": json_msg["request_id"]},
                        {"$set": {"status": "processing" if json_msg['code'] == 0 else "error", "start_at": time.time()}}
                    )
                    return {"code": 0, "message": "updated"}
                elif json_msg['type'] == 'qod_report':
                    self.collection.find_one_and_update(
                        {"request_id": json_msg["request_id"]},
                        {"$set": {
                            "qod": json_msg['qod'],
                            "status": "finished" if json_msg['code'] == 0 else "error",
                            "finish_at": time.time()}}
                    )
                    return {"code": 0, "message": "updated"}
        return {"code": 1, "message": "request must enclose a json object"}, 400


# in case of client want to start more edges/datasets
class ControlEdge(Resource):
    def __init__(self, queue):
        self.queue = queue

    def get(self):
        return {"code": 0}

    def post(self, op):
        # get param from args here
        msg = "starting" if op == "start" else "stopping"
        cmd = (
            Protocol.START_CONTAINER_COMMAND
            if op == "start"
            else Protocol.STOP_CONTAINER_COMMAND
        )
        if request.is_json:
            json_msg = request.get_json(force=True)
            request_id = str(uuid.uuid4())
            orchestrator_command = {
                "type": Protocol.MSG_REQUEST,
                "requester": Protocol.ACTOR_TRAINING_SERVICE,
                "command": cmd,
                "request_id": request_id,
                "content": json_msg,
            }
            self.queue.send(orchestrator_command)
            return {"code": 0, "message": msg, "request_id": request_id}
        return {"code": 1, "message": "request must enclose a json object"}, 400


def required_auth():
    # verify correct user ==========
    token = request.headers.get("Authorization")
    if not token:
        return {"status": "Required session id!"}

    secret_token = token.split("Bearer ")[1]

    if len(list(auth_collection.find({"session_id": secret_token}))) < 1:
        return {"status": "Your session is expired. Please login again!"}

    return None


class Queue(object):
    def __init__(self, _config):
        self.amqp_queue_out = AmqpConnector(AMQPConnectorConfig(**_config['amqp_out']['amqp_connector']['conf']))

    def send(self, msg):
        self.amqp_queue_out.send_report(json.dumps(msg))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arguments for Management Service")
    parser.add_argument(
        "--conf", help="configuration file", default="cloud/services/conf/config.json"
    )
    args = parser.parse_args()
    with open(args.conf) as f:
        config = json.loads(f.read())

    queue = Queue(config["orchestrator"])

    mongo_client = pymongo.MongoClient(config["mongo_url"])
    db = (
        mongo_client.get_database(config["authentication"]["db_name"])
        if config["authentication"]["db_name"] in mongo_client.list_database_names()
        else mongo_client[config["authentication"]["db_name"]]
    )
    auth_collection = db[config["authentication"]["db_col"]]

    # queue to get health info from edge and federated server
    ResourceHealthReport(config)

    # two main services of eadran: data service, training service and control edges
    api.add_resource(EADRANService, "/service/<string:op>", resource_class_args=(queue,),
                     resource_class_kwargs=config)
    api.add_resource(
        ControlEdge, "/control/edge/<string:op>", resource_class_args=(queue,)
    )
    # service to check health of edge and federated server
    api.add_resource(ComputingResourceHealth, "/health", resource_class_kwargs=config)

    # management service
    api.add_resource(EdgeMgt, "/mgt/edge", resource_class_kwargs=config)
    api.add_resource(MetadataMgt, "/mgt/metadata", resource_class_kwargs=config)
    api.add_resource(ModelMgt, "/mgt/model", resource_class_kwargs=config)
    api.add_resource(UserMgt, "/mgt/user", resource_class_kwargs=config)
    api.add_resource(Authentication, "/auth", resource_class_kwargs=config)

    # run service
    app.run(host="0.0.0.0", debug=True, port=Service.SERVICE_PORT)
