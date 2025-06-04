import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import pickle


# Load training data
df = pd.read_csv("data/prepared/games_prepared.csv", low_memory=False)

# Define features
features = [
    "homePregameElo",
    "awayPregameElo"
]

X = df[features]
y = df["spread"]

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=24)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Evaluate Model
print("Train R²:", model.score(X_train, y_train))
print("Test R²:", model.score(X_test, y_test))

# Save the model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)