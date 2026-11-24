"""PCFB spread model: opponent-adjusted offense/defense ratings.

The model treats every team's points in a game as

    points(team vs opp) = mu + offense[team] - defense[opp] +/- hfa/2

where ``mu`` is the league-average scoring level, ``offense`` is how many
points a team scores above average, ``defense`` is how many points a team
*prevents* relative to average (higher is better) and ``hfa`` is home-field
advantage expressed as a margin (home gets +hfa/2, away gets -hfa/2; 0 on a
neutral site).

Ratings are fit by weighted ridge regression toward a *preseason prior*:

    minimise  sum_i w_i (points_i - x_i . beta)^2  +  sum_j lambda_j (beta_j - prior_j)^2

* ``w_i`` decays exponentially with how long ago the game was played
  (``half_life_weeks``), so recent form matters more.
* Lopsided scores are dampened past ``blowout_cap`` so running up the score
  against a weak opponent doesn't inflate a rating.
* ``prior_j`` comes from last season's final rating (regressed by
  ``carryover``) plus a roster-talent adjustment (247 Sports talent
  composite z-score x ``talent_coef``). ``prior_weight`` is roughly how many
  games of evidence the prior is worth, so it dominates in September and
  fades as real results accumulate.
* All non-FBS opponents are pooled into a single "FCS" pseudo-team.

Everything in this module is pure Python + numpy so it can be unit tested and
re-used without a database.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, fields
from typing import Iterable, Mapping, Sequence

import numpy as np

FCS_KEY = -1  # pseudo-team id for every non-FBS opponent
DEFAULT_SIGMA = 16.0  # fallback std-dev of margin errors (points)


@dataclass(frozen=True)
class GameRecord:
    season: int
    order: float  # chronological index in weeks (larger = later)
    home: int
    away: int
    home_points: float
    away_points: float
    neutral: bool = False

    @property
    def margin(self) -> float:
        return self.home_points - self.away_points


@dataclass(frozen=True)
class ModelParams:
    prior_weight: float = 3.0  # strength of preseason prior, ~ games of evidence
    carryover: float = 0.6  # fraction of last season's rating carried forward
    talent_coef: float = 4.0  # net-rating points per 1 SD of roster talent
    half_life_weeks: float = 10.0  # recency decay of game weights
    blowout_cap: float = 28.0  # margin beyond which scoring is dampened
    blowout_excess: float = 0.3  # fraction of margin beyond the cap that counts
    league_avg_points: float = 28.0  # prior for mu
    hfa_prior: float = 2.5  # prior for home-field advantage (points of margin)
    hfa_prior_weight: float = 10.0
    fcs_prior_net: float = -25.0  # prior net rating of the pooled FCS team

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping | None) -> "ModelParams":
        known = {f.name for f in fields(cls)}
        return cls(**{k: float(v) for k, v in (data or {}).items() if k in known})

    def replace(self, **changes) -> "ModelParams":
        return ModelParams(**{**self.to_dict(), **changes})


@dataclass
class Ratings:
    mu: float
    hfa: float
    offense: dict[int, float]
    defense: dict[int, float]
    games_played: dict[int, int] = field(default_factory=dict)

    def net(self, team: int) -> float:
        return self.offense.get(team, 0.0) + self.defense.get(team, 0.0)

    def project(self, team_a: int, team_b: int, home: int | None = None) -> tuple[float, float]:
        """Projected points for (team_a, team_b). ``home=None`` means neutral site."""
        h = 0.0
        if home is not None and home == team_a:
            h = self.hfa / 2
        elif home is not None and home == team_b:
            h = -self.hfa / 2
        pa = self.mu + self.offense.get(team_a, 0.0) - self.defense.get(team_b, 0.0) + h
        pb = self.mu + self.offense.get(team_b, 0.0) - self.defense.get(team_a, 0.0) - h
        return pa, pb

    def predict_margin(self, team_a: int, team_b: int, home: int | None = None) -> float:
        pa, pb = self.project(team_a, team_b, home)
        return pa - pb


@dataclass
class SeasonData:
    season: int
    teams: list[int]  # FBS team ids for this season
    games: list[GameRecord]  # completed games (non-FBS teams mapped to FCS_KEY)
    talent_z: dict[int, float] = field(default_factory=dict)


@dataclass
class BacktestResult:
    n: int
    mae: float
    rmse: float
    bias: float
    winner_accuracy: float
    per_season: dict[int, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Core fitting
# --------------------------------------------------------------------------

def dampen_scores(pf: float, pa: float, cap: float, excess: float) -> tuple[float, float]:
    """Shrink the winner's score so only ``excess`` of margin beyond ``cap`` counts."""
    margin = pf - pa
    if cap <= 0 or abs(margin) <= cap:
        return pf, pa
    adj = (abs(margin) - cap) * (1.0 - excess)
    return (pf - adj, pa) if margin > 0 else (pf, pa - adj)


