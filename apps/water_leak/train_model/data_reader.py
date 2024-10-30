import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np


def read_data(train_data, validate_data=None):
    # both train and validate params have the structure as follows.
    # {
    #     "method": "",
    #     "location": "",
    #     "format": "",
    #     "params": ""
    # }
    file_path = train_data['location']
    df = None
    if train_data['format'] == 'csv':
        df = pd.read_csv(file_path)

    if df is not None:
        y = df['target']
        X = df.drop(['target', 'time'], axis=1)
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        np.nan_to_num(X, copy=False)
        X_test, y_test = None, None
        if validate_data is not None:
            try:
                df = pd.read_csv(validate_data['location'])
                y_test = df['target']
                X_test = df.drop(['target', 'time'], axis=1)
            except FileNotFoundError:
                print("cannot read validate data...")
        return X, y, X_test, y_test
    else:
        return None, None, None, None


def read_data_without_process(train_data, validate_data=None):
    # both train and validate params have the structure as follows.
    # {
    #     "method": "",
    #     "location": "",
    #     "format": "",
    #     "params": ""
    # }
    file_path = train_data['location']
    df = None
    if train_data['format'] == 'csv':
        df = pd.read_csv(file_path)

    if df is not None:
        y = df['target']
        X = df.drop(['target', 'time'], axis=1)
        X_test, y_test = None, None
        if validate_data is not None:
            try:
                df = pd.read_csv(validate_data['location'])
                y_test = df['target']
                X_test = df.drop(['target', 'time'], axis=1)
            except FileNotFoundError:
                print("cannot read validate data...")
        return X, y, X_test, y_test
    else:
        return None, None, None, None


def read_test_data(train_data, validate_data=None):
    # both train and validate params have the structure as follows.
    # {
    #     "method": "",
    #     "location": "",
    #     "format": "",
    #     "params": ""
    # }
    file_path = train_data['location']
    df = None
    if train_data['format'] == 'csv':
        df = pd.read_csv(file_path)

    if df is not None:
        y = df['target']
        X = df.drop(['target', 'time'], axis=1)
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        np.nan_to_num(X, copy=False)
        return None, None, X, y
    else:
        return None, None, None, None
