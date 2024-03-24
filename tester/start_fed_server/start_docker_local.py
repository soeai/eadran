import subprocess
import sys
import traceback
import docker

try:
    config = {
                "image": "rabbitmq:3",
                "options":{
                      "--name": "rabbit_container_01",
                      "-p": ["5672:5672/tcp"],
                          }
            }
    res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + config["options"]["--name"]], capture_output=True)
    if res.returncode == 0 and str(res.stdout).find(config["options"]["--name"]) >= 0:
        subprocess.run(["docker", "stop", config["options"]["--name"]])
        subprocess.run(["docker", "remove", config["options"]["--name"]])

        command = ["docker", "run", "-d"]
        for (k, v) in config["options"].items():
            if v is not None and len(v) > 0:
                if k == "-p":
                    for port in v:
                        command.extend(["-p", port])
                elif k != "-d":
                    command.extend([k, v])
            else:
                command.append(k)
        command.append(config["image"])
    # print(command)
    # docker_client = docker.from_env()
    # docker_client.containers.run(image=config["image"],
    #                               detach=bool(config["detach"]),
    #                               name=config["container_name"],
    #                               ports=config["binding_port"])
    # res = docker_client.containers.run("ubuntu", "echo hello world")
    # print("Running", res)
    # res = subprocess.run(["docker", "run", "-d", "--name","some-rabbit","-p","5672:5672","rabbitmq:3"], capture_output=True)
    # res = subprocess.run(["docker", "remove", config["options"]["--name"]], capture_output=True)
    # res = subprocess.run(["docker", "ps", "-a", "--filter", "name=some-rabbit"],capture_output=True)
    res = subprocess.run(command, capture_output=True)
    print(res)
except Exception as e:
    print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e.__traceback__))
    traceback.print_exception(*sys.exc_info())