def fit_ratings(
    games: Sequence[GameRecord],
    priors: Mapping[int, tuple[float, float]],
    params: ModelParams,
    teams: Iterable[int] = (),
) -> Ratings:
    keys = set(teams) | set(priors)
    for g in games:
        keys.add(g.home)
        keys.add(g.away)
    keys = sorted(keys)
    idx = {k: i for i, k in enumerate(keys)}
    n = len(keys)
    ncol = 2 + 2 * n
    off0, def0 = 2, 2 + n

    prior_vec = np.zeros(ncol)
    lam = np.full(ncol, params.prior_weight, dtype=float)
    prior_vec[0], lam[0] = params.league_avg_points, 1e-3
    prior_vec[1], lam[1] = params.hfa_prior, params.hfa_prior_weight
    for k, (po, pd) in priors.items():
        i = idx[k]
        prior_vec[off0 + i] = po
        prior_vec[def0 + i] = pd

    games_played = {k: 0 for k in keys}
    if games:
        last = max(g.order for g in games)
        decay = math.log(2) / params.half_life_weeks if params.half_life_weeks > 0 else 0.0
        m = 2 * len(games)
        X = np.zeros((m, ncol))
        y = np.zeros(m)
        w = np.zeros(m)
        for j, g in enumerate(games):
            hp, ap = dampen_scores(g.home_points, g.away_points, params.blowout_cap, params.blowout_excess)
            wt = math.exp(-decay * (last - g.order))
            hv = 0.0 if g.neutral else 0.5
            h, a = idx[g.home], idx[g.away]
            r = 2 * j
            X[r, 0], X[r, 1], X[r, off0 + h], X[r, def0 + a] = 1.0, hv, 1.0, -1.0
            y[r], w[r] = hp, wt
            r += 1
            X[r, 0], X[r, 1], X[r, off0 + a], X[r, def0 + h] = 1.0, -hv, 1.0, -1.0
            y[r], w[r] = ap, wt
            games_played[g.home] += 1
            games_played[g.away] += 1
        XtW = X.T * w
        A = XtW @ X + np.diag(lam)
        b = XtW @ y + lam * prior_vec
    else:
        A = np.diag(lam)
        b = lam * prior_vec

    beta = np.linalg.solve(A, b)
    return Ratings(
        mu=float(beta[0]),
        hfa=float(beta[1]),
        offense={k: float(beta[off0 + i]) for k, i in idx.items()},
        defense={k: float(beta[def0 + i]) for k, i in idx.items()},
        games_played=games_played,
    )


def build_priors(
    teams: Iterable[int],
    prev: Ratings | None,
    talent_z: Mapping[int, float],
    params: ModelParams,
) -> dict[int, tuple[float, float]]:
    priors: dict[int, tuple[float, float]] = {}
    for t in teams:
        if prev is not None and t in prev.offense:
            po, pd = params.carryover * prev.offense[t], params.carryover * prev.defense[t]
        elif t == FCS_KEY:
            po = pd = params.fcs_prior_net / 2
        else:
            po = pd = 0.0
        if t != FCS_KEY and t in talent_z:
            bump = params.talent_coef * talent_z[t] / 2
            po, pd = po + bump, pd + bump
        priors[t] = (po, pd)
    return priors


def fit_season(
    sd: SeasonData,
    prev: Ratings | None,
    params: ModelParams,
    games: Sequence[GameRecord] | None = None,
) -> Ratings:
    teams = list(sd.teams) + [FCS_KEY]
    priors = build_priors(teams, prev, sd.talent_z, params)
    return fit_ratings(sd.games if games is None else games, priors, params, teams)


