from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np
from pathlib import Path


# Get the path to the model file relative to this script
model_path = Path(__file__).resolve().parent.parent / "model" / "model.pkl"

# Load the model
with open(model_path, "rb") as f:
    model = pickle.load(f)

app = FastAPI()

# Define input schema
class EloInput(BaseModel):
    homePregameElo: float
    awayPregameElo: float

# Route to make predictions
@app.post("/predict")
def predict_spread(input: EloInput):
    features = np.array([[input.homePregameElo, input.awayPregameElo]])
    predicted_spread = model.predict(features)[0]
    return {"predicted_spread": predicted_spread}
