from app.normalize import normalize_game, normalize_talent, normalize_team


def test_normalize_game_camel_case():
    raw = {
        "id": 401628374, "season": 2024, "week": 1, "seasonType": "regular",
        "startDate": "2024-08-31T16:00:00.000Z", "neutralSite": True, "completed": True,
        "homeId": 61, "homeTeam": "Georgia", "homePoints": 34,
        "awayId": 333, "awayTeam": "Clemson", "awayPoints": 3,
    }
    g = normalize_game(raw)
    assert g["home_team"] == "Georgia" and g["away_points"] == 3
    assert g["neutral_site"] is True and g["completed"] is True
    assert g["start_date"].year == 2024 and g["start_date"].tzinfo is not None


def test_normalize_game_snake_case_and_unplayed():
    raw = {"id": 1, "season": 2026, "week": 14, "season_type": "regular", "start_date": None,
           "neutral_site": False, "home_id": 2, "home_team": "Auburn", "home_points": None,
           "away_id": 333, "away_team": "Alabama", "away_points": None}
    g = normalize_game(raw)
    assert g["completed"] is False and g["home_points"] is None and g["start_date"] is None


def test_normalize_team_and_talent():
    t = normalize_team({"id": 61, "school": "Georgia", "mascot": "Bulldogs", "abbreviation": "UGA",
                        "conference": "SEC", "color": "#ba0c2f", "alternateColor": "#000000",
                        "logos": ["http://a.espncdn.com/i/teamlogos/ncaa/500/61.png"]})
    assert t["alt_color"] == "#000000" and t["logo"].endswith("61.png")
    assert normalize_team({"school": "No id"}) is None
    assert normalize_talent({"year": 2025, "team": "Georgia", "talent": "1009.5"}, 2025)["talent"] == 1009.5
    assert normalize_talent({"school": "Georgia", "talent": 990}, 2024)["season"] == 2024
    assert normalize_talent({"team": "X", "talent": None}, 2024) is None
