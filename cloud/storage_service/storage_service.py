import werkzeug
from flask import Flask, jsonify, request, send_from_directory
import os, time
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
from cloud.commons.default import ServiceConfig
from cloud.storage_service.storage import MinioStorage
from helpers.custom_logger import CustomLogger
from flask_restful import reqparse
import json

app = Flask(__name__)
api = Api(app)

logger = CustomLogger().get_logger()

with open("conf/config.json") as f:
    confs = json.load(f)


class StorageService(Resource):
    def __init__(self):
        # create a MinioStorage object here
        self.storage = MinioStorage(confs)

    def get(self, file_id):
        if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], file_id)):
            return jsonify({"status": False}), 404
        return self.storage.get(file_id)
        # return send_from_directory(confs['STORAGE_FOLDER'], file_id, as_attachment=True)
        # return jsonify({'Working': True})

    def post(self):
        if 'file' not in request.files:
            return jsonify({'status': False}), 401

        file = request.files.get("file")
        if file:
            filename = secure_filename(file.filename)
            # put file to storage
            self.storage.put(filename, file)

            # file.save(os.path.join(confs['STORAGE_FOLDER'], filename))
            return jsonify({'status': True})

    def put(self,file_id):
        # args = parser.parse_args()
        # get param from args here
        if 'file' not in request.files:
            return jsonify({'status': False}), 401

        filename = secure_filename(file_id)

        if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], filename)):
            return jsonify({"status": False}), 404

        file = request.files.get("file")
        if file:
            self.storage.put(filename, file)
            # file.save(os.path.join(confs['STORAGE_FOLDER'], filename))
            return jsonify({'status': True})

    def delete(self, file_id):
        # args = parser.parse_args()
        # get param from args here
        filename = secure_filename(file_id)
        if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], filename)):
            return jsonify({"status": False}), 404

        # os.remove(os.path.join(confs['STORAGE_FOLDER'], filename))
        self.storage.delete(filename)
        return jsonify({'status': True})


api.add_resource(StorageService, '/storage')

if __name__ == '__main__': 
    # init_env_variables()
    parser = reqparse.RequestParser()
    # Look only in the POST body
    # parser.add_argument('data', type=list, location='json')
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    app.run(debug=True, port=ServiceConfig.STORAGE_SERVICE_PORT)