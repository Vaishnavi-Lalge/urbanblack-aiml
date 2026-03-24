import numpy as np
import pandas as pd

# Load training data stats
train_data = pd.read_csv("data/dataset.csv")

train_mean = train_data.mean()
train_std = train_data.std()

def detect_drift(input_features):
    drift_report = {}

    for i, col in enumerate(train_data.columns[:-2]):  # exclude targets
        value = input_features[0][i]

        mean = train_mean[col]
        std = train_std[col]

        if std == 0:
            continue

        z_score = abs((value - mean) / std)

        drift_report[col] = {
            "value": float(value),
            "z_score": float(z_score),
            "drift": z_score > 3
        }

    return drift_report