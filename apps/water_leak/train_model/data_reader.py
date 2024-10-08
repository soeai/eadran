import pandas as pd


def read_data(data_file):
    df = pd.read_csv(data_file)
    y = df['leak']
    X = df.drop('leak', axis=1).to_numpy()
    return X, y