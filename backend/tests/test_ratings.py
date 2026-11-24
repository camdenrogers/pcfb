import random

import numpy as np
import pytest

from app.model.ratings import (
    FCS_KEY,
    GameRecord,
    ModelParams,
    SeasonData,
    backtest,
    dampen_scores,
    fit_chain,
    fit_ratings,
    fit_season,
    win_probability,
)


def synthetic_season(season, true_off, true_def, hfa=3.0, mu=28.0, weeks=13, noise=10.0, seed=0):
    rng = random.Random(seed)
    teams = list(true_off)
    games = []
    for week in range(1, weeks + 1):
        order = teams[:]
        rng.shuffle(order)
        for i in range(0, len(order) - 1, 2):
            h, a = order[i], order[i + 1]
            neutral = rng.random() < 0.1
            hv = 0 if neutral else hfa / 2
            hp = mu + true_off[h] - true_def[a] + hv + rng.gauss(0, noise / 1.4)
            ap = mu + true_off[a] - true_def[h] - hv + rng.gauss(0, noise / 1.4)
            games.append(GameRecord(season, week, h, a, max(0, round(hp)), max(0, round(ap)), neutral))
    return SeasonData(season=season, teams=teams, games=games)


def make_truth(n=40, seed=1):
    rng = np.random.default_rng(seed)
    off = {i: float(rng.normal(0, 7)) for i in range(1, n + 1)}
    dfn = {i: float(rng.normal(0, 7)) for i in range(1, n + 1)}
    return off, dfn


def test_dampen_scores():
    assert dampen_scores(70, 0, 28, 0.3) == pytest.approx((28 + 42 * 0.3, 0))
    assert dampen_scores(0, 70, 28, 0.3) == pytest.approx((0, 28 + 42 * 0.3))
    assert dampen_scores(31, 24, 28, 0.3) == (31, 24)


def test_recovers_true_ratings_and_hfa():
    off, dfn = make_truth()
    sd = synthetic_season(2024, off, dfn, weeks=40, noise=6.0)
    params = ModelParams(prior_weight=0.5, half_life_weeks=0, blowout_cap=0, hfa_prior_weight=0.01)
    r = fit_season(sd, None, params)
    true_net = np.array([off[t] + dfn[t] for t in sd.teams])
    est_net = np.array([r.net(t) for t in sd.teams])
    assert np.corrcoef(true_net, est_net)[0, 1] > 0.97
    assert r.hfa == pytest.approx(3.0, abs=1.0)
    assert r.mu == pytest.approx(28.0, abs=2.0)


def test_neutral_prediction_is_antisymmetric():
    off, dfn = make_truth(10)
    sd = synthetic_season(2024, off, dfn)
    r = fit_season(sd, None, ModelParams())
    assert r.predict_margin(1, 2) == pytest.approx(-r.predict_margin(2, 1))
    # home field moves the margin by exactly hfa
    assert r.predict_margin(1, 2, home=1) - r.predict_margin(1, 2) == pytest.approx(r.hfa / 2 * 2)


def test_no_games_returns_prior():
    params = ModelParams()
    r = fit_ratings([], {1: (5.0, 3.0), 2: (-2.0, -1.0)}, params)
    assert r.offense[1] == pytest.approx(5.0)
    assert r.defense[2] == pytest.approx(-1.0)
    assert r.mu == pytest.approx(params.league_avg_points)
    assert r.predict_margin(1, 2) == pytest.approx((5 + 3) - (-2 - 1))


def test_talent_prior_orders_teams_before_any_games():
    sd = SeasonData(2025, teams=[1, 2], games=[], talent_z={1: 1.5, 2: -1.0})
    r = fit_season(sd, None, ModelParams(talent_coef=4.0))
    assert r.predict_margin(1, 2) == pytest.approx(4.0 * 2.5)


def test_fcs_games_are_pooled():
    games = [GameRecord(2024, 1, 1, FCS_KEY, 56, 7), GameRecord(2024, 2, 2, FCS_KEY, 35, 14)]
    sd = SeasonData(2024, teams=[1, 2], games=games)
    r = fit_season(sd, None, ModelParams())
    assert FCS_KEY in r.offense
    assert r.net(FCS_KEY) < r.net(1)


def test_chain_and_backtest_beat_naive_baseline():
    off, dfn = make_truth(30)
    seasons = []
    for s in [2022, 2023, 2024]:
        # ratings drift a little year to year
        off = {k: 0.8 * v + np.random.default_rng(s).normal(0, 2) for k, v in off.items()}
        dfn = {k: 0.8 * v + np.random.default_rng(s + 99).normal(0, 2) for k, v in dfn.items()}
        seasons.append(synthetic_season(s, off, dfn, seed=s))
    finals = fit_chain(seasons, ModelParams())
    assert set(finals) == {2022, 2023, 2024}

    res = backtest(seasons, ModelParams())
    assert res.n > 0
    assert set(res.per_season) == {2023, 2024}
    naive_mae = np.mean([abs(g.margin) for sd in seasons[1:] for g in sd.games])
    assert res.mae < naive_mae
    assert res.winner_accuracy > 0.6


def test_win_probability():
    assert win_probability(0, 16) == pytest.approx(0.5)
    assert win_probability(16, 16) == pytest.approx(0.8413, abs=1e-3)
    assert win_probability(-7, 16) < 0.5


def test_params_roundtrip():
    p = ModelParams(prior_weight=4.0)
    assert ModelParams.from_dict({**p.to_dict(), "unknown": 1}) == p
