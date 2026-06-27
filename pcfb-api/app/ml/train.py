import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

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
TARGET = "covered"

def train():
    df = pd.read_csv("data/processed/features.csv")
    print(f"Training on {len(df)} rows")

    X = df[FEATURE_COLS]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    # Try two models
    models = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000))
        ]),
        "gradient_boosting": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=3))
        ]),
    }

    best_model = None
    best_score = 0

    for name, model in models.items():
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
        print(f"\n{name}")
        print(f"  CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

        model.fit(X_train, y_train)
        test_acc = accuracy_score(y_test, model.predict(X_test))
        print(f"  Test accuracy: {test_acc:.3f}")

        if cv_scores.mean() > best_score:
            best_score = cv_scores.mean()
            best_model = (name, model)

    # Save best model
    name, model = best_model
    Path("models/saved").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, "models/saved/model.pkl")
    joblib.dump(FEATURE_COLS, "models/saved/feature_cols.pkl")

    print(f"\nBest model: {name} (CV accuracy: {best_score:.3f})")
    print("Saved to models/saved/model.pkl")

    # Full report on best model
    print("\nClassification report on test set:")
    print(classification_report(y_test, model.predict(X_test)))

if __name__ == "__main__":
    train()
