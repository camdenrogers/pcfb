"""Postgres schema (SQLAlchemy ORM)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Team(Base):
    """Every team CFBD has told us about (FBS membership is tracked per season in TeamSeason)."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    school: Mapped[str] = mapped_column(String(120), index=True)
    mascot: Mapped[str | None] = mapped_column(String(120))
    abbreviation: Mapped[str | None] = mapped_column(String(20))
    conference: Mapped[str | None] = mapped_column(String(80))
    classification: Mapped[str | None] = mapped_column(String(20))
    color: Mapped[str | None] = mapped_column(String(20))
    alt_color: Mapped[str | None] = mapped_column(String(20))
    logo: Mapped[str | None] = mapped_column(Text)


class TeamSeason(Base):
    __tablename__ = "team_seasons"

    season: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    conference: Mapped[str | None] = mapped_column(String(80))


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (Index("ix_games_season_completed", "season", "completed"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    season: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int | None] = mapped_column(Integer)
    season_type: Mapped[str] = mapped_column(String(20), default="regular")
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    neutral_site: Mapped[bool] = mapped_column(Boolean, default=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    home_id: Mapped[int | None] = mapped_column(Integer, index=True)
    home_team: Mapped[str | None] = mapped_column(String(120))
    home_points: Mapped[int | None] = mapped_column(Integer)
    away_id: Mapped[int | None] = mapped_column(Integer, index=True)
    away_team: Mapped[str | None] = mapped_column(String(120))
    away_points: Mapped[int | None] = mapped_column(Integer)


class TeamTalent(Base):
    """247 Sports team talent composite (keyed by school name, as CFBD returns it)."""

    __tablename__ = "team_talent"

    season: Mapped[int] = mapped_column(Integer, primary_key=True)
    team: Mapped[str] = mapped_column(String(120), primary_key=True)
    talent: Mapped[float] = mapped_column(Float)


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    season: Mapped[int] = mapped_column(Integer)
    through_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    through_label: Mapped[str | None] = mapped_column(String(40))
    games_used: Mapped[int] = mapped_column(Integer, default=0)
    mu: Mapped[float] = mapped_column(Float)
    hfa: Mapped[float] = mapped_column(Float)
    sigma: Mapped[float] = mapped_column(Float)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class TeamRating(Base):
    __tablename__ = "team_ratings"

    run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id", ondelete="CASCADE"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    offense: Mapped[float] = mapped_column(Float)  # points scored above FBS average
    defense: Mapped[float] = mapped_column(Float)  # points prevented vs FBS average (higher = better)
    rating: Mapped[float] = mapped_column(Float)  # offense + defense: neutral-site margin vs average FBS team
    rank: Mapped[int] = mapped_column(Integer)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
