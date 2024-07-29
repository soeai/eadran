from typing import Optional
import docker
import asyncio
import warnings

warnings.filterwarnings('ignore')

async def check_docker_running(container_name: str) -> Optional[bool]:
    """Verify the status of a container by its name

    :param container_name: the name of the container
    :return: boolean or None
    """
    RUNNING = "running"
    # Connect to Docker using the default socket or the configuration
    # in your environment
    docker_client = docker.from_env()
    await asyncio.sleep(2)
    try:
        container = docker_client.containers.get(container_name)
        container_state = container.attrs["State"]
        return container_state["Status"] == RUNNING
    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")
        return False
    except docker.errors.APIError as e:
        print(f"Error communicating with Docker API: {e}")
        return False
    finally:
        docker_client.close()


if __name__ == "__main__":
    container_name = "airflow_docker-redis-1"
    result = asyncio.run(check_docker_running(container_name))
    print(result)
