class Service:
    SERVICE_PORT = 8080
    STORAGE_PORT = 8081


class Protocol:
    TRAIN_MODEL_COMMAND = "train_model"
    DATA_EXTRACTION_COMMAND = "data_extraction"
    DATA_QOD_COMMAND = "data_qod_evaluation"
    START_CONTAINER_COMMAND = "start_container"
    STOP_CONTAINER_COMMAND = "stop_container"
    MSG_REQUEST = "request"
    MSG_RESPONSE = "response"
    ACTOR_TRAINING_SERVICE = "training_ws"
    ACTOR_DATA_SERVICE = "data_ws"
    ACTOR_ORCHESTRATOR = "orchestrator"
    DOCKER_COMMAND = "docker"
    QOT_COLLECTOR_COMMAND = "start_qot_collector"
