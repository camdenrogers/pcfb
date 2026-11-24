from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TeamOut(BaseModel):
    id: int
    school: str
    mascot: str | None = None
    abbreviation: str | None = None
    conference: str | None = None
    color: str | None = None
    alt_color: str | None = None
    logo: str | None = None
    offense: float
    defense: float
    rating: float
    rank: int
    games_played: int


class TeamProjection(TeamOut):
    projected_points: float
    win_probability: float


class Spread(BaseModel):
    favorite_id: int | None
    line: float  # favorite's line, e.g. -7.5 (0 for a pick'em)
    team_a_line: float  # line from team A's perspective (negative = A favored)
    display: str


class ModelInfo(BaseModel):
    ready: bool
    refreshing: bool = False
    run_id: int | None = None
    trained_at: datetime | None = None
    season: int | None = None
    through: str | None = None
    through_date: datetime | None = None
    games_used: int | None = None
    home_field_advantage: float | None = None
    league_avg_points: float | None = None
    sigma: float | None = None
    params: dict | None = None
    metrics: dict | None = None


class Prediction(BaseModel):
    team_a: TeamProjection
    team_b: TeamProjection
    neutral_site: bool
    margin: float  # team A points minus team B points
    spread: Spread
    total: float
    generated_at: datetime
    model: ModelInfo
