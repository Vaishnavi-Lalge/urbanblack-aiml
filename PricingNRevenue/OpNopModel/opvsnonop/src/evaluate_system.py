import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score, recall_score

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
CLEAN_DATA_PATH = os.path.join(DATA_DIR, "clean_data.csv")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.api import MODEL_FEATURES, DECISION_CONFIG, evaluate_decision, is_model_source, model


def load_eval_data() -> pd.DataFrame:
    return pd.read_csv(CLEAN_DATA_PATH).dropna(
        subset=list(MODEL_FEATURES) + ["speed_kmh", "time_since_last_trip_end_min", "label"]
    )


def main():
    df = load_eval_data()

    y_true = df["label"]
    y_pred = []
    source_counts = Counter()
    adjustment_counts = Counter()
    adjustment_values = []
    probas = model.predict_proba(df[MODEL_FEATURES].copy())[:, 1]

    for row_dict, proba in zip(df.to_dict(orient="records"), probas):
        decision = evaluate_decision(row_dict, float(proba), DECISION_CONFIG)
        y_pred.append(decision["prediction"])
        source_counts[decision["source"]] += 1
        adjustment_counts.update(decision["adjustments"])
        if decision["adjustments"]:
            adjustment_values.append(abs(decision["total_adjustment"]))

    total = sum(source_counts.values())
    model_share = sum(
        count for source, count in source_counts.items() if is_model_source(source)
    ) / total
    rule_share = source_counts["soft_rule_adjusted"] / total
    avg_adjustment = sum(adjustment_values) / len(adjustment_values) if adjustment_values else 0.0

    print("\nPROBA DISTRIBUTION:\n")
    print("min:", round(float(np.min(probas)), 4))
    print("max:", round(float(np.max(probas)), 4))
    print("mean:", round(float(np.mean(probas)), 4))
    print("\nHistogram bins:")
    hist, bins = np.histogram(probas, bins=10)
    for i in range(len(hist)):
        print(f"{bins[i]:.2f}-{bins[i + 1]:.2f}: {hist[i]}")

    print("\nSYSTEM REPORT:\n")
    print(classification_report(y_true, y_pred))
    print("System F1:", round(f1_score(y_true, y_pred), 4))
    print("Class 0 Recall:", round(recall_score(y_true, y_pred, pos_label=0), 4))
    print("Model Decision Share:", f"{model_share:.2%}")
    print("Rule Decision Share:", f"{rule_share:.2%}")
    print("Average Adjustment Magnitude:", round(avg_adjustment, 4))

    print("\nSOURCE DISTRIBUTION:\n")
    for source, count in source_counts.most_common():
        print(f"{source}: {count} ({count / total:.2%})")

    print("\nSOFT RULE USAGE:\n")
    if adjustment_counts:
        for adjustment, count in adjustment_counts.most_common():
            print(f"{adjustment}: {count} ({count / total:.2%})")
    else:
        print("No soft-rule adjustments applied.")


if __name__ == "__main__":
    main()
