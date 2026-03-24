import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from imblearn.over_sampling import SMOTE
import joblib

def preprocess(filepath):
    df = pd.read_csv(filepath)

    # Extract time features
    df['requestedAt'] = pd.to_datetime(df['requestedAt'])
    df['hour']        = df['requestedAt'].dt.hour
    df['day_of_week'] = df['requestedAt'].dt.dayofweek
    df['month']       = df['requestedAt'].dt.month
    df.drop(columns=['requestedAt', 'ride_id'], inplace=True)

    # Encode categoricals
    le_status = LabelEncoder()
    le_demand = LabelEncoder()
    df['status']       = le_status.fit_transform(df['status'])
    df['demand_level'] = le_demand.fit_transform(df['demand_level'])

    # Split features and target
    X = df.drop(columns=['label'])
    y = df['label']

    # Scale
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # SMOTE
    sm = SMOTE(random_state=42)
    X_resampled, y_resampled = sm.fit_resample(X_scaled, y)

    # Save scaler
    joblib.dump(scaler, '../models/scaler.pkl')
    print("Preprocessing done ✅")

    return X_resampled, y_resampled