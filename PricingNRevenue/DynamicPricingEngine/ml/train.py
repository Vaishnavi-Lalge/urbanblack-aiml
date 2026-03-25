import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os

def train_model_from_csv():
    csv_path = r"c:\\Visual Studio Code\\urbanblack-aiml\\PricingNRevenue\\DynamicPricingEngine\\data\\utr_fare_dataset_7500.csv"
    print(f"Loading dataset from {csv_path} ...")
    
    if not os.path.exists(csv_path):
        print("CSV not found!")
        return

    df = pd.read_csv(csv_path)
    
    # Feature Engineering from CSV
    # We map what our ML inference expects: zone_demand_supply_ratio, rainfall_mm_per_hour, is_peak_hour
    # The pure dataset doesn't have "zone_demand_supply_ratio" expressly defined in this form. 
    # It has 'traffic_multiplier', 'rain_surcharge_applied', 'is_peak_hour'. 
    # We will simulate the demand supply ratio correlation with traffic multiplier to map linearly.
    
    # Deriving proxy 'zone_demand_supply_ratio' assuming traffic_multiplier is highly correlated
    df['zone_demand_supply_ratio'] = df['traffic_multiplier'].apply(lambda x: x * 1.5 if x > 1.0 else 1.0)
    
    # Map weather string to approx rainfall_mm
    def get_rain(w):
        if w == 'heavy_rain': return 12.0
        elif w == 'light_rain': return 3.0
        elif w == 'drizzle': return 1.5
        return 0.0
    df['rainfall_mm_per_hour'] = df['weather'].apply(get_rain)
    
    features = ['zone_demand_supply_ratio', 'rainfall_mm_per_hour', 'is_peak_hour']
    target = 'traffic_multiplier' # Treating traffic_multiplier as our surge metric to predict
    
    # Clean anomalies
    df = df.dropna(subset=features + [target])
    
    X_train, X_test, y_train, y_test = train_test_split(df[features], df[target], test_size=0.2, random_state=42)
    
    # LightGBM Dataset
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'verbose': -1
    }
    
    print("Starting LightGBM training on actual dataset...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, test_data],
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)]
    )
    
    preds = model.predict(X_test, num_iteration=model.best_iteration)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    
    print(f"Validation MAE: {mae:.4f}")
    print(f"Validation RMSE: {rmse:.4f}")
    
    # Save model
    os.makedirs(r"c:\\Visual Studio Code\\urbanblack-aiml\\PricingNRevenue\\DynamicPricingEngine\\models", exist_ok=True)
    model_path = r"c:\\Visual Studio Code\\urbanblack-aiml\\PricingNRevenue\\DynamicPricingEngine\\models\\surge_lgb_model.txt"
    model.save_model(model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model_from_csv()
