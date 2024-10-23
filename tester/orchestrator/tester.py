# import json
#
# from cloud.orchestrator.commons.modules import Config4Edge
# from cloud.orchestrator.commons.pipeline import Pipeline
# from cloud.orchestrator.orchestrator import Orchestrator
#
# with open("../../cloud/orchestrator/conf/config.json") as config_file:
#     conf = json.load(config_file)
#
# with open("../../cloud/orchestrator/conf/image4edge.json") as config_file:
#     conf4e = json.load(config_file)
#
#
# with open("req.json") as train_request_file:
#     params = json.load(train_request_file)
#
# orchestrator = Orchestrator(conf, conf4e)
# orchestrator.start()
#
# pipeline = Pipeline(task_list=[Config4Edge(orchestrator)],
#                     params=params)
# pipeline.exec()
#

import pandas as pd
import numpy as np

df = pd.read_csv("../../apps/water_leak/data_preprocessing/preprocessData/scenario_2/split_8.csv")
# null_count = df.isnull().sum().sum()
# total_count = np.prod(df.shape)
#
# print(np.around(1 - null_count / total_count, 4))
print(df['target'].value_counts())
y = df['target']
values, counts = np.unique(y, return_counts=True)
max_count = max(counts)
# print(max_count)
counts = counts/max_count
# print(counts)
mean_count = counts.mean()
# print(mean_count)
counts = counts - mean_count
# print(counts)
print(np.around(np.absolute(counts).sum()/len(counts),4))


