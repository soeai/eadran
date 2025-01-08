# Infrastructure Setup Guide

## Requirements

### Devices

- **All-services**: Ubuntu
  - **Prerequisites**:
    - Docker installed on all devices in the framework
    - MongoDB on 1 device
    - MinIO on 1 device
    - Cloud setup with 1 or 2 clouds (1 for service and 1 for orchestrator)
      - `requirement.txt`
      - Services as shown on the right side in Figure 1
        - `config.json` (edit IP for MinIO and MongoDB)
        - `storage_config.json` (edit IP for MinIO and MongoDB)
        - `requirement.txt`
      - Orchestrator (can be on the same or another device as shown in Figure 1)
        - `config.json`
        - `image4edge.json` (environment config for Docker, e.g., TensorFlow, PyTorch, or scikit-learn)
        - `requirement.txt`
    - Edge devices (multiple edge nodes as shown in Figure 1)
      - `config.json`
      - `requirement.txt`
      - Data extraction module from MC
        - MC sites
      - Orchestration (nothing special, can be ignored)
    - Fed_server (cloud node as shown in Figure 1)
      - `config.json`
      - `queue2kafka.json` (for training and real-time monitoring with Grafana)
      - Orchestration (nothing special, can be ignored)
        - `requirement.txt`
      - `qot_eval`
        - `rabbitMQ-2-kafka` for real-time visualization

## Flow Logic

1. Ensure Docker is installed on all devices.
2. Set up `requirement.txt` for all devices.
3. Edit all necessary configuration files.

### Using Docker

- After building Docker images:
  ```bash
  ./start_dockers_4_service.sh # cd eadran
  ```

### Without Docker Images

- If MongoDB, MinIO, and RabbitMQ are already running:
  ```bash
  ./start_all_service.sh # cd eadran
  ```

### Orchestrator

- Start the orchestrator:
  ```bash
  ./start_orchestrator.sh # cd eadran
  ```

### Fed_server

- Start the Fed_server:
  ```bash
  ./start_fedserver.sh # cd eadran
  ```

### Edge Devices

- Start edge devices with the configuration file:
  ```bash
  ./start_fededge.sh <file_config> # cd eadran
  ```

### for Market Consumers

- For example, with water_leak:
  - Define a directory as in `apps/water_leak`
  - Implement model training and data writing modules
  - MCs implement `apps/water_leak/water_leak_model_tf.py`
  - DPs implement `apps/water_leak/data_reader.py`
  - Upload both files to services in the cloud's service
    ```python
    post_parser.add_argument('file', type=werkzeug.datastructures.FileStorage, required=True, location='files')
    post_parser.add_argument('user', type=str, required=True, location='form')
    post_parser.add_argument('key', type=str, location='form')
    api.add_resource(StorageService, '/storage/obj', resource_class_kwargs=config) # POST parse -- recommend usage of Postman
    ```

### Training Request

- Include parameters:
  - Key from uploaded files, e.g., MC: `ttu_water_leak_model_tf_v1`, DP: `ttu_water_leak_data_reader_v1`
  - Start multiple requests for many edges to the services
    ```python
    api.add_resource(EADRANService, "/service/<string:op>", resource_class_args=(queue,),
                     resource_class_kwargs=config)
    ```

### Monitoring and Measurement

- Use another machine to start Kafka and Spark:
  ```bash
  # Start Kafka and Spark
  ```

### Cloud Configuration

- Edit `config/kafka_conf.json`:
  ```bash
  python kafka2influxdb.py # Push to InfluxDB
  ```

### Fed_server Configuration

- Edit `config/queue2kafka.json`:
  ```bash
  python rabbitmq2kakfka.py
  ```

### Cost Service

- Edit `eadran_cost_service/run_submit_spark`
- Edit cost formula if needed:
  ```bash
  ./run_submit_spark.sh
  ```

### Data Verification

- Check data from InfluxDB:
  ```bash
  # Verify calculated data
