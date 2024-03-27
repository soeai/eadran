import json
import os

import pymongo
import werkzeug
from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename

from cloud.commons.default import ServiceConfig
from cloud.storage_service.storage import MinioStorage
from helpers.custom_logger import CustomLogger

app = Flask(__name__)
api = Api(app)

logger = CustomLogger().get_logger()


class StorageService(Resource):
    def __init__(self, **kwargs) -> None:
        self.mongo_client = pymongo.MongoClient(kwargs['mongo_url'])
        self.db = self.mongo_client[kwargs["storage"]["db_name"]]
        self.collection = self.db[kwargs["storage"]["db_col"]]
        # create a MinioStorage object here
        self.storage = MinioStorage(kwargs["minio_conf"])

    def get(self, storage_id):
        # check if it exists in database
        result = list(self.collection.find({"_id":storage_id}))
        if len(result) < 0:
            return jsonify({"status": False}), 404

        return Response(self.storage.get(storage_id),
                        mimetype=result[0]['mimetype'],
                        headers={"Content-Disposition":
                                    "attachment;filename={}".format(result[0]['filename'])})

    def post(self):
        if 'file' not in request.files:
            return jsonify({'status': False}), 401

        file = request.files.get("file")
        if file:
            msg = {"filename": secure_filename(file.filename),
                   "mimetype":file.mimetype}
            # put info into database
            storage_id = self.collection.insert_one(msg).inserted_id
            # put file to storage
            self.storage.put(storage_id, file)

            return jsonify({'storage_id': storage_id})

    # def put(self,storage_id):
    #     # args = parser.parse_args()
    #     # get param from args here
    #     if 'file' not in request.files:
    #         return jsonify({'status': False}), 401
    #
    #     filename = secure_filename(storage_id)
    #
    #     # if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], filename)):
    #     #     return jsonify({"status": False}), 404
    #
    #     file = request.files.get("file")
    #     if file:
    #         self.storage.put(storage_id, file)
    #         # file.save(os.path.join(confs['STORAGE_FOLDER'], filename))
    #         return jsonify({'status': True})

    def delete(self, storage_id):
        # # args = parser.parse_args()
        # # get param from args here
        # filename = secure_filename(storage_id)
        # if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], filename)):
        #     return jsonify({"status": False}), 404
        self.collection.delete_one({"_id":storage_id})

        self.storage.delete(storage_id)
        return jsonify({'status': True})


if __name__ == '__main__':
    # init_env_variables()
    parser = reqparse.RequestParser()
    # Look only in the POST body
    # parser.add_argument('data', type=list, location='json')
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    parser.add_argument('--conf', help='configuration file', default="./conf/config.json")

    args = parser.parse_args()
    with open(args.conf) as f:
        config = json.loads(f.read())

    api.add_resource(StorageService, '/storage',resource_class_kwargs=config)

    app.run(debug=True, port=ServiceConfig.STORAGE_SERVICE_PORT)