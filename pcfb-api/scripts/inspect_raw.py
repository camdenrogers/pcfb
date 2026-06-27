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

# Look at the first game object directly
g = games[0]
print("Type:", type(g))
print("Dir:", [x for x in dir(g) if not x.startswith("_")])
print("\nFirst game:")
print(g)
