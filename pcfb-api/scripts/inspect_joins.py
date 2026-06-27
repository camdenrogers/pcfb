import sys
sys.path.insert(0, ".")
from app.core.cfbd_client import fetch_games, fetch_lines, fetch_sp_ratings

games = fetch_games(2023)
lines = fetch_lines(2023)
sp = fetch_sp_ratings(2023)

# Check a few team names from each
print("Games home teams sample:", games["home_team"].head(5).tolist())
print("SP+ teams sample:", sp["team"].head(5).tolist())

# Check if lines merge works
print("\nGames IDs sample:", games["id"].head(3).tolist())
print("Lines IDs sample:", lines["id"].head(3).tolist())
print("ID dtype games:", games["id"].dtype)
print("ID dtype lines:", lines["id"].dtype)
