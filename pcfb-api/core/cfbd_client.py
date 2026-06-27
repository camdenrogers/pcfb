import cfbd
import pandas as pd
from app.core.config import settings

def get_cfbd_client() -> cfbd.ApiClient:
    configuration = cfbd.Configuration(
        access_token=settings.cfbd_api_key
    )
    return cfbd.ApiClient(configuration)


def fetch_games(year: int, season_type: str = "regular") -> pd.DataFrame:
    """Fetch all FBS games for a given season."""
    with get_cfbd_client() as client:
        api = cfbd.GamesApi(client)
        games = api.get_games(year=year, classification="fbs", season_type=season_type)
        return pd.DataFrame.from_records([g.to_dict() for g in games])


def fetch_lines(year: int) -> pd.DataFrame:
    """Fetch betting lines for a given season."""
    with get_cfbd_client() as client:
        api = cfbd.BettingApi(client)
        lines = api.get_lines(year=year)
        return pd.DataFrame.from_records([l.to_dict() for l in lines])


def fetch_sp_ratings(year: int) -> pd.DataFrame:
    """Fetch SP+ ratings for a given season."""
    with get_cfbd_client() as client:
        api = cfbd.RatingsApi(client)
        ratings = api.get_sp_ratings(year=year)
        return pd.DataFrame.from_records([r.to_dict() for r in ratings])


def fetch_elo_ratings(year: int) -> pd.DataFrame:
    """Fetch Elo ratings for a given season."""
    with get_cfbd_client() as client:
        api = cfbd.RatingsApi(client)
        ratings = api.get_elo_ratings(year=year)
        return pd.DataFrame.from_records([r.to_dict() for r in ratings])


def fetch_advanced_stats(year: int) -> pd.DataFrame:
    """Fetch advanced game stats for a given season."""
    with get_cfbd_client() as client:
        api = cfbd.StatsApi(client)
        stats = api.get_advanced_team_game_stats(year=year, classification="fbs")
        return pd.DataFrame.from_records([s.to_dict() for s in stats])