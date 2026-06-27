import sys
sys.path.insert(0, ".")
import pandas as pd
import joblib
from app.ml.features import build_features
from sklearn.metrics import accuracy_score, classification_report

# Build 2024 feature set
print("Fetching 2024 data...")
df = build_features([2024])
print(f"Built {len(df)} rows")

# Load saved model
model = joblib.load("models/saved/model.pkl")
feature_cols = joblib.load("models/saved/feature_cols.pkl")

X = df[feature_cols]
y = df["covered"]

# Predict
preds = model.predict(X)
acc = accuracy_score(y, preds)

print(f"\n2024 Out-of-sample accuracy: {acc:.3f}")
print(f"Cover rate in 2024 data: {y.mean():.3f}")
print("\nClassification report:")
print(classification_report(y, preds))
