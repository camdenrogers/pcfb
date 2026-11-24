"""Command line entry points.

    python -m app.cli refresh                 # ingest current season (+ missing history) and train
    python -m app.cli ingest --seasons 2023 2024 2025
    python -m app.cli train
    python -m app.cli backtest
    python -m app.cli tune --apply            # grid-search hyperparameters on walk-forward MAE
    python -m app.cli predict Georgia "Ohio State"
"""
from __future__ import annotations

import argparse
import json
import logging

from sqlalchemy import func, select


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="pcfb")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    r = sub.add_parser("refresh")
    r.add_argument("--full", action="store_true", help="re-fetch all history seasons too")
    i = sub.add_parser("ingest")
    i.add_argument("--seasons", type=int, nargs="*", help="defaults to the last HISTORY_SEASONS seasons")
    sub.add_parser("train")
    sub.add_parser("backtest")
    t = sub.add_parser("tune")
    t.add_argument("--apply", action="store_true", help="retrain with the best parameters")
    pr = sub.add_parser("predict")
    pr.add_argument("team_a")
    pr.add_argument("team_b")
    args = p.parse_args(argv)

    from . import pipeline
    from .db import SessionLocal, init_db
    from .model import service
    from .model.ratings import ModelParams, backtest, tune

    init_db()
    if args.cmd == "init-db":
        print("Tables created.")
    elif args.cmd == "refresh":
        _print(pipeline.refresh(full=args.full))
    elif args.cmd == "ingest":
        _print(pipeline.ingest(args.seasons or pipeline.target_seasons()))
    elif args.cmd == "train":
        with SessionLocal() as s:
            run = service.train(s)
            _print({"run_id": run.id, "season": run.season, "through": run.through_label,
                    "hfa": run.hfa, "sigma": run.sigma, "metrics": run.metrics})
    elif args.cmd in ("backtest", "tune"):
        with SessionLocal() as s:
            data = [d for d, _, _ in service.load_all(s)]
            base = service.active_params(s) or ModelParams()
        evals = [d.season for d in data[1:] if d.games][-service.BACKTEST_SEASONS:]
        if not evals:
            raise SystemExit("Need at least two ingested seasons to backtest.")
        if args.cmd == "backtest":
            _print({"params": base.to_dict(), "seasons": evals, **backtest(data, base, evals).to_dict()})
        else:
            best, res, _ = tune(data, base, eval_seasons=evals,
                                progress=lambda i, n, c, mae: print(f"[{i}/{n}] {c} MAE={mae:.3f}"))
            _print({"best_params": best.to_dict(), **res.to_dict()})
            if args.apply:
                with SessionLocal() as s:
                    run = service.train(s, params=best)
                print(f"Retrained with tuned params -> model run {run.id}")
    elif args.cmd == "predict":
        from .models import Team

        with SessionLocal() as s:
            model = service.get_active_model(s)
            if model is None:
                raise SystemExit("No trained model. Run `refresh` first.")
            ids = []
            for name in (args.team_a, args.team_b):
                tid = next((t for t, v in model.teams.items() if v["school"].lower() == name.lower()), None)
                if tid is None:
                    tid = s.scalar(select(Team.id).where(func.lower(Team.school) == name.lower()))
                if tid is None or tid not in model.teams:
                    raise SystemExit(f"Unknown FBS team: {name}")
                ids.append(tid)
            res = service.predict(model, *ids)
            print(f"{res['team_a']['school']} {res['team_a']['projected_points']} - "
                  f"{res['team_b']['projected_points']} {res['team_b']['school']}  |  {res['spread']['display']}  |  "
                  f"{res['team_a']['school']} win prob {res['team_a']['win_probability']:.0%}")


if __name__ == "__main__":
    main()
