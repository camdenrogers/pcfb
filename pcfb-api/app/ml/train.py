import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
import numpy as np

FEATURE_COLS = [
    "spRatingDiff",
    "eloDiff",
    "isNeutral",
    "spread",
    "overUnder",
    "homeSPOffense",
    "awaySPOffense",
    "homeSPDefense",
    "awaySPDefense",
]
TARGET_COVER = "covered"
TARGET_MARGIN = "homeMargin"

def train():
    df = pd.read_csv("data/processed/features.csv")
    print(f"Training on {len(df)} rows")

    X = df[FEATURE_COLS]
    y_cover = df[TARGET_COVER]
    y_margin = df[TARGET_MARGIN]

    X_train, X_test, yc_train, yc_test, ym_train, ym_test = train_test_split(
        X, y_cover, y_margin, test_size=0.2, random_state=42, shuffle=True
    )

    # --- Cover classifier ---
    classifiers = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000))
        ]),
        "gradient_boosting": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=3))
        ]),
    }

    best_clf = None
    best_clf_score = 0

    for name, model in classifiers.items():
        cv_scores = cross_val_score(model, X_train, yc_train, cv=5, scoring="accuracy")
        print(f"\n{name} (classifier)")
        print(f"  CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        model.fit(X_train, yc_train)
        test_acc = accuracy_score(yc_test, model.predict(X_test))
        print(f"  Test accuracy: {test_acc:.3f}")
        if cv_scores.mean() > best_clf_score:
            best_clf_score = cv_scores.mean()
            best_clf = (name, model)

    # --- Margin regressor ---
    regressors = {
        "ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", Ridge())
        ]),
        "gradient_boosting_reg": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", GradientBoostingRegressor(n_estimators=100, max_depth=3))
        ]),
    }

    best_reg = None
    best_reg_score = float("inf")

    for name, model in regressors.items():
        cv_scores = cross_val_score(model, X_train, ym_train, cv=5, scoring="neg_mean_absolute_error")
        mae = -cv_scores.mean()
        print(f"\n{name} (regressor)")
        print(f"  CV MAE: {mae:.2f} points (+/- {cv_scores.std():.2f})")
        model.fit(X_train, ym_train)
        test_mae = mean_absolute_error(ym_test, model.predict(X_test))
        print(f"  Test MAE: {test_mae:.2f} points")
        if mae < best_reg_score:
            best_reg_score = mae
            best_reg = (name, model)

    # Save both models
    Path("models/saved").mkdir(parents=True, exist_ok=True)

    clf_name, clf_model = best_clf
    clf_model.fit(X, y_cover)  # refit on full data
    joblib.dump(clf_model, "models/saved/model.pkl")
    joblib.dump(FEATURE_COLS, "models/saved/feature_cols.pkl")
    print(f"\nBest classifier: {clf_name} (CV: {best_clf_score:.3f})")

    reg_name, reg_model = best_reg
    reg_model.fit(X, y_margin)  # refit on full data
    joblib.dump(reg_model, "models/saved/margin_model.pkl")
    print(f"Best regressor: {reg_name} (CV MAE: {best_reg_score:.2f} pts)")

    print("\nClassification report on test set:")
    print(classification_report(yc_test, clf_model.predict(X_test)))

if __name__ == "__main__":
    train()
