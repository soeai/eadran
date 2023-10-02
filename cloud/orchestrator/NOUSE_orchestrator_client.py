from qoa4ml.collector.amqp_collector import Amqp_Collector
import qoa4ml.utils as utils
import argparse, json, docker
import traceback,sys
from threading import Thread

"""
Example Command Message
{
    "command": "start",
    "config":[
        {
            "image": "repo:docker_image_rabbitmq",
            "container_name": "rabbit_container_01",
            "detach": "True",
            "binding_port":{
                "5672/tcp":"5672",
                "5671/tcp":"5671",
                "25672/tcp":"25672",
                "15672/tcp":"15672"}
        },
        {
            "image": "repo:docker_image_fedserver",
            "container_name": "fedserver_container_01",
            "detach": "True",
            "binding_port":{
                "1111/tcp":"2222",
                "3333/tcp":"4444"}
        }
    ]
}

{
    "command": "stop",
    "containers":["rabbit_container_01","fedserver_container_01"]
}
"""

class OrchestratorClient(object):
    def __init__(self, config):
        connetor_conf = utils.load_config(config)
        self.connector = Amqp_Collector(connetor_conf['amqp_collector']['conf'])
        self.docker_client = docker.from_env()
        self.containers = {}

    
    def start(self):
        self.connector.start()

    def start_container(self, config):
        try:
            self.containers[config["container_name"]] = self.docker_client.containers.run(image=config["image"],
                                              detach=bool(config["detach"]),
                                              name=config["container_name"],
                                              ports=config["binding_port"])
        except Exception as e:
            print("[ERROR] - Error {} while estimating contribution: {}".format(type(e),e.__traceback__))
            traceback.print_exception(*sys.exc_info())
    
    def stop_container(self, container_name):
        try:
            self.containers[container_name].stop()
            self.connector.pop(container_name,None)
        except Exception as e:
            print("[ERROR] - Error {} while estimating contribution: {}".format(type(e),e.__traceback__))
            traceback.print_exception(*sys.exc_info())


    def message_processing(self, ch, method, props, body):
        mess = json.loads(str(body.decode("utf-8")))
        if mess["command"] == "start":
            for config in mess["config"]:
                self.start_container(config)
        if mess["command"] == "start":
            for container in mess["containers"]:
                self.start_container(container)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Orchestrator Client')
    parser.add_argument('--conf', type=str, default='conf/orchestrator_client_config.json')
    args = parser.parse_args()

    orchestrator = OrchestratorClient(args.conf)
    orchestrator.start()