import werkzeug
from flask import Flask, jsonify, request, send_from_directory
import os, time
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
from cloud.commons.default import ServiceConfig
from helpers.custom_logger import CustomLogger
from flask_restful import reqparse
import json

app = Flask(__name__)
api = Api(app)

logger = CustomLogger().get_logger()

# headers = {'content-type': 'application/json'}
# edge_service = "edge_service"
# edge_service_port= "8006"

with open("conf/config.json") as f:
    confs = json.load(f)

# app.config['UPLOAD_FOLDER'] = 'temp'

# def get_node_name():
#     node_name = os.environ.get('NODE_NAME')
#     if not node_name:
#         print("NODE_NAME is not defined")
#         node_name = "Empty"
#     return node_name
# def get_instance_id():
#     pod_id = os.environ.get('POD_ID')
#     if not pod_id:
#         print("POD_ID is not defined")
#         pod_id = "Empty"
#     return pod_id
#
# def init_env_variables():
#     edge_service = os.environ.get('EDGE_SERVICE')
#     edge_service_port = os.environ.get("EDGE_SERVICE_PORT")
#     if not edge_service:
#         logger.error("EDGE_SERVICE is not defined")
#         raise Exception("EDGE_SERVICE is not defined")
#     if not edge_service_port:
#         logger.error("EDGE_SERVICE_PORT is not defined")
#         raise Exception("EDGE_SERVICE_PORT is not defined")

# @app.route("/storage", methods = ['GET', 'POST'])
# def inference():
#
#     if request.method == 'GET':
#         logger.info("Received a a GET request!")
#         return Response('{"error":"use POST"}', status=200, mimetype='application/json')
#
#     elif request.method == 'POST':
#
#         # Handle request
#         content_type = request.headers.get('Content-Type')
#         if (content_type == 'application/json'):
#             jdata = request.json
#             edge_data = jdata['edge_data']
#             # To do: handel request
#
#         # 10 - EDGE RESOURCE MANAGEMENT
#         try:
#             for i in range(10):
#                 r = rq.post(url=f"http://{edge_service}:{edge_service_port}/edge", json=edge_data, headers=headers)
#                 errors += 1
#                 if (r!= None):
#                     break
#                 time.sleep(0.1)
#             logger.info(str(r.text))
#             edge_result = json.loads(r.text)
#             # Handle metadata result : json_data
#         except Exception as e:
#             errors += 1
#             logger.exception("Some Error occurred while querying edge resource: {}".format(e))
#
#
#         # To do: Send response
#         result = {'Success'}
#         return Response(result, status=200, mimetype='application/json')
#     else:
#         return Response('{"error":"method not allowed"}', status=405, mimetype='application/json')


class Storage(Resource):
    def get(self, file_id):
        if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], file_id)):
            return jsonify({"status": False}), 404

        return send_from_directory(confs['STORAGE_FOLDER'], file_id, as_attachment=True)
        # return jsonify({'Working': True})

    def post(self):
        if 'file' not in request.files:
            return jsonify({'status': False}), 401

        file = request.files.get("file")
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(confs['STORAGE_FOLDER'], filename))
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
            file.save(os.path.join(confs['STORAGE_FOLDER'], filename))
            return jsonify({'status': True})

    def delete(self, file_id):
        # args = parser.parse_args()
        # get param from args here
        filename = secure_filename(file_id)
        if not os.path.exists(os.path.join(confs['STORAGE_FOLDER'], filename)):
            return jsonify({"status": False}), 404

        os.remove(os.path.join(confs['STORAGE_FOLDER'], filename))
        return jsonify({'status': True})


api.add_resource(Storage, '/storage')

if __name__ == '__main__': 
    # init_env_variables()
    parser = reqparse.RequestParser()
    # Look only in the POST body
    # parser.add_argument('data', type=list, location='json')
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    app.run(debug=True, port=ServiceConfig.STORAGE_SERVICE_PORT)