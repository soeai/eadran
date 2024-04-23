from cloud.orchestrator.commons.modules import StartFedServer, GenerateConfiguration
from cloud.orchestrator.commons.pipeline import Pipeline
from cloud.orchestrator.orchestrator import Orchestrator
import argparse
import json
import uuid

from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml.connector.amqp_connector import Amqp_Connector
import qoa4ml.qoaUtils as utils
from threading import Thread
from cloud.commons.default import ServiceConfig
import logging
import requests

with open("../../cloud/orchestrator/conf/config.json") as config_file:
    conf = json.load(config_file)

with open("train_request.json") as train_request_file:
    params = json.load(train_request_file)

orchestrator = Orchestrator("../../cloud/orchestrator/conf/config.json")
orchestrator.start()

pipeline = Pipeline(task_list=[GenerateConfiguration(orchestrator)],
                    params=params)
pipeline.exec()
