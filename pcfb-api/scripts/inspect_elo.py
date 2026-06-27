import sys
sys.path.insert(0, ".")
from app.core.cfbd_client import fetch_elo_ratings

elo = fetch_elo_ratings(2024)
print("Columns:", list(elo.columns))
print(elo.head(3))
