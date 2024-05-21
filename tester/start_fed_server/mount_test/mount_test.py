import docker

def main():
    client = docker.from_env()

    # container
    image = "test"
    name = "container_test_06"
    mount_type = "bind"
    host_path = "/Users/vuducduy/Documents/TTU/FALL2023/CS322"
    container_path = "/data"

    try:
        # run container with mount
        container = client.containers.run(
            image,
            name=name,
            volumes={host_path: {'bind': container_path, 'mode': 'rw'}},
            ports={'5672/tcp': 5672},
            detach=True,
            auto_remove=True
        )
        print(f"Container {name} started successfully.")

        # read and print file
        exec_result = container.exec_run(f"ls -l {container_path}")
        print(f"Contents of {container_path}:")
        print(exec_result.output.decode())

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
