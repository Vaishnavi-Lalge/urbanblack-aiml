import os
import sys
from collections import Counter

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, f1_score, precision_recall_curve, recall_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "clean_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.decision_logic import default_decision_config, evaluate_decision, is_model_source
from src.feature_engineering import TIME_SPLIT_COLUMN

NON_MODEL_COLUMNS = [
    "label",
    "segment_id",
    "driver_id",
    "duration_seconds",
    "speed_kmh",
    "time_since_last_trip_end_min",
    TIME_SPLIT_COLUMN,
]
CONFIDENCE_MARGIN_CANDIDATES = [0.06]
MIN_MODEL_SHARE = 0.60
MIN_BALANCED_F1 = 0.80


def split_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if TIME_SPLIT_COLUMN not in df.columns:
        raise ValueError(f"{TIME_SPLIT_COLUMN} is required for time-based validation.")

    ordered = df.copy()
    ordered["_sort_ts"] = pd.to_datetime(ordered[TIME_SPLIT_COLUMN], utc=True, errors="coerce")
    ordered = (
        ordered.dropna(subset=["_sort_ts"])
        .sort_values("_sort_ts")
        .drop(columns=["_sort_ts"])
        .reset_index(drop=True)
    )

    train_end = int(len(ordered) * 0.6)
    calib_end = int(len(ordered) * 0.8)

    train_df = ordered.iloc[:train_end].copy()
    calib_df = ordered.iloc[train_end:calib_end].copy()
    test_df = ordered.iloc[calib_end:].copy()
    return train_df, calib_df, test_df


def get_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    drop_cols = [col for col in NON_MODEL_COLUMNS if col in df.columns]
    return df.drop(columns=drop_cols)


def build_pipeline(X: pd.DataFrame, y: pd.Series) -> Pipeline:
    categorical = X.select_dtypes(include=["object"]).columns.tolist()
    numerical = X.select_dtypes(exclude=["object"]).columns.tolist()

    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), numerical),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(len(y[y == 0]) / len(y[y == 1])),
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline([("prep", preprocessor), ("model", model)])


def run_decision_layer(
    rows: list[dict], probas: np.ndarray, decision_config: dict
) -> tuple[list[int], list[str]]:
    predictions = []
    sources = []

    for row, proba in zip(rows, probas):
        decision = evaluate_decision(row, float(proba), decision_config)
        predictions.append(decision["prediction"])
        sources.append(decision["source"])

    return predictions, sources


def build_threshold_candidates(probas: np.ndarray, y_true: pd.Series) -> list[float]:
    _, _, thresholds = precision_recall_curve(y_true, probas)
    candidates = np.unique(np.round(thresholds, 3))
    candidates = candidates[(candidates >= 0.30) & (candidates <= 0.75)]
    candidates = np.unique(np.append(candidates, 0.50))

    if len(candidates) > 25:
        idx = np.linspace(0, len(candidates) - 1, 25, dtype=int)
        candidates = candidates[idx]

    return candidates.tolist()


def optimize_decision_config(calib_df: pd.DataFrame, calibrated_model, model_features: list[str]) -> tuple[dict, dict]:
    rows = calib_df.to_dict(orient="records")
    y_calib = calib_df["label"]
    probas = calibrated_model.predict_proba(calib_df[model_features].copy())[:, 1]
    threshold_candidates = build_threshold_candidates(probas, y_calib)

    candidates = []
    for threshold in threshold_candidates:
        for margin in CONFIDENCE_MARGIN_CANDIDATES:
            low_conf = round(max(0.0, threshold - margin), 3)
            high_conf = round(min(1.0, threshold + margin), 3)
            if not (low_conf < threshold < high_conf):
                continue

            decision_config = default_decision_config()
            decision_config["decision_threshold"] = round(float(threshold), 3)
            decision_config["low_conf"] = round(float(threshold) - margin, 3)
            decision_config["high_conf"] = round(float(threshold) + margin, 3)
            decision_config["direct_model_margin"] = 0.06
            decision_config["rule_trigger_margin"] = 0.04
            decision_config["min_rule_signals"] = 2

            preds, sources = run_decision_layer(rows, probas, decision_config)
            model_share = sum(is_model_source(source) for source in sources) / len(sources)
            candidates.append(
                {
                    "config": decision_config,
                    "f1": f1_score(y_calib, preds),
                    "class0_recall": recall_score(y_calib, preds, pos_label=0),
                    "model_share": model_share,
                }
            )

    preferred = [candidate for candidate in candidates if candidate["model_share"] >= MIN_MODEL_SHARE]
    balanced = [candidate for candidate in preferred if candidate["f1"] >= MIN_BALANCED_F1]

    if balanced:
        search_pool = balanced
        ranking_key = lambda candidate: (
            candidate["class0_recall"],
            candidate["f1"],
            candidate["model_share"],
        )
    else:
        search_pool = preferred or candidates
        ranking_key = lambda candidate: (
            candidate["f1"],
            candidate["class0_recall"],
            candidate["model_share"],
        )

    best = max(search_pool, key=ranking_key)

    return best["config"], best


