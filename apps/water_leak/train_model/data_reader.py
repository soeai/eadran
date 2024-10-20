import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np


def read_data(data_file):
    df = pd.read_csv(data_file)
    y = df['target']
    X = df.drop(['target', 'time'], axis=1)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    np.nan_to_num(X, copy=False)
    X_test, y_test = None, None
    return X, y, X_test, y_test