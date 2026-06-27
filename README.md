# PCFB

A college football spread-prediction app. The Python API pulls game data from the College Football Data API, engineers features, trains an ML model, and exposes endpoints for on-demand predictions. The Next.js UI consumes the API.

---

## API (`pcfb-api`)

### Technical Overview

The API is a **FastAPI** app that predicts whether the home team will cover the spread in a given FBS game. The pipeline has three stages:

1. **Data ingestion** — `cfbd_client.py` fetches game results, betting lines, and SP+/Elo ratings from [collegefootballdata.com](https://collegefootballdata.com) for the requested seasons.
2. **Feature engineering** — `ml/features.py` joins those datasets, computes `spRatingDiff`, `eloDiff`, and a binary `covered` target (did the home team beat the spread?), and writes the result to `data/processed/features.csv`.
3. **Model training** — `ml/train.py` evaluates a Logistic Regression and a Gradient Boosting Classifier (both via scikit-learn pipelines with `StandardScaler`) using 5-fold CV and saves the better-performing model to `models/saved/model.pkl`.

Features used at inference time:

| Feature | Description |
|---|---|
| `spRatingDiff` | Home SP+ rating minus away SP+ rating |
| `eloDiff` | Home pregame Elo minus away pregame Elo |
| `isNeutral` | 1 if played at a neutral site |
| `spread` | Vegas consensus spread (negative = home favored) |
| `overUnder` | Vegas consensus over/under |
| `homeSPOffense` / `awaySPOffense` | SP+ offensive ratings |
| `homeSPDefense` / `awaySPDefense` | SP+ defensive ratings |

### Prerequisites

- Python 3.13+
- A free API key from [collegefootballdata.com](https://collegefootballdata.com)

### Setup

```bash
cd pcfb-api
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic pydantic-settings \
    pandas scikit-learn joblib requests
```

Create a `.env` file in `pcfb-api/`:

```
CFBD_API_KEY=your_key_here
```

### Build the model

Fetch historical data and train before serving predictions. Run these from the `pcfb-api/` directory:

```bash
# Download game data and build features.csv (2021–2023 by default)
python app/ml/features.py

# Train and save the best model to models/saved/model.pkl
python app/ml/train.py
```

### Running the API

```bash
cd pcfb-api
source venv/bin/activate
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000). Interactive docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

### Endpoints

#### `GET /health`
Returns `{"status": "ok"}` — use to confirm the server is up.

---

#### `POST /api/predict`
Predict whether the home team will cover the spread.

**Request body:**
```json
{
  "homeTeam": "Alabama",
  "awayTeam": "Georgia",
  "spread": -7.5,
  "overUnder": 52.0,
  "homeSPRating": 25.3,
  "awaySPRating": 22.1,
  "homeSPOffense": 38.5,
  "awaySPOffense": 35.2,
  "homeSPDefense": 12.1,
  "awaySPDefense": 14.3,
  "homePregameElo": 1750,
  "awayPregameElo": 1700,
  "isNeutral": 0
}
```

**Response:**
```json
{
  "homeTeam": "Alabama",
  "awayTeam": "Georgia",
  "spread": -7.5,
  "predictedCover": true,
  "confidence": 0.613
}
```

`predictedCover: true` means the model expects the home team to cover. `confidence` is the model's probability for the predicted outcome (0.5–1.0).

---

#### `POST /api/refresh`
Triggers a background job to re-fetch data from the CFBD API and rebuild `features.csv`. Returns immediately; poll `/api/status` for progress.

---

#### `POST /api/retrain`
Triggers a background job to retrain the model on the current `features.csv`. Returns immediately; poll `/api/status` for progress.

---

#### `GET /api/status`
Returns the current state of the refresh and retrain background jobs.

```json
{
  "refresh": {"status": "success", "last_run": "2025-09-01T12:00:00", "message": "Features refreshed successfully"},
  "retrain": {"status": "idle",    "last_run": null,                    "message": null}
}
```

`status` is one of `idle`, `running`, `success`, or `error`.

---

## Running the UI

The UI is a Next.js app located in [pcfb-ui/](pcfb-ui/).

### Prerequisites

- Node.js (v18+)
- npm

### Setup

```bash
cd pcfb-ui
npm install
```

### Development

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

### Production

```bash
npm run build
npm run start
```

## Project Structure

```
pcfb-ui/src/
├── app/
│   ├── page.tsx              # Root — redirects to /control
│   ├── layout.tsx            # Root layout (fonts, global styles)
│   ├── globals.css
│   ├── (app)/                # Route group for the main app shell
│   │   ├── layout.tsx        # Shared layout: sidebar + site header
│   │   ├── control/          # Control Center page (/control)
│   │   └── predictions/      # Weekly Predictions page (/predictions)
│   └── dashboard/            # Standalone dashboard page
├── components/
│   ├── app-sidebar.tsx       # Primary navigation sidebar
│   ├── site-header.tsx       # Top header bar
│   ├── nav-main.tsx          # Main nav links
│   ├── nav-documents.tsx     # Documents section in sidebar
│   ├── nav-secondary.tsx     # Secondary nav (settings, help)
│   ├── nav-user.tsx          # User profile in sidebar footer
│   ├── chart-area-interactive.tsx  # Recharts area chart component
│   ├── data-table.tsx        # TanStack Table data table
│   ├── section-cards.tsx     # Summary/stat card grid
│   └── ui/                   # shadcn/ui primitives (button, card, etc.)
├── hooks/
│   └── use-mobile.ts         # Responsive breakpoint hook
└── lib/
    └── utils.ts              # Tailwind class merge utility (cn)
```

### Key technologies

- **Next.js 16** with the App Router
- **shadcn/ui** for UI components (built on Radix UI + Tailwind CSS v4)
- **Recharts** for charts
- **TanStack Table** for data tables
- **dnd-kit** for drag-and-drop
