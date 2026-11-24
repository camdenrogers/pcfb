"""Glue between Postgres and the pure-math model: load data, train, persist, predict."""
from __future__ import annotations

import logging
import statistics
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..models import Game, ModelRun, Team, TeamRating, TeamSeason, TeamTalent
from .ratings import (
    DEFAULT_SIGMA,
    FCS_KEY,
    GameRecord,
    ModelParams,
    Ratings,
    SeasonData,
    backtest,
    fit_chain,
    win_probability,
)

log = logging.getLogger(__name__)

MISSING_TALENT_Z = -1.0  # FBS teams with no talent composite (usually new programs)
BACKTEST_SEASONS = 2


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def _week_anchor(first: date) -> date:
    """The Tuesday on/before the first game, so model 'weeks' run Tue-Mon like real CFB weeks."""
    return first - timedelta(days=(first.weekday() - 1) % 7)


def load_season(session: Session, season: int) -> tuple[SeasonData, datetime | None, str | None] | None:
    fbs = set(session.scalars(select(TeamSeason.team_id).where(TeamSeason.season == season)))
    if not fbs:
        return None

    rows = session.scalars(
        select(Game).where(
            Game.season == season,
            Game.completed.is_(True),
            Game.home_points.is_not(None),
            Game.away_points.is_not(None),
        )
    ).all()
    dates = [g.start_date.date() for g in rows if g.start_date]
    anchor = _week_anchor(min(dates)) if dates else None

    games: list[GameRecord] = []
    for g in rows:
        h = g.home_id if g.home_id in fbs else FCS_KEY
        a = g.away_id if g.away_id in fbs else FCS_KEY
        if h == a:
            continue  # FCS vs FCS (or bad data)
        if anchor and g.start_date:
            order = float((g.start_date.date() - anchor).days // 7)
        else:
            order = float((g.week or 0) + (20 if g.season_type == "postseason" else 0))
        games.append(GameRecord(season, order, h, a, float(g.home_points), float(g.away_points), bool(g.neutral_site)))

    # talent composite -> z-score among FBS teams
    names = dict(session.execute(select(Team.school, Team.id).where(Team.id.in_(fbs))).all())
    talent = {names[t.team]: t.talent for t in session.scalars(select(TeamTalent).where(TeamTalent.season == season)) if t.team in names}
    talent_z: dict[int, float] = {}
    if len(talent) >= 10:
        mean = statistics.fmean(talent.values())
        sd = statistics.pstdev(talent.values()) or 1.0
        talent_z = {t: (talent[t] - mean) / sd if t in talent else MISSING_TALENT_Z for t in fbs}

    latest = max((g for g in rows if g.start_date), key=lambda g: g.start_date, default=None)
    through_date = latest.start_date if latest else None
    if latest is None:
        label = "Preseason"
    elif latest.season_type == "postseason":
        label = "Postseason"
    else:
        label = f"Week {latest.week}"
    return SeasonData(season, sorted(fbs), games, talent_z), through_date, label


def load_all(session: Session) -> list[tuple[SeasonData, datetime | None, str | None]]:
    seasons = sorted(session.scalars(select(TeamSeason.season).distinct()))
    out = []
    for s in seasons:
        loaded = load_season(session, s)
        if loaded:
            out.append(loaded)
    return out


# --------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------

def train(session: Session, params: ModelParams | None = None, run_backtest: bool = True) -> ModelRun:
    loaded = load_all(session)
    if not loaded:
        raise RuntimeError("No data ingested yet. Run `python -m app.cli ingest` (or `refresh`) first.")
    data = [d for d, _, _ in loaded]
    current, through_date, through_label = loaded[-1]
    params = params or active_params(session) or ModelParams()

    finals = fit_chain(data, params)
    ratings = finals[current.season]

    metrics: dict = {}
    sigma = DEFAULT_SIGMA
    if run_backtest:
        eval_seasons = [d.season for d in data[1:] if d.games][-BACKTEST_SEASONS:]
        if eval_seasons:
            bt = backtest(data, params, eval_seasons)
            metrics = {"backtest": bt.to_dict(), "backtest_seasons": eval_seasons}
            if bt.n >= 100:
                sigma = bt.rmse

    # Center offense/defense on the FBS average for readability. Shifting all offense by c_o
    # and all defense by c_d leaves predictions unchanged if mu absorbs (c_o - c_d).
    fbs = current.teams
    c_o = statistics.fmean(ratings.offense[t] for t in fbs)
    c_d = statistics.fmean(ratings.defense[t] for t in fbs)
    mu = ratings.mu + c_o - c_d

    run = ModelRun(
        season=current.season,
        through_date=through_date,
        through_label=through_label,
        games_used=len(current.games),
        mu=mu,
        hfa=ratings.hfa,
        sigma=sigma,
        params=params.to_dict(),
        metrics=metrics,
        is_active=True,
    )
    session.execute(update(ModelRun).values(is_active=False))
    session.add(run)
    session.flush()

    rows = []
    for t in fbs:
        off = ratings.offense[t] - c_o
        dfn = ratings.defense[t] - c_d
        rows.append({"team_id": t, "offense": off, "defense": dfn, "rating": off + dfn,
                     "games_played": ratings.games_played.get(t, 0)})
    rows.sort(key=lambda r: r["rating"], reverse=True)
    session.add_all(TeamRating(run_id=run.id, rank=i, **r) for i, r in enumerate(rows, 1))
    session.commit()
    invalidate_cache()
    log.info("Trained model run %s: season %s through %s (%s games), hfa=%.2f sigma=%.2f",
             run.id, run.season, through_label, run.games_used, run.hfa, run.sigma)
    return run


def active_params(session: Session) -> ModelParams | None:
    run = session.scalar(select(ModelRun).where(ModelRun.is_active.is_(True)).order_by(ModelRun.id.desc()).limit(1))
    return ModelParams.from_dict(run.params) if run else None


# --------------------------------------------------------------------------
# Serving
# --------------------------------------------------------------------------

@dataclass
class LoadedModel:
    run: ModelRun
    ratings: Ratings
    teams: dict[int, dict]  # team_id -> team info + ratings


_cache: dict[str, LoadedModel] = {}
_cache_lock = threading.Lock()


def invalidate_cache() -> None:
    with _cache_lock:
        _cache.clear()


def get_active_model(session: Session) -> LoadedModel | None:
    run_id = session.scalar(select(func.max(ModelRun.id)).where(ModelRun.is_active.is_(True)))
    if run_id is None:
        return None
    with _cache_lock:
        cached = _cache.get("active")
        if cached and cached.run.id == run_id:
            return cached

    run = session.get(ModelRun, run_id)
    teams: dict[int, dict] = {}
    for tr, team in session.execute(
        select(TeamRating, Team).join(Team, Team.id == TeamRating.team_id).where(TeamRating.run_id == run_id)
    ).all():
        teams[team.id] = {
            "id": team.id,
            "school": team.school,
            "mascot": team.mascot,
            "abbreviation": team.abbreviation,
            "conference": team.conference,
            "color": team.color,
            "alt_color": team.alt_color,
            "logo": team.logo,
            "offense": tr.offense,
            "defense": tr.defense,
            "rating": tr.rating,
            "rank": tr.rank,
            "games_played": tr.games_played,
        }
    ratings = Ratings(
        mu=run.mu,
        hfa=run.hfa,
        offense={t: v["offense"] for t, v in teams.items()},
        defense={t: v["defense"] for t, v in teams.items()},
    )
    loaded = LoadedModel(run=run, ratings=ratings, teams=teams)
    with _cache_lock:
        _cache["active"] = loaded
    return loaded


def _round_half(x: float) -> float:
    return round(x * 2) / 2


def predict(model: LoadedModel, team_a: int, team_b: int) -> dict:
    a, b = model.teams[team_a], model.teams[team_b]
    pa, pb = model.ratings.project(team_a, team_b, home=None)
    margin = pa - pb
    p_a = win_probability(margin, model.run.sigma)

    line = _round_half(abs(margin))
    if line == 0:
        favorite, display = None, "Pick'em"
    else:
        favorite = a if margin > 0 else b
        display = f"{favorite['school']} -{line:g}"

    return {
        "team_a": {**a, "projected_points": round(pa, 1), "win_probability": round(p_a, 4)},
        "team_b": {**b, "projected_points": round(pb, 1), "win_probability": round(1 - p_a, 4)},
        "neutral_site": True,
        "margin": round(margin, 2),
        "spread": {
            "favorite_id": favorite["id"] if favorite else None,
            "line": -line if favorite else 0.0,
            "team_a_line": _round_half(-margin),
            "display": display,
        },
        "total": round(pa + pb, 1),
        "generated_at": datetime.now(timezone.utc),
    }