def print_feature_importance(base_pipeline: Pipeline):
    model = base_pipeline.named_steps["model"]
    feature_names = base_pipeline.named_steps["prep"].get_feature_names_out()
    importances = model.feature_importances_
    ranked_features = sorted(
        zip(feature_names, importances), key=lambda item: item[1], reverse=True
    )

    print("\nTop Features:\n")
    for feature_name, importance in ranked_features[:15]:
        print(f"{feature_name}: {importance:.4f}")


def evaluate_hybrid(
    df: pd.DataFrame, calibrated_model, model_features: list[str], decision_config: dict
):
    rows = df.to_dict(orient="records")
    y_true = df["label"]
    probas = calibrated_model.predict_proba(df[model_features].copy())[:, 1]
    preds, sources = run_decision_layer(rows, probas, decision_config)
    source_counts = Counter(sources)
    total = sum(source_counts.values())

    print("\nHybrid Test Report:\n")
    print(classification_report(y_true, preds))
    print("Hybrid Test F1:", round(f1_score(y_true, preds), 4))
    print("Hybrid Class 0 Recall:", round(recall_score(y_true, preds, pos_label=0), 4))
    print(
        "Hybrid Model Share:",
        round(sum(is_model_source(source) for source in sources) / len(sources), 4),
    )

    print("\nHybrid Source Distribution:\n")
    for source, count in source_counts.most_common():
        print(f"{source}: {count} ({count / total:.2%})")


def train():
    df = pd.read_csv(DATA_PATH)

    if df.empty:
        raise ValueError(
            f"{DATA_PATH} has no training rows. Run src/preprocess.py and verify preprocessing first."
        )

    train_df, calib_df, test_df = split_data(df)

    X_train = get_model_frame(train_df)
    y_train = train_df["label"]
    model_features = X_train.columns.tolist()

    base_pipeline = build_pipeline(X_train, y_train)
    cv = TimeSeriesSplit(n_splits=3)
    scores = cross_val_score(base_pipeline, X_train, y_train, cv=cv, scoring="f1", n_jobs=1)
    print("\nTrain CV F1:", round(scores.mean(), 4))

    base_pipeline.fit(X_train, y_train)
    base_test_preds = base_pipeline.predict(get_model_frame(test_df))

    print("\nBase Model Test Report:\n")
    print(classification_report(test_df["label"], base_test_preds))
    print("Base Model Test F1:", round(f1_score(test_df["label"], base_test_preds), 4))
    print_feature_importance(base_pipeline)

    calibrated_model = CalibratedClassifierCV(
        estimator=build_pipeline(X_train, y_train),
        method="isotonic",
        cv=TimeSeriesSplit(n_splits=3),
        n_jobs=1,
    )
    calibrated_model.fit(X_train, y_train)

    decision_config, best_candidate = optimize_decision_config(calib_df, calibrated_model, model_features)

    print("\nSelected Decision Config:\n")
    print(
        {
            "decision_threshold": decision_config["decision_threshold"],
            "low_conf": decision_config["low_conf"],
            "high_conf": decision_config["high_conf"],
            "calibration_f1": round(best_candidate["f1"], 4),
            "calibration_class0_recall": round(best_candidate["class0_recall"], 4),
            "calibration_model_share": round(best_candidate["model_share"], 4),
        }
    )

    evaluate_hybrid(test_df, calibrated_model, model_features, decision_config)

    artifact = {
        "model": calibrated_model,
        "model_features": model_features,
        "decision_config": decision_config,
    }

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(artifact, MODEL_PATH)
    print("\nModel saved:", MODEL_PATH)


if __name__ == "__main__":
    train()
