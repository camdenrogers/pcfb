"""High-level jobs: ingest from CFBD and retrain."""
from __future__ import annotations

import logging
import threading
from collections.abc import Iterable

from sqlalchemy import select

from .cfbd_client import CFBDClient
from .config import current_season, settings
from .db import SessionLocal
from .ingest import ingest_season
from .model.service import train
from .models import ModelRun, TeamSeason

log = logging.getLogger(__name__)

_refresh_lock = threading.Lock()


class RefreshInProgress(RuntimeError):
    pass


def target_seasons() -> list[int]:
    cur = current_season()
    return list(range(cur - settings.history_seasons + 1, cur + 1))


def ingest(seasons: Iterable[int]) -> list[dict]:
    out = []
    with SessionLocal() as session, CFBDClient() as client:
        for season in seasons:
            out.append(ingest_season(session, client, season))
    return out


def refresh(full: bool = False) -> dict:
    """Ingest the current season (and any missing history seasons), then retrain.

    Historical seasons don't change, so they're fetched only once unless ``full=True``.
    """
    if not _refresh_lock.acquire(blocking=False):
        raise RefreshInProgress("A refresh is already running")
    try:
        with SessionLocal() as session:
            have = set(session.scalars(select(TeamSeason.season).distinct()))
        cur = current_season()
        to_fetch = [s for s in target_seasons() if full or s == cur or s not in have]
        ingested = ingest(to_fetch)
        with SessionLocal() as session:
            run = train(session)
            return {"ingested": ingested, "model_run_id": run.id, "season": run.season,
                    "through": run.through_label, "metrics": run.metrics}
    finally:
        _refresh_lock.release()


def has_model() -> bool:
    with SessionLocal() as session:
        return session.scalar(select(ModelRun.id).where(ModelRun.is_active.is_(True)).limit(1)) is not None


def is_refreshing() -> bool:
    return _refresh_lock.locked()
