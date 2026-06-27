import pandas as pd
from app.core.cfbd_client import fetch_games, fetch_lines, fetch_sp_ratings

def extract_spread(lines_list: list) -> float | None:
    if not lines_list:
        return None
    spreads = [l["spread"] for l in lines_list if l.get("spread") is not None]
    if not spreads:
        return None
    return sum(spreads) / len(spreads)

def extract_over_under(lines_list: list) -> float | None:
    if not lines_list:
        return None
    ous = [l["overUnder"] for l in lines_list if l.get("overUnder") is not None]
    if not ous:
        return None
    return sum(ous) / len(ous)

def extract_sp_rating(val) -> float | None:
    if isinstance(val, dict):
        return val.get("rating")
    return val

def build_features(years: list[int]) -> pd.DataFrame:
    all_frames = []

    for year in years:
        print(f"Fetching {year}...")

        games = fetch_games(year)
        lines = fetch_lines(year)
        sp = fetch_sp_ratings(year)

        # Extract nested offense/defense ratings
        sp["offenseRating"] = sp["offense"].apply(extract_sp_rating)
        sp["defenseRating"] = sp["defense"].apply(extract_sp_rating)

        # Filter to completed games with scores
        games = games[
            (games["homePoints"].notna()) &
            (games["awayPoints"].notna())
        ].copy()

        # Flatten lines
        lines["spread"] = lines["lines"].apply(extract_spread)
        lines["overUnder"] = lines["lines"].apply(extract_over_under)
        lines_flat = lines[["id", "spread", "overUnder"]].dropna(subset=["spread"])

        # Merge games with lines
        df = games.merge(lines_flat, on="id", how="inner")

        # Merge SP+ ratings
        sp_home = sp[["team", "rating", "offenseRating", "defenseRating"]].copy()
        sp_home.columns = ["homeTeam", "homeSPRating", "homeSPOffense", "homeSPDefense"]
        sp_away = sp[["team", "rating", "offenseRating", "defenseRating"]].copy()
        sp_away.columns = ["awayTeam", "awaySPRating", "awaySPOffense", "awaySPDefense"]

        df = df.merge(sp_home, on="homeTeam", how="left")
        df = df.merge(sp_away, on="awayTeam", how="left")

        # Feature engineering
        df["spRatingDiff"] = df["homeSPRating"] - df["awaySPRating"]
        df["eloDiff"] = df["homePregameElo"] - df["awayPregameElo"]
        df["isNeutral"] = df["neutralSite"].astype(int)

        # Target: did home team cover?
        df["homeMargin"] = df["homePoints"] - df["awayPoints"]
        df["covered"] = (df["homeMargin"] > -df["spread"]).astype(int)

        df["year"] = year
        all_frames.append(df)

    combined = pd.concat(all_frames, ignore_index=True)

    feature_cols = [
        "id", "year", "week", "homeTeam", "awayTeam",
        "homePoints", "awayPoints", "homeMargin",
        "spread", "overUnder", "covered",
        "spRatingDiff", "eloDiff", "isNeutral",
        "homeSPRating", "awaySPRating",
        "homeSPOffense", "awaySPOffense",
        "homeSPDefense", "awaySPDefense",
        "homePregameElo", "awayPregameElo",
        "conferenceGame",
    ]

    return combined[feature_cols].dropna(subset=["spRatingDiff", "eloDiff", "covered"])

if __name__ == "__main__":
    df = build_features([2021, 2022, 2023])
    print(f"\nBuilt {len(df)} rows with {len(df.columns)} features")
    print(df.head())
    print(f"\nCover rate: {round(df['covered'].mean(), 3)}")
    df.to_csv("data/processed/features.csv", index=False)
    print("Saved to data/processed/features.csv")
