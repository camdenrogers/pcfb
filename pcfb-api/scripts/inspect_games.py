import sys
sys.path.insert(0, ".")
from app.core.cfbd_client import fetch_games

games = fetch_games(2023)
print("All columns:", list(games.columns))
print("\nFirst row:")
print(games.iloc[0].to_dict())