def fit_chain(seasons: Sequence[SeasonData], params: ModelParams) -> dict[int, Ratings]:
    """Fit seasons oldest -> newest, each using the previous final ratings as its prior."""
    finals: dict[int, Ratings] = {}
    prev = None
    for sd in sorted(seasons, key=lambda s: s.season):
        prev = fit_season(sd, prev, params)
        finals[sd.season] = prev
    return finals


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------

def _metrics(pairs: list[tuple[float, float]]) -> dict:
    if not pairs:
        return {"n": 0, "mae": float("nan"), "rmse": float("nan"), "bias": float("nan"), "winner_accuracy": float("nan")}
    pred = np.array([p for p, _ in pairs])
    actual = np.array([a for _, a in pairs])
    err = pred - actual
    decided = (pred != 0) & (actual != 0)
    acc = float(np.mean(np.sign(pred[decided]) == np.sign(actual[decided]))) if decided.any() else float("nan")
    return {
        "n": int(len(pairs)),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "bias": float(np.mean(err)),
        "winner_accuracy": acc,
    }


def backtest(
    seasons: Sequence[SeasonData],
    params: ModelParams,
    eval_seasons: Iterable[int] | None = None,
) -> BacktestResult:
    """Walk-forward backtest: every week is predicted using only games played before it.

    By default every season except the oldest is evaluated (the oldest has no
    prior-season ratings to start from). Only FBS-vs-FBS games are scored.
    """
    ordered = sorted(seasons, key=lambda s: s.season)
    if eval_seasons is None:
        eval_set = {s.season for s in ordered[1:]}
    else:
        eval_set = set(eval_seasons)

    all_pairs: list[tuple[float, float]] = []
    per_season: dict[int, dict] = {}
    prev: Ratings | None = None
    for sd in ordered:
        if sd.season in eval_set and sd.games:
            teams = list(sd.teams) + [FCS_KEY]
            priors = build_priors(teams, prev, sd.talent_z, params)
            pairs: list[tuple[float, float]] = []
            for o in sorted({g.order for g in sd.games}):
                train = [g for g in sd.games if g.order < o]
                test = [g for g in sd.games if g.order == o and g.home != FCS_KEY and g.away != FCS_KEY]
                if not test:
                    continue
                r = fit_ratings(train, priors, params, teams)
                for g in test:
                    pred = r.predict_margin(g.home, g.away, home=None if g.neutral else g.home)
                    pairs.append((pred, g.margin))
            per_season[sd.season] = _metrics(pairs)
            all_pairs.extend(pairs)
        prev = fit_season(sd, prev, params)

    m = _metrics(all_pairs)
    return BacktestResult(per_season=per_season, **m)


def tune(
    seasons: Sequence[SeasonData],
    base: ModelParams | None = None,
    grid: Mapping[str, Sequence[float]] | None = None,
    eval_seasons: Iterable[int] | None = None,
    progress=None,
) -> tuple[ModelParams, BacktestResult, list[tuple[dict, float]]]:
    """Small grid search minimising walk-forward MAE."""
    import itertools

    base = base or ModelParams()
    grid = grid or {
        "prior_weight": [2.0, 3.0, 5.0],
        "carryover": [0.5, 0.65, 0.8],
        "talent_coef": [2.0, 4.0, 6.0],
        "half_life_weeks": [6.0, 10.0, 20.0],
    }
    names = list(grid)
    best: tuple[ModelParams, BacktestResult] | None = None
    history: list[tuple[dict, float]] = []
    combos = list(itertools.product(*(grid[n] for n in names)))
    for i, combo in enumerate(combos, 1):
        p = base.replace(**dict(zip(names, combo)))
        res = backtest(seasons, p, eval_seasons)
        history.append((dict(zip(names, combo)), res.mae))
        if best is None or res.mae < best[1].mae:
            best = (p, res)
        if progress:
            progress(i, len(combos), dict(zip(names, combo)), res.mae)
    assert best is not None
    return best[0], best[1], history


def win_probability(margin: float, sigma: float) -> float:
    sigma = sigma if sigma and sigma > 0 else DEFAULT_SIGMA
    return 0.5 * (1.0 + math.erf(margin / (sigma * math.sqrt(2.0))))
