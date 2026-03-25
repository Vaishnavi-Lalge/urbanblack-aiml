import lightgbm as lgb
import os
import numpy as np

class MLSpeeds:
    def __init__(self, model_path=r"c:\\Visual Studio Code\\urbanblack-aiml\\PricingNRevenue\\DynamicPricingEngine\\models\\surge_lgb_model.txt"):
        self.model_path = model_path
        self.model = None
        self._load_model()
        
    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = lgb.Booster(model_file=self.model_path)
            print("Loaded LightGBM model successfully.")
        else:
            print("LightGBM model not found. Using Rule-Based fallback.")
            
    def predict_surge(self, request) -> float:
        if not self.model:
            from app.services.rule_based_surge import get_rule_based_surge_multiplier
            multiplier, _ = get_rule_based_surge_multiplier(request.zone_demand_supply_ratio)
            return multiplier
            
        # Features map exactly to the training dataframe order
        features = np.array([[
            request.zone_demand_supply_ratio,
            request.rainfall_mm_per_hour,
            int(request.is_peak_hour)
        ]])
        
        pred = self.model.predict(features)[0]
        return float(np.clip(pred, 1.0, 2.5))

ml_predictor = MLSpeeds()
