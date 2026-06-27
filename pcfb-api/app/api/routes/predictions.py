from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
from pathlib import Path

router = APIRouter()

MODEL_PATH = Path("models/saved/model.pkl")
FEATURE_COLS_PATH = Path("models/saved/feature_cols.pkl")

def load_model():
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model not trained yet")
    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURE_COLS_PATH)
    return model, feature_cols

class PredictionRequest(BaseModel):
    homeTeam: str
    awayTeam: str
    spread: float
    overUnder: float
    homeSPRating: float
    awaySPRating: float
    homeSPOffense: float
    awaySPOffense: float
    homeSPDefense: float
    awaySPDefense: float
    homePregameElo: float
    awayPregameElo: float
    isNeutral: int = 0

class PredictionResponse(BaseModel):
    homeTeam: str
    awayTeam: str
    spread: float
    predictedCover: bool
    confidence: float

@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    model, feature_cols = load_model()

    features = {
        "spRatingDiff": req.homeSPRating - req.awaySPRating,
        "eloDiff": req.homePregameElo - req.awayPregameElo,
        "isNeutral": req.isNeutral,
        "spread": req.spread,
        "overUnder": req.overUnder,
        "homeSPOffense": req.homeSPOffense,
        "awaySPOffense": req.awaySPOffense,
        "homeSPDefense": req.homeSPDefense,
        "awaySPDefense": req.awaySPDefense,
    }

    X = pd.DataFrame([features])[feature_cols]
    prob = model.predict_proba(X)[0]
    predicted_cover = bool(prob[1] > 0.5)
    confidence = float(prob[1] if predicted_cover else prob[0])

    return PredictionResponse(
        homeTeam=req.homeTeam,
        awayTeam=req.awayTeam,
        spread=req.spread,
        predictedCover=predicted_cover,
        confidence=round(confidence, 3),
    )
