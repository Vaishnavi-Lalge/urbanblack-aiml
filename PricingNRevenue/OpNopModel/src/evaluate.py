import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score,
                             confusion_matrix, classification_report)
from preprocess import preprocess

# Load and preprocess
X, y = preprocess('../data/km_classifier_dummy_dataset.csv')

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)

# Load saved model
model  = joblib.load('../models/km_classifier.pkl')
y_pred = model.predict(X_test)

# Print metrics
print("===== XGBoost Evaluation =====")
print(f"Accuracy : {accuracy_score(y_test, y_pred):.2%}")
print(f"Precision: {precision_score(y_test, y_pred):.2%}")
print(f"Recall   : {recall_score(y_test, y_pred):.2%}")
print(f"F1 Score : {f1_score(y_test, y_pred):.2%}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred,
      target_names=['Non-Operational', 'Operational']))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Non-Op', 'Operational'],
            yticklabels=['Non-Op', 'Operational'])
plt.title('Confusion Matrix - XGBoost')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.tight_layout()
plt.savefig('../models/confusion_matrix.png')
plt.show()
print("Confusion matrix saved ✅")