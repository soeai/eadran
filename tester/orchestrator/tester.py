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
from sklearn.preprocessing import StandardScaler

from cloud.orchestrator.build_docker.qod.evaluate import *

df = pd.read_csv("/Users/Storage/Research/EdgeML/eadran_water_leak/split_1_mice.csv")
# df = pd.read_csv("../../apps/water_leak/data_preprocessing/preprocessData/scenario_2/split_1.csv")

# null_count = df.isnull().sum().sum()
# total_count = np.prod(df.shape)
#
# print(np.around(1 - null_count / total_count, 4))
# print(df['target'].value_counts())
y = df['target']
X = df.drop(['target','time'], axis=1)
# print(X.max())
#
# df = pd.DataFrame(X)
# null_count = df.isnull().sum().sum()
# total_count = np.prod(df.shape)
#
# print(np.around(1 - null_count / total_count, 4))
#
# # print(completeness(X))
# values, counts = np.unique(y, return_counts=True)
# max_count = max(counts)
# # print(max_count)
# counts = counts/max_count
# # print(counts)
# mean_count = counts.mean()
# # print(mean_count)
# counts = counts - mean_count
# # print(counts)
# print(np.around(1 - np.absolute(counts).sum()/len(counts),4))

# X = df[np.isfinite(X).all(1)]

_com = completeness(X)
scaler = StandardScaler()
X = scaler.fit_transform(X)
# np.nan_to_num(X, copy=False)
# X = np.asarray(X,dtype=np.float32)
# print(type(X))
# print(X.isnull().sum())
# print("class_overlap: ", class_overlap(X, y))
# print("class_parity: ", class_parity(y))
# print("label_purity: ", label_purity(X, y))
qod_metrics = {"class_overlap": class_overlap(X, y),
               "class_parity": class_parity(y),
               # "label_purity": label_purity(X, y),
               "feature_correlation": feature_correlation(X),
               "feature_relevance": feature_relevance(X, y, 0.9),
               "completeness": _com}
#
print(qod_metrics)


