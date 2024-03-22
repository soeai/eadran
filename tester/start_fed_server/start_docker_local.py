import subprocess
import sys
import traceback
import docker

try:
    config = {
            "image": "rabbitmq:3",
            "container_name": "fed_rabbit_container_01",
            "detach": "True",
            "binding_port": {
                "5672/tcp": "5672",
                "5671/tcp": "5671",
                "25672/tcp": "25672",
                "15672/tcp": "15672"
            }
        }
    # docker_client = docker.from_env()
    # docker_client.containers.run(image=config["image"],
    #                               detach=bool(config["detach"]),
    #                               name=config["container_name"],
    #                               ports=config["binding_port"])
    # res = docker_client.containers.run("ubuntu", "echo hello world")
    # print("Running", res)
    subprocess.run(["docker", "run -d --hostname my-rabbit --name some-rabbit rabbitmq:3"], capture_output=True)
except Exception as e:
    print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
    traceback.print_exception(*sys.exc_info())