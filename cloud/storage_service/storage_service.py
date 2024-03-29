import argparse
import json
import os
from datetime import datetime
import pymongo
import werkzeug

from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from cloud.commons.default import ServiceConfig
from cloud.storage_service.storage import MinioStorage
from helpers.custom_logger import CustomLogger

app = Flask(__name__)
api = Api(app)

logger = CustomLogger().get_logger()


class StorageService(Resource):
    def __init__(self, **kwargs) -> None:
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["storage"]["db_name"]]) \
            if self.mongo_client[kwargs["storage"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["storage"]["db_name"]]
        self.collection = self.db[kwargs["storage"]["db_col"]]
        # create a MinioStorage object here
        self.storage = MinioStorage(kwargs["minio_conf"])

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                storage_id = query[1]
                # check if it exists in database
                result = list(self.collection.find({"_id":ObjectId(storage_id)}))
                if len(result) < 0:
                    return jsonify({"message": "The \'{}\' object is not managed!".format(storage_id)}), 404

                return Response(self.storage.get(storage_id),
                                mimetype=result[0]['mimetype'],
                                headers={"Content-Disposition":
                                        "attachment;filename={}".format(result[0]['filename'])})
        return jsonify({"message":"missing query: id=???"}), 404

    def post(self):
        req_params = post_parser.parse_args()
        file = req_params.file
        if file:
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            msg = {"filename": secure_filename(file.filename),
                   "mimetype": file.mimetype,
                   "owner": req_params.user,
                   "create_at": dt_string}
            # put info into database
            storage_id = str(self.collection.insert_one(msg).inserted_id)
            # put file to storage
            data = file.stream.read()
            self.storage.put(storage_id, data)

            return jsonify({'storage_id': storage_id})

    def delete(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                storage_id = query[1]

                if len(self.collection.find_one_and_delete({"_id":ObjectId(storage_id)})) < 0:
                    return jsonify({"status": False}), 401

                self.storage.delete(storage_id)
                return jsonify({'status': True})

        return jsonify({"message":"missing query: id=???"}), 404


class StorageInfo(Resource):
    def __init__(self, **kwargs) -> None:
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client.get_database(self.mongo_client[kwargs["storage"]["db_name"]]) \
            if self.mongo_client[kwargs["storage"]["db_name"]] in self.mongo_client.list_database_names() \
            else self.mongo_client[kwargs["storage"]["db_name"]]
        self.collection = self.db[kwargs["storage"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                user_id = query[1]
                # check if it exists in database
                result = list(self.collection.find({"owner":user_id}))
                # print(result)
                result = list(map(StorageInfo.obj2string, result))

                if len(result) < 0:
                    return jsonify({"message": "There is no object owned by \'{}\'".format(user_id)}), 201

                return jsonify({"objects": result})

        return jsonify({"message": "missing query: id=???"}), 404

    # utility function
    def obj2string(obj):
        obj['_id'] = str(obj["_id"])
        return obj


if __name__ == '__main__':
    # init_env_variables()
    post_parser = reqparse.RequestParser()
    # Look only in the POST body
    # parser.add_argument('data', type=list, location='json')
    post_parser.add_argument('file', type=werkzeug.datastructures.FileStorage, required=True, location='files')
    post_parser.add_argument('user', type=str, required=True, location='form')

    parser = argparse.ArgumentParser(description="Argument for Storage Service")
    parser.add_argument('--conf', help='configuration file', default="./conf/config.json")

    args = parser.parse_args()
    with open(args.conf) as f:
        config = json.loads(f.read())

    api.add_resource(StorageService, '/storage/obj',resource_class_kwargs=config)
    api.add_resource(StorageInfo, '/storage/owner', resource_class_kwargs=config)

    app.run(debug=True, port=ServiceConfig.STORAGE_SERVICE_PORT)