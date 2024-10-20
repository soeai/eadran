import pandas as pd


def read_data(data_file):
    df = pd.read_csv(data_file)
    y = df['is_fraud']
    X = df.drop('is_fraud', axis=1).to_numpy()
    return X, y, None, None
