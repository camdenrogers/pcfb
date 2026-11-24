"""PCFB REST API."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import pipeline
from .config import settings
from .db import get_session, init_db
from .model.service import LoadedModel, get_active_model, predict
from .schemas import ModelInfo, Prediction, TeamOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("pcfb")


async def _safe_refresh(reason: str) -> None:
    try:
        log.info("Starting refresh (%s)", reason)
        result = await run_in_threadpool(pipeline.refresh)
        log.info("Refresh complete: run %s through %s", result["model_run_id"], result["through"])
    except pipeline.RefreshInProgress:
        log.info("Refresh already in progress; skipping (%s)", reason)
    except Exception:
        log.exception("Refresh failed (%s)", reason)


async def _refresh_loop(hours: float) -> None:
    while True:
        await asyncio.sleep(hours * 3600)
        await _safe_refresh("scheduled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(init_db)
    tasks: list[asyncio.Task] = []
    if settings.auto_bootstrap and settings.cfbd_api_key and not await run_in_threadpool(pipeline.has_model):
        tasks.append(asyncio.create_task(_safe_refresh("bootstrap")))
    if settings.refresh_interval_hours > 0 and settings.cfbd_api_key:
        tasks.append(asyncio.create_task(_refresh_loop(settings.refresh_interval_hours)))
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="PCFB – College Football Spread Model", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _model_info(model: LoadedModel | None) -> ModelInfo:
    if model is None:
        return ModelInfo(ready=False, refreshing=pipeline.is_refreshing())
    r = model.run
    return ModelInfo(
        ready=True,
        refreshing=pipeline.is_refreshing(),
        run_id=r.id,
        trained_at=r.created_at,
        season=r.season,
        through=r.through_label,
        through_date=r.through_date,
        games_used=r.games_used,
        home_field_advantage=round(r.hfa, 2),
        league_avg_points=round(r.mu, 2),
        sigma=round(r.sigma, 2),
        params=r.params,
        metrics=r.metrics,
    )


def _require_model(session: Session) -> LoadedModel:
    model = get_active_model(session)
    if model is None:
        raise HTTPException(503, "Model not trained yet. Ingest data and train (see README).")
    return model


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/model", response_model=ModelInfo)
def model_info(session: Session = Depends(get_session)) -> ModelInfo:
    return _model_info(get_active_model(session))


@app.get("/api/teams", response_model=list[TeamOut])
def teams(session: Session = Depends(get_session)) -> list[dict]:
    model = get_active_model(session)
    if model is None:
        return []
    return sorted(model.teams.values(), key=lambda t: t["school"])


@app.get("/api/rankings", response_model=list[TeamOut])
def rankings(limit: int = Query(25, ge=1, le=200), session: Session = Depends(get_session)) -> list[dict]:
    model = _require_model(session)
    return sorted(model.teams.values(), key=lambda t: t["rank"])[:limit]


@app.get("/api/predict", response_model=Prediction)
def predict_matchup(
    team_a: int = Query(..., description="CFBD team id"),
    team_b: int = Query(..., description="CFBD team id"),
    session: Session = Depends(get_session),
) -> dict:
    model = _require_model(session)
    if team_a == team_b:
        raise HTTPException(400, "Pick two different teams")
    missing = [t for t in (team_a, team_b) if t not in model.teams]
    if missing:
        raise HTTPException(404, f"Unknown FBS team id(s): {missing}")
    return {**predict(model, team_a, team_b), "model": _model_info(model)}


@app.post("/api/admin/refresh")
async def admin_refresh(x_admin_token: str | None = Header(default=None)) -> dict:
    if not settings.admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(401, "Invalid or missing X-Admin-Token")
    if pipeline.is_refreshing():
        raise HTTPException(409, "A refresh is already running")
    task = asyncio.create_task(_safe_refresh("admin"))
    _background.add(task)  # keep a reference so the task isn't garbage-collected
    task.add_done_callback(_background.discard)
    return {"status": "started"}


_background: set[asyncio.Task] = set()
