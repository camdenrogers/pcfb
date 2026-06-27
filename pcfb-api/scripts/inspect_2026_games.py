import sys
sys.path.insert(0, ".")
from app.core.cfbd_client import fetch_games
import pandas as pd

games = fetch_games(2026)
print(f"Total 2026 games: {len(games)}")
print(f"Columns: {list(games.columns)}")
print(f"\nWeeks available: {sorted(games['week'].unique())}")
print(f"\nWeek 1 games:")
week1 = games[games["week"] == 1]
print(f"Count: {len(week1)}")
print(week1[["homeTeam", "awayTeam", "homePoints", "awayPoints", "startDate"]].head(10))
