from cloud.orchestrator.commons.modules import FedServerContainer, Config4Edge
from cloud.orchestrator.commons.pipeline import Pipeline
from cloud.orchestrator.orchestrator import Orchestrator
import json

with open("../../cloud/orchestrator/conf/config.json") as config_file:
    conf = json.load(config_file)

with open("train_request.json") as train_request_file:
    params = json.load(train_request_file)

orchestrator = Orchestrator("../../cloud/orchestrator/conf/config.json")
orchestrator.start()

pipeline = Pipeline(task_list=[Config4Edge(orchestrator)],
                    params=params)
pipeline.exec()
