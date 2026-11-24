"""Turn raw CollegeFootballData.com JSON into rows for our tables.

CFBD's v2 API returns camelCase keys (``homeTeam``) while older versions
returned snake_case (``home_team``); every accessor here accepts both.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def pick(d: dict, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def parse_dt(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _int(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def normalize_team(raw: dict) -> dict | None:
    team_id = _int(pick(raw, "id"))
    school = pick(raw, "school")
    if team_id is None or not school:
        return None
    logos = pick(raw, "logos", default=[]) or []
    return {
        "id": team_id,
        "school": school,
        "mascot": pick(raw, "mascot"),
        "abbreviation": pick(raw, "abbreviation"),
        "conference": pick(raw, "conference"),
        "classification": pick(raw, "classification", default="fbs"),
        "color": pick(raw, "color"),
        "alt_color": pick(raw, "alternateColor", "alt_color"),
        "logo": logos[0] if logos else None,
    }


def normalize_game(raw: dict) -> dict | None:
    game_id = _int(pick(raw, "id"))
    season = _int(pick(raw, "season"))
    if game_id is None or season is None:
        return None
    home_points = _int(pick(raw, "homePoints", "home_points"))
    away_points = _int(pick(raw, "awayPoints", "away_points"))
    completed = pick(raw, "completed")
    if completed is None:
        completed = home_points is not None and away_points is not None
    return {
        "id": game_id,
        "season": season,
        "week": _int(pick(raw, "week")),
        "season_type": pick(raw, "seasonType", "season_type", default="regular"),
        "start_date": parse_dt(pick(raw, "startDate", "start_date")),
        "neutral_site": bool(pick(raw, "neutralSite", "neutral_site", default=False)),
        "completed": bool(completed),
        "home_id": _int(pick(raw, "homeId", "home_id")),
        "home_team": pick(raw, "homeTeam", "home_team"),
        "home_points": home_points,
        "away_id": _int(pick(raw, "awayId", "away_id")),
        "away_team": pick(raw, "awayTeam", "away_team"),
        "away_points": away_points,
    }


def normalize_talent(raw: dict, season: int) -> dict | None:
    team = pick(raw, "team", "school")
    try:
        talent = float(pick(raw, "talent"))
    except (TypeError, ValueError):
        return None
    if not team:
        return None
    return {"season": _int(pick(raw, "year", "season")) or season, "team": team, "talent": talent}
