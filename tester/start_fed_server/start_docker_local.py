import json
import subprocess
import traceback

try:
    # Install required packages
    # subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Now import the required modules

    request_file = open('request.json')
    config_data = json.load(request_file)
    # Extract necessary information
    image_name = config_data["config"]["image"]
    container_name = config_data["config"]["container_name"]
    binding_ports = [f"{v}:{k}" for k, v in config_data["config"]["binding_port"].items()]

    res = subprocess.run(["docker", "ps", "-a", "--filter", "name=" + container_name], capture_output=True)
    if res.returncode == 0 and container_name in str(res.stdout):
        subprocess.run(["docker", "stop", container_name])
        subprocess.run(["docker", "rm", container_name])

    # Assemble the docker run command
    docker_run_command = ["docker", "run", "-d", "--name", container_name]
    docker_run_command += ["-p"] + binding_ports
    docker_run_command += [image_name]

    res = subprocess.run(docker_run_command, capture_output=True)
    print(res)
except Exception as e:
    print("[ERROR] - Error {} while estimating contribution: {}".format(type(e), e))
    traceback.print_exc()
