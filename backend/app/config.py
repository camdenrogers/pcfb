"""Runtime configuration, read from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://pcfb:pcfb@localhost:5432/pcfb")
    cfbd_api_key: str = os.getenv("CFBD_API_KEY", "")
    cfbd_base_url: str = os.getenv("CFBD_BASE_URL", "https://api.collegefootballdata.com")
    admin_token: str = os.getenv("ADMIN_TOKEN", "")
    # How many seasons (including the current one) to ingest and chain through the model.
    history_seasons: int = int(os.getenv("HISTORY_SEASONS", "4"))
    # If > 0, re-ingest the current season and retrain every N hours while the API runs.
    refresh_interval_hours: float = float(os.getenv("REFRESH_INTERVAL_HOURS", "0"))
    # On startup, ingest + train automatically if no model exists yet.
    auto_bootstrap: bool = _bool("AUTO_BOOTSTRAP", True)
    cors_origins: list[str] = field(default_factory=lambda: _list("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"))


settings = Settings()


def current_season(today: date | None = None) -> int:
    """College football seasons start in late August; Jan bowl games belong to the prior season."""
    today = today or date.today()
    return today.year if today.month >= 8 else today.year - 1
