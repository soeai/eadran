import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np


def read_data(data_file, validate_data=None):
    df = pd.read_csv(data_file)
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


def read_data_without_process(data_file, validate_data=None):
    df = pd.read_csv(data_file)
    y = df['target']
    X = df.drop(['target', 'time'], axis=1)
    # scaler = StandardScaler()
    # X = scaler.fit_transform(X)
    # np.nan_to_num(X, copy=False)
    X_test, y_test = None, None
    if validate_data is not None:
        try:
            df = pd.read_csv(validate_data['location'])
            y_test = df['target']
            X_test = df.drop(['target', 'time'], axis=1)
        except FileNotFoundError:
            print("cannot read validate data...")
    return X, y, X_test, y_test


def read_test_data(data_file, validate_data=None):
    # df = pd.read_csv(data_file)
    # y = df['target']
    # X = df.drop(['target', 'time'], axis=1)
    scaler = StandardScaler()
    # X = scaler.fit_transform(X)
    # np.nan_to_num(X, copy=False)
    X_test, y_test = None, None
    if validate_data is not None:
        try:
            df = pd.read_csv(validate_data['location'])
            y_test = df['target']
            X_test = df.drop(['target', 'time'], axis=1)
            X_test = scaler.fit_transform(X_test)
            np.nan_to_num(X_test, copy=False)
        except FileNotFoundError:
            print("cannot read validate data...")
    return None, None, X_test, y_test
