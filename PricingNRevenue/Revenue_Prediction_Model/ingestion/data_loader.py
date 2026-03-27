import pandas as pd
from config.settings import DATA_PATH

def load_data():
    try:
        df = pd.read_excel(DATA_PATH)
        print(f"✅ Data loaded: {df.shape}")
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {e}")