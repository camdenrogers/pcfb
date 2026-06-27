import requests
import pandas as pd
from app.core.config import settings

BASE_URL = "https://api.collegefootballdata.com"

def get_headers() -> dict:
    return {"Authorization": f"Bearer {settings.cfbd_api_key}"}

def fetch_games(year: int, season_type: str = "regular") -> pd.DataFrame:
    r = requests.get(
        f"{BASE_URL}/games",
        headers=get_headers(),
        params={"year": year, "seasonType": season_type, "division": "fbs"}
    )
    r.raise_for_status()
    return pd.DataFrame(r.json())

def fetch_lines(year: int) -> pd.DataFrame:
    r = requests.get(
        f"{BASE_URL}/lines",
        headers=get_headers(),
        params={"year": year}
    )
    r.raise_for_status()
    return pd.DataFrame(r.json())

def fetch_sp_ratings(year: int) -> pd.DataFrame:
    r = requests.get(
        f"{BASE_URL}/ratings/sp",
        headers=get_headers(),
        params={"year": year}
    )
    r.raise_for_status()
    return pd.DataFrame(r.json())

def fetch_elo_ratings(year: int) -> pd.DataFrame:
    r = requests.get(
        f"{BASE_URL}/ratings/elo",
        headers=get_headers(),
        params={"year": year}
    )
    r.raise_for_status()
    return pd.DataFrame(r.json())
