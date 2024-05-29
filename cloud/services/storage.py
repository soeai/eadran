import argparse
import json
import os
from datetime import datetime
import pymongo
import werkzeug
from flask_cors import CORS
import io
from minio.error import S3Error
from minio import Minio
from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from cloud.commons.default import Service

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r"/storage/*": {"origins": "*"}})
mongo_client = None


class MinioStorage:
    def __init__(self, conf, bucket_name='eadran'):
        self.bucket_name = bucket_name
        self.minioClient = Minio(conf['minio_server'],
                                 access_key=conf['minio_access'],
                                 secret_key=conf['minio_secret'],
                                 secure=False)
        if not self.minioClient.bucket_exists(bucket_name):
            self.minioClient.make_bucket(bucket_name, location='us-east-1')

    def get(self, key):
        try:
            data = self.minioClient.get_object(self.bucket_name, key)
            return data.read()
        except S3Error as err:
            print(err)
            return None

    def put(self, key, value):
        try:
            self.minioClient.put_object(self.bucket_name, key, io.BytesIO(value), len(value))
            return len(value)
        except S3Error as err:
            print(err)
            return None

    def delete(self, key):
        try:
            self.minioClient.remove_object(self.bucket_name, key)
            return key
        except S3Error as err:
            print(err)
        return None


class StorageService(Resource):
    def __init__(self, **kwargs) -> None:
        self.db = mongo_client.get_database(kwargs["storage"]["db_name"]) \
            if kwargs["storage"]["db_name"] in mongo_client.list_database_names() \
            else mongo_client[kwargs["storage"]["db_name"]]
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
                result = list(self.collection.find({"_id": ObjectId(storage_id)}))
                if len(result) < 0:
                    return jsonify({"message": "The \'{}\' object is not managed!".format(storage_id)}), 404

                return Response(self.storage.get(storage_id),
                                mimetype=result[0]['mimetype'],
                                headers={"Content-Disposition":
                                             "attachment;filename={}".format(result[0]['filename'])})
        return {"message": "missing query: id=???"}, 404

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

            return {'storage_id': storage_id}

    def delete(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                storage_id = query[1]

                if len(self.collection.find_one_and_delete({"_id": ObjectId(storage_id)})) < 0:
                    return jsonify({"status": False}), 401

                self.storage.delete(storage_id)
                return jsonify({'status': True})

        return jsonify({"message": "missing query: id=???"}), 404


class StorageInfo(Resource):
    def __init__(self, **kwargs) -> None:
        # self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = mongo_client.get_database(kwargs["storage"]["db_name"]) \
            if kwargs["storage"]["db_name"] in mongo_client.list_database_names() \
            else mongo_client[kwargs["storage"]["db_name"]]
        self.collection = self.db[kwargs["storage"]["db_col"]]

    def get(self):
        req_args = request.query_string.decode("utf-8").split("&")
        if len(req_args) > 0:
            # get param from args here
            query = req_args[0].split("=")
            if query[0] == 'id':
                user_id = query[1]
                # check if it exists in database
                result = list(self.collection.find({"owner": user_id}))
                # print(result)
                result = list(map(StorageInfo.obj2string, result))

                if len(result) < 0:
                    return jsonify({"message": "There is no object owned by \'{}\'".format(user_id)}), 201

                return jsonify({"objects": result})

        return jsonify({"message": "missing query: id=???"}), 404

    # utility function
    def obj2string(obj):
        obj['id'] = str(obj["_id"])
        obj.pop("_id")
        return obj


if __name__ == '__main__':
    # init_env_variables()
    post_parser = reqparse.RequestParser()
    # Look only in the POST body
    # parser.add_argument('data', type=list, location='json')
    post_parser.add_argument('file', type=werkzeug.datastructures.FileStorage, required=True, location='files')
    post_parser.add_argument('user', type=str, required=True, location='form')

    parser = argparse.ArgumentParser(description="Argument for Storage Service")
    parser.add_argument('--conf', help='configuration file', default="./conf/storage_config.json")

    args = parser.parse_args()
    with open(args.conf) as f:
        config = json.loads(f.read())

    mongo_client = pymongo.MongoClient(config['mongo_url'])
    api.add_resource(StorageService, '/storage/obj', resource_class_kwargs=config)
    api.add_resource(StorageInfo, '/storage/owner', resource_class_kwargs=config)

    app.run(host='0.0.0.0', debug=True, port=Service.STORAGE_PORT)
