import logging
import subprocess
import json

# Orchestrator class
class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.url_storage_service = config.get("url_storage_service")
        self.eadran_qod_image_name = config.get("eadran_qod_image_name")

# QoDTest class
class QoDTest:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def exec(self, params):
        command = {
            "edge_id": params["edge_id"],
            "request_id": params["request_id"],
            "command": "docker",
            "params": "start",
            "docker": [
                {
                    "image": self.orchestrator.eadran_qod_image_name,
                    "options": {
                        "--name": f"data_qod_container_{params['consumer_id']}_{params['model_id']}",
                    },
                    "arguments": [
                        self.orchestrator.url_storage_service,
                        params["data_conf"]["reader_module"]["storage_ref_id"],
                    ],
                }
            ],
        }
        if params["data_conf"]["method"] == "local":
            fullpath = params["data_conf"]["location"]
            filename = fullpath.split("/")[-1]
            folder_path = fullpath[: fullpath.index(filename)]
            mount = f"type=bind,source={folder_path},target=/data/"
            command["docker"][0]["options"]["--mount"] = mount
        self.send_command(command)
        logging.info("Sent QoD evaluation command to edge.")

    def send_command(self, command):
        logging.info(f"Command sent: {json.dumps(command, indent=2)}")
        subprocess.run(["docker", "run", "--rm", "-v", "/path/to/data:/data", "qod_test"])

if __name__ == "__main__":
    orchestrator_config = {
        "eadran_qod_image_name": "qod_test",
        "url_storage_service": "http://192.168.80.194:8081"
    }
    orchestrator = Orchestrator(orchestrator_config)
    qod_test = QoDTest(orchestrator)
    params = {
        "edge_id": "edge001",
        "request_id": "req_001",
        "consumer_id": "dungcao",
        "model_id": "tensorflow001",
        "data_conf": {
            "method": "local",
            "location": "/path/to/data/fraudTrain_processed_SMOTE_1.csv",
            "reader_module": {
                "storage_ref_id": "665d497f52c81403417a6a4e"
            }
        }
    }
    qod_test.exec(params)