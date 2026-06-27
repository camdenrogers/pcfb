import sys
sys.path.insert(0, ".")
from app.core.cfbd_client import fetch_sp_ratings, fetch_elo_ratings

sp = fetch_sp_ratings(2026)
elo = fetch_elo_ratings(2026)

print("SP+ rows:", len(sp))
print("SP+ columns:", list(sp.columns) if len(sp) > 0 else "EMPTY")

print("\nElo rows:", len(elo))
print("Elo columns:", list(elo.columns) if len(elo) > 0 else "EMPTY")

if len(elo) > 0:
    print(elo.head(3))
