import subprocess
import sys
import traceback
import docker

try:
    # Install required packages
    # subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Now import the required modules

    config = {
        "image": "rabbitmq:3",
        "options": {
            "--name": "rabbit_container_01",
            "-p": ["5672:5672/tcp"],
        }
    }
    res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + config["options"]["--name"]], capture_output=True)
    if res.returncode == 0 and config["options"]["--name"] in str(res.stdout):
        subprocess.run(["docker", "stop", config["options"]["--name"]])
        subprocess.run(["docker", "rm", config["options"]["--name"]])

    command = ["docker", "run", "-d"]
    for (k, v) in config["options"].items():
        if v is not None and len(v) > 0:
            if k == "-p":
                for port in v:
                    command.extend(["-p", port])
            else:
                command.extend([k, v])
        else:
            command.append(k)
    command.append(config["image"])

    res = subprocess.run(command, capture_output=True)
    print(res)
except Exception as e:
    print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e))
    traceback.print_exc()
