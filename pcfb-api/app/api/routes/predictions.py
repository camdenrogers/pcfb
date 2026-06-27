from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

router = APIRouter()

MODEL_PATH = Path("models/saved/model.pkl")
FEATURE_COLS_PATH = Path("models/saved/feature_cols.pkl")
MARGIN_MODEL_PATH = Path("models/saved/margin_model.pkl")

def load_model():
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model not trained yet")
    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURE_COLS_PATH)
    return model, feature_cols

def extract_rating(val):
    if isinstance(val, dict):
        return val.get("rating")
    return val

def safe_float(val):
    try:
        f = float(val)
        return None if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return None

def extract_spread(lines_list):
    if not lines_list:
        return None
    spreads = [l["spread"] for l in lines_list if l.get("spread") is not None]
    if not spreads:
        return None
    return sum(spreads) / len(spreads)

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
    modelSpread: float | None
    predictedCover: bool
    confidence: float

@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    model, feature_cols = load_model()

    features = {
        "spRatingDiff": req.awaySPRating - req.homeSPRating,
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

    model_spread = None
    if MARGIN_MODEL_PATH.exists():
        margin_model = joblib.load(MARGIN_MODEL_PATH)
        predicted_margin = float(margin_model.predict(X)[0])
        model_spread = round(-predicted_margin, 1)

    return PredictionResponse(
        homeTeam=req.homeTeam,
        awayTeam=req.awayTeam,
        spread=req.spread,
        modelSpread=model_spread,
        predictedCover=predicted_cover,
        confidence=round(confidence, 3),
    )

@router.get("/teams")
def get_teams():
    from app.core.cfbd_client import fetch_sp_ratings, fetch_elo_ratings

    sp = fetch_sp_ratings(2025)
    elo = fetch_elo_ratings(2025)[["team", "elo"]]

    sp["offenseRating"] = sp["offense"].apply(extract_rating)
    sp["defenseRating"] = sp["defense"].apply(extract_rating)

    merged = sp.merge(elo, on="team", how="left")

    teams = []
    for _, row in merged.iterrows():
        teams.append({
            "team": str(row["team"]) if row["team"] else None,
            "conference": str(row["conference"]) if row.get("conference") else None,
            "spRating": safe_float(row.get("rating")),
            "spOffense": safe_float(row.get("offenseRating")),
            "spDefense": safe_float(row.get("defenseRating")),
            "elo": safe_float(row.get("elo")),
        })

    return sorted(teams, key=lambda x: x["team"] or "")

@router.get("/predictions/week")
def get_week_predictions():
    from app.core.cfbd_client import fetch_games, fetch_sp_ratings, fetch_elo_ratings, fetch_lines
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    season = 2026

    games = fetch_games(season)
    if len(games) == 0:
        return {"games": [], "week": None, "season": season, "offseason": True}

    games["startDateParsed"] = pd.to_datetime(games["startDate"], utc=True, errors="coerce")

    future_games = games[games["startDateParsed"] > now]
    past_games = games[games["startDateParsed"] <= now]

    if len(future_games) > 0:
        next_week = int(future_games["week"].min())
    elif len(past_games) > 0:
        next_week = int(past_games["week"].max())
    else:
        return {"games": [], "week": None, "season": season, "offseason": True}

    week_games = games[games["week"] == next_week].copy()

    lines = fetch_lines(season)
    lines["vegasSpread"] = lines["lines"].apply(extract_spread)
    lines_flat = lines[["id", "vegasSpread"]].copy()
    week_games = week_games.merge(lines_flat, on="id", how="left")

    sp = fetch_sp_ratings(2025)
    sp["offenseRating"] = sp["offense"].apply(extract_rating)
    sp["defenseRating"] = sp["defense"].apply(extract_rating)

    sp_home = sp[["team", "rating", "offenseRating", "defenseRating"]].copy()
    sp_home.columns = ["homeTeam", "homeSPRating", "homeSPOffense", "homeSPDefense"]
    sp_away = sp[["team", "rating", "offenseRating", "defenseRating"]].copy()
    sp_away.columns = ["awayTeam", "awaySPRating", "awaySPOffense", "awaySPDefense"]

    week_games = week_games.merge(sp_home, on="homeTeam", how="left")
    week_games = week_games.merge(sp_away, on="awayTeam", how="left")

    elo_lookup = fetch_elo_ratings(2025).set_index("team")["elo"].to_dict()

    has_model = MODEL_PATH.exists()
    has_margin_model = MARGIN_MODEL_PATH.exists()

    if has_model:
        model = joblib.load(MODEL_PATH)
        feature_cols = joblib.load(FEATURE_COLS_PATH)

    if has_margin_model:
        margin_model = joblib.load(MARGIN_MODEL_PATH)

    results = []
    for _, row in week_games.iterrows():
        home_sp = safe_float(row.get("homeSPRating"))
        away_sp = safe_float(row.get("awaySPRating"))
        home_elo = safe_float(row.get("homePregameElo")) or safe_float(elo_lookup.get(str(row.get("homeTeam"))))
        away_elo = safe_float(row.get("awayPregameElo")) or safe_float(elo_lookup.get(str(row.get("awayTeam"))))
        vegas_spread = safe_float(row.get("vegasSpread"))

        prediction = None
        confidence = None
        model_spread = None

        if has_model and all(v is not None for v in [home_sp, away_sp, home_elo, away_elo]):
            sp_diff = away_sp - home_sp
            features = {
                "spRatingDiff": sp_diff,
                "eloDiff": home_elo - away_elo,
                "isNeutral": int(row.get("neutralSite") or 0),
                "spread": vegas_spread if vegas_spread is not None else sp_diff,
                "overUnder": 50.0,
                "homeSPOffense": safe_float(row.get("homeSPOffense")) or 0,
                "awaySPOffense": safe_float(row.get("awaySPOffense")) or 0,
                "homeSPDefense": safe_float(row.get("homeSPDefense")) or 0,
                "awaySPDefense": safe_float(row.get("awaySPDefense")) or 0,
            }
            X = pd.DataFrame([features])[feature_cols]
            prob = model.predict_proba(X)[0]
            prediction = bool(prob[1] > 0.5)
            confidence = round(float(prob[1] if prediction else prob[0]), 3)

            if has_margin_model:
                predicted_margin = float(margin_model.predict(X)[0])
                model_spread = round(-predicted_margin, 1)

        results.append({
            "homeTeam": str(row["homeTeam"]) if row.get("homeTeam") else None,
            "awayTeam": str(row["awayTeam"]) if row.get("awayTeam") else None,
            "startDate": str(row["startDate"]) if row.get("startDate") else None,
            "neutralSite": bool(row.get("neutralSite") or False),
            "homeConference": str(row["homeConference"]) if row.get("homeConference") else None,
            "awayConference": str(row["awayConference"]) if row.get("awayConference") else None,
            "homeSPRating": home_sp,
            "awaySPRating": away_sp,
            "homePregameElo": home_elo,
            "awayPregameElo": away_elo,
            "vegasSpread": vegas_spread,
            "modelSpread": model_spread,
            "predictedCover": prediction,
            "confidence": confidence,
        })

    return {
        "games": results,
        "week": next_week,
        "season": season,
        "offseason": False,
    }
