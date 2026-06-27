import sys
sys.path.insert(0, ".")
import cfbd
from app.core.config import settings

configuration = cfbd.Configuration()
configuration.api_key["Authorization"] = settings.cfbd_api_key
configuration.api_key_prefix["Authorization"] = "Bearer"
client = cfbd.ApiClient(configuration)

api = cfbd.GamesApi(client)
games = api.get_games(year=2023, division="fbs", season_type="regular")

print(f"Total games: {len(games)}")
has_home = [g for g in games if g.home_team is not None]
print(f"Games with home_team: {len(has_home)}")

# Show a game that has data
g = has_home[0]
print(f"\nSample game with data:")
print(f"  {g.away_team} @ {g.home_team}")
print(f"  Score: {g.away_points} - {g.home_points}")
print(f"  Week: {g.week}")
print(f"  ID: {g.id}")
