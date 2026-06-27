import sys
sys.path.append(".")
from app.core.cfbd_client import fetch_games, fetch_lines, fetch_sp_ratings

# Pull one season as a sanity check
games = fetch_games(2023)
lines = fetch_lines(2023)
ratings = fetch_sp_ratings(2023)

print(f"Games: {len(games)} rows, columns: {list(games.columns)}")
print(f"Lines: {len(lines)} rows, columns: {list(lines.columns)}")
print(f"SP+ Ratings: {len(ratings)} rows, columns: {list(ratings.columns)}")
print(games.head(2))