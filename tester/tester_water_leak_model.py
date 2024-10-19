from apps.water_leak.train_model.water_leak_model_tf import *
from apps.water_leak.train_model.data_reader import *
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import numpy as np
import time
# "https://raw.githubusercontent.com/dungcao/eadran-data/refs/heads/main/data-waterLeak/scenario_1/ALL.csv"
X,y = read_data("https://raw.githubusercontent.com/dungcao/eadran-data/refs/heads/main/data-waterLeak/scenario_1/ALL_1s.csv")
# X,y = read_data("../apps/water_leak/data_preprocessing/preprocessData/scenario_1/ALL_1s.csv")
# print(np.isnan(X).sum())
# y = y.reshape()
# create_model((32, 36))
print(X.shape)
print(y.value_counts())
# model.summary()
# print(y.shape)
# X.fillna(0, inplace=True)
# scaler = MinMaxScaler()
# X_normalized = scaler.fit_transform(X)
# np.nan_to_num(X_normalized, copy=False)
# # print(X_normalized)
# s = time.time()
# his = fit(X_normalized, y, 10)
# e = time.time()
# print(his, " -- time: ", e-s)
