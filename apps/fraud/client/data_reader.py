# from typing import Tuple, Union, List
# import numpy as np
import pandas as pd
# from sklearn.linear_model import LogisticRegression
#
# XY = Tuple[np.ndarray, np.ndarray]
# LogRegParams = Union[XY, Tuple[np.ndarray]]
#
#
# def get_model_parameters(model):
#     """Returns the paramters of a sklearn LogisticRegression model"""
#     if model.fit_intercept:
#         params = ([model.coef_, model.intercept_])
#     else:
#         params = ([model.coef_])
#     return params
#
#
# def set_model_params(
#     model: LogisticRegression, params: LogRegParams
# ) -> LogisticRegression:
#     """Sets the parameters of a sklean LogisticRegression model"""
#     model.coef_ = params[0]
#     if model.fit_intercept:
#         model.intercept_ = params[1]
#     return model
#
#
# def set_initial_params(model: LogisticRegression, n_features=22, n_classes=2):
#     """
#     Sets initial parameters as zeros
#     """
#     model.classes_ = np.array([i for i in range(n_classes)])
#
#     model.coef_ = np.zeros((n_classes, n_features))
#     if model.fit_intercept:
#         model.intercept_ = np.zeros((n_classes,))


def read_data(data_file):
    df = pd.read_csv(data_file)
    y = df['is_fraud']
    X = df.drop('is_fraud', axis=1).to_numpy()
    return X, y
