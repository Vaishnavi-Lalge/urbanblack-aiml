import pandas as pd

def clean_data(df):

    # Remove duplicates
    df = df.drop_duplicates()

    # Handle missing values
    df = df.fillna(method="ffill")

    # Remove invalid rows
    df = df[df["trip_distance"] > 0]
    df = df[df["trip_duration_min"] > 0]

    print("✅ Data cleaned")

    return df