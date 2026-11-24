"""Load CFBD data into Postgres (idempotent upserts)."""
from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .cfbd_client import CFBDClient
from .models import Game, Team, TeamSeason, TeamTalent
from .normalize import normalize_game, normalize_talent, normalize_team

log = logging.getLogger(__name__)


def upsert(session: Session, model, rows: Iterable[dict], pk: list[str], chunk: int = 1000) -> int:
    rows = list(rows)
    # de-duplicate on primary key (last one wins) so a single statement never conflicts with itself
    rows = list({tuple(r[c] for c in pk): r for r in rows}.values())
    for i in range(0, len(rows), chunk):
        batch = rows[i : i + chunk]
        stmt = pg_insert(model).values(batch)
        update_cols = {c.name: stmt.excluded[c.name] for c in model.__table__.columns if c.name not in pk}
        if update_cols:
            stmt = stmt.on_conflict_do_update(index_elements=pk, set_=update_cols)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=pk)
        session.execute(stmt)
    return len(rows)


def ingest_season(session: Session, client: CFBDClient, season: int) -> dict:
    teams = [t for t in (normalize_team(r) for r in client.fbs_teams(season)) if t]
    upsert(session, Team, teams, ["id"])
    upsert(session, TeamSeason, ({"season": season, "team_id": t["id"], "conference": t["conference"]} for t in teams),
           ["season", "team_id"])

    games: list[dict] = []
    for season_type in ("regular", "postseason"):
        games.extend(g for g in (normalize_game(r) for r in client.games(season, season_type)) if g)
    upsert(session, Game, games, ["id"])

    talent = [t for t in (normalize_talent(r, season) for r in client.talent(season)) if t]
    upsert(session, TeamTalent, talent, ["season", "team"])

    session.commit()
    counts = {
        "season": season,
        "fbs_teams": len(teams),
        "games": len(games),
        "completed_games": sum(1 for g in games if g["completed"]),
        "talent_rows": len(talent),
    }
    log.info("Ingested %s", counts)
    return counts
