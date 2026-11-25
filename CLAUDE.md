# CLAUDE.md

Guidance for working in this repo. See [README.md](README.md) for architecture/model details — this file is the quick reference for running things.

## What this is

FastAPI + Postgres + React/Vite app that fits an opponent-adjusted offense/defense rating model on CollegeFootballData.com (CFBD) data and predicts neutral-site spreads between FBS teams. Backend: `backend/app/`. Frontend: `frontend/src/`.

## Running the stack

```bash
cp .env.example .env         # fill in CFBD_API_KEY (free: https://collegefootballdata.com/key)
docker compose up --build -d
docker compose logs -f backend   # watch the first-run ingest + train
```

- backend: http://localhost:8000 (docs at `/docs`)
- frontend: http://localhost:8080
- postgres: localhost:5432 (`pcfb`/`pcfb` by default)

On first start, if `AUTO_BOOTSTRAP=true` (default) and no model exists yet, the backend ingests the last `HISTORY_SEASONS` seasons (default 4) from CFBD and trains — usually well under a minute. Data and the trained model persist in the `pgdata` volume across restarts, so a plain `docker compose up -d` after the first run won't re-ingest.

To force a re-ingest + retrain: `docker compose exec backend python -m app.cli refresh` (add `--full` to also re-fetch history seasons, not just the current one).

## Tests

The backend image doesn't include `tests/` or dev dependencies (it's a deploy image), so run tests in a local venv, not in the container:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

12 tests across `tests/test_normalize.py` (CFBD camelCase/snake_case field handling) and `tests/test_ratings.py` (the pure-numpy rating model). No DB needed — these test `normalize.py` and `model/ratings.py` in isolation.

## CLI commands

Run via `docker compose exec backend python -m app.cli <cmd>` against the running stack, or locally (same venv as tests) with `DATABASE_URL`/`CFBD_API_KEY` exported and pointed at `localhost:5432`.

```bash
python -m app.cli init-db                         # create tables only
python -m app.cli refresh [--full]                # ingest current season (+ missing history) and retrain
python -m app.cli ingest --seasons 2023 2024 2025 # ingest specific seasons
python -m app.cli train                           # retrain from what's already in Postgres
python -m app.cli backtest                        # walk-forward MAE/RMSE/bias/winner-accuracy of the active params
python -m app.cli tune [--apply]                   # grid-search hyperparameters on walk-forward MAE; --apply retrains with the winner
python -m app.cli predict Georgia "Ohio State"    # spread + win prob by team name
```

## Key endpoints

`/api/health`, `/api/model` (active run + backtest metrics), `/api/teams`, `/api/rankings?limit=25`, `/api/predict?team_a={id}&team_b={id}`, `POST /api/admin/refresh` (needs `X-Admin-Token` matching `ADMIN_TOKEN` in `.env`).

## Platform

Runs on k3s on GCP. Architecture, costs and the full runbook are in [docs/platform.md](docs/platform.md).

```bash
./scripts/tunnel.sh                         # IAP tunnel to the Kubernetes API; leave running
./scripts/kubeconfig.sh                     # write ~/.kube/pcfb.yaml
export KUBECONFIG=~/.kube/pcfb.yaml
./scripts/tf.sh plan                        # terraform in infra/platform, tokens from Secret Manager
terraform -chdir=infra/cluster plan         # ArgoCD; needs the tunnel
./scripts/sync-secrets.sh neon test|prod    # copy Neon URL into Secret Manager
./scripts/sync-secrets.sh tunnel            # copy Cloudflare tunnel token into Secret Manager
./scripts/destroy-all.sh --dry-run          # preview a full teardown
gh workflow run promote-prod.yml --ref main # promote test's SHA; waits for approval
```

- `main` is protected: change it through a PR. Merging deploys to test and applies `infra/platform`.
- `env/test` and `env/prod` are written by CI. ArgoCD deploys from them.
- The repo, CI logs and PR comments are public. Never send secrets or masking commands to a file that CI posts.

## Local machine

- Apple Silicon (M2) Mac, zsh. Don't use Homebrew: the copy in `/usr/local` is the x86 build. Install official darwin-arm64 binaries into `~/.local/bin`, with checksums verified.
- gcloud is at `~/google-cloud-sdk/bin` and may not be on PATH in non-interactive shells.
- Build images for `linux/amd64`.

## Notes

- `.env` is gitignored — never commit it (it holds `CFBD_API_KEY` and `ADMIN_TOKEN`).
- `HISTORY_SEASONS` and `REFRESH_INTERVAL_HOURS` (hours between auto re-ingest of the current season; `0` disables) are the main knobs in `.env`.
- CFBD field names were compared with `normalize.py` on 2026-11-25, using raw 2025 regular-season games, teams and talent: no missing keys and no rejected rows.
