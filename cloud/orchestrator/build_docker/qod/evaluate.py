'''
We assume that the data for training is available that can be accessed through a uri
note that other tasks have been done to prepare such a data for the training task
'''
import argparse
import logging
from urllib.request import urlretrieve

import numpy as np
import pandas as pd
import qoa4ml.utils.qoa_utils as utils
import requests
from cleanlab.filter import find_label_issues
from imblearn.under_sampling import TomekLinks
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(level=logging.INFO)


# from imblearn.over_sampling import SMOTE

# def tomek_links(X,y):
#     tomek_links = []
#     for i in range(len(X)):
#         for j in range(i+1, len(X)):
#             if y[i] != y[j]:  # Check if they have different labels
#                 distance_ij = np.linalg.norm(X[i] - X[j])  # distance between x[i] and x[j]
#                 is_tomek_link = True
#                 for k in range(len(X)):
#                     if y[i] != y[k] and np.linalg.norm(X[i] - X[k]) < distance_ij:
#                         is_tomek_link = False
#                         break
#                     if y[j] != y[k] and np.linalg.norm(X[j] - X[k]) < distance_ij:
#                         is_tomek_link = False
#                         break
#                 if is_tomek_link:
#                     tomek_links.append((i, j))
#     return tomek_links


def predict_prob(X, y):
    rf = RandomForestClassifier()
    size = len(y)
    idx = np.arange(size)
    np.random.shuffle(idx)

    step = size // 5
    start = 0
    end = step
    repeat = size // step
    probs = []
    for i in range(repeat):
        if i == repeat - 1:
            end = size + 1
        idx_val = idx[start:end]
        X_val = X[idx_val]
        idx_train = np.concatenate([idx[:start], idx[end:]])
        y_train = y[idx_train]
        X_train = X[idx_train]
        rf.fit(X_train, y_train)
        probs.append(rf.predict_proba(X_val))
        start = end
        end += step
    return np.concatenate(probs, axis=0)


def class_overlap(x, y, classify=True):
    if classify:
        tkl = TomekLinks()
        _, ry = tkl.fit_resample(x, y)
        return len(ry) / len(y)
    else:
        return 1


def class_parity(y):
    values, counts = np.unique(y, return_counts=True)
    max_count = max(counts)
    counts = counts / max_count
    mean_count = counts.mean()
    counts = counts - mean_count
    return np.around(np.absolute(counts).sum() / len(counts), 4)


def feature_correlation(X):
    """
    Calculate the QoD^D_FC metric for a given dataframe.

    Args:
    - dataframe (pd.DataFrame): The input data.

    Returns:
    - float: The QoD^D_FC value.
    """
    # Drop non-numeric columns
    df = pd.DataFrame(X)
    df = df.select_dtypes(include=[np.number])

    correlations = df.corr().abs().unstack().sort_values(kind="quicksort", ascending=False)
    # Exclude self correlations
    correlations = correlations[correlations < 1]

    N = len(df.columns)
    # Adjusted denominator based on unique pairs of features
    adjusted_denominator = N * (N - 1) / 2

    # Compute the metric
    return np.around(1 - correlations.sum() / adjusted_denominator, 4)


def feature_relevance(X, y, alpha=0.5):
    """
    Calculate the QoD^D_FR metric for a given dataframe and label column.

    Args:
    - dataframe (pd.DataFrame): The input data.
    - label_column (str): The column name of the label.
    - alpha (float): The alpha parameter.
    - beta (float): The beta parameter.

    Returns:
    - float: The QoD^D_FR value.
    """
    # For simplicity, we'll use feature importance_scores from a decision tree

    model = RandomForestClassifier()
    model.fit(X, y)
    importance_scores = model.feature_importances_
    m = min(3, X.shape[1])
    beta = 1 - alpha
    return np.around(alpha * (1 - np.var(importance_scores)) + beta * np.mean(sorted(importance_scores)[-m:]), 4)


def completeness(X):
    """
    Calculate the QoD^D_Com metric for a given dataframe.

    Args:
    - dataframe (pd.DataFrame): The input data.

    Returns:
    - float: The QoD^D_Com value.
    """
    df = pd.DataFrame(X)
    null_count = df.isnull().sum().sum()
    total_count = np.prod(df.shape)

    return np.around(1 - null_count / total_count, 4)


def label_purity(X, y):
    """
        Calculate the label purity metric for a given set of data points, true labels, and predicted probabilities.

        Args:
        - X (array-like): The input data points.
        - y (array-like): The true labels of the data points.

        Returns:
        - float: The label purity value, computed as QoD_lp.
        """
    # Using is_tomek_link from imbalanced-learn
    tl = TomekLinks()
    _, y_resampled = tl.fit_resample(X, y)

    # Get indices of Tomek links
    tomek_indices = tl.sample_indices_
    pred_probs = predict_prob(X, y)
    # Using find_label_issues from cleanlab
    label_issue_indices = find_label_issues(
        labels=y,
        pred_probs=pred_probs,
        return_indices_ranked_by='self_confidence'
    )

    intersection = len(set(tomek_indices) & set(label_issue_indices))

    # Compute the label purity as per the formula
    return np.around(1 - (intersection / len(y)), 4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="QoD Evaluation Plugin")
    parser.add_argument('--sessionid', help='The request Id from orchestrator')
    parser.add_argument('--conf', help='Client config file')
    args = parser.parse_args()

    client_conf = utils.load_config("/conf/" + args.conf)
    logging.info(client_conf)

    url_service = client_conf['storage_service'] + "/storage/obj?key="

    # download code of DPs to read data
    urlretrieve(url_service + client_conf['data_conf']['reader_module']['storage_ref_id'],
                client_conf['data_conf']['reader_module']['module_name'] + ".py")

    # import code of data provider to read data
    dps_read_data_module = getattr(__import__(client_conf['data_conf']['reader_module']['module_name']),
                                   client_conf['data_conf']['reader_module']["function_map"])

    if client_conf['data_conf']['method'] == 'local':
        filename = client_conf['data_conf']['location'].split('/')[-1]
        X, y, _, _ = dps_read_data_module("/data/" + filename)
    else:
        X, y, _, _ = dps_read_data_module(client_conf['data_conf']['location'])

    _com = completeness(X)
    if _com < 1:
        np.nan_to_num(X, copy=False)

    qod_metrics = {"class_overlap": class_overlap(X, y),
                   "class_parity": class_parity(y),
                   "label_purity": label_purity(X, y),
                   "feature_correlation": feature_correlation(X),
                   "feature_relevance": feature_relevance(X, y, 0.9),
                   "completeness": _com}

    # report this metric to data service
    r = requests.post(url=client_conf['mgt_service'] + "/service/report",
                      json={"type": "qod_report",
                            "code": 0,
                            "request_id": args.sessionid,
                            "qod": {"dataset_id": client_conf['dataset_id'],
                                    "metric": qod_metrics
                                    }
                            }
                      )
    logging.info("Post QoD request [{}] --result [{}]: status {}".format(args.sessionid,
                                                                         qod_metrics,
                                                                         r.status_code))
