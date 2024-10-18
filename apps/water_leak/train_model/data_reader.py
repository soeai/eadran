import pandas as pd


def read_data(data_file):
    df = pd.read_csv(data_file)
    y = df['target']
    X = df.drop('target', axis=1).to_numpy()
    return X, y