from apps.water_leak.train_model.model_tf import *
from apps.water_leak.train_model.data_reader import *
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import numpy as np

X,y = read_data("https://raw.githubusercontent.com/dungcao/eadran-data/refs/heads/main/data-waterLeak/scenario_1/ALL.csv")
# print(np.isnan(X).sum())
# y = y.reshape()
# create_model((32, 36))

# model.summary()
# print(y.shape)
scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)
his = fit(X_normalized, y, 10)
print(his)
print(X_normalized)