import json

import numpy as np
import pandas as pd
import pytest

from engine import gauge, paper, plan, walkforward
from engine.backtest import run_backtest
from engine.config import EngineConfig, RiskLimits, StrategyParams
from engine.data import MarketData
from engine.portfolio import build_target
from engine.signals import dfa_hurst, hill_tail_exponent, historical_es, tail_es, trend_score


def make_market(n=1400, seed=0, end=None):
    rng = np.random.default_rng(seed)
    drifts = {"UP": 0.0008, "DOWN": -0.0006, "FLAT": 0.0, "UP2": 0.0005}
    idx = pd.bdate_range(end=end or pd.Timestamp.today().normalize(), periods=n)
    close = {}
    for sym, mu in drifts.items():
        r = mu + 0.01 * rng.standard_t(3, n) / np.sqrt(3)
        close[sym] = 100 * np.exp(np.cumsum(r))
    close["SGOV"] = 100 * np.cumprod(np.full(n, 1 + 0.03 / 252))
    close = pd.DataFrame(close, index=idx)
    vol = pd.DataFrame(1e6, index=idx, columns=close.columns)
    return MarketData(close, vol, "synthetic")


def cfg_for_tests(**kw):
    base = dict(
        universe=["UP", "DOWN", "FLAT", "UP2"],
        safe_asset="SGOV",
        safe_asset_fallbacks=[],
        benchmark="UP",
        risk=RiskLimits(lookback_days=252),
        params=StrategyParams(horizons=[21, 63, 126]),
        param_grid={"risky_budget": [0.2, 0.4], "use_hurst": [True, False]},
    )
    base.update(kw)
    return EngineConfig(**base)


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(walkforward, "STATE_DIR", tmp_path)
    monkeypatch.setattr(plan, "STATE_DIR", tmp_path)
    monkeypatch.setattr(paper, "STATE_DIR", tmp_path)
    monkeypatch.setattr(paper, "LEDGER", tmp_path / "paper.json")
    return tmp_path


class TestGauge:
    def setup_method(self):
        rng = np.random.default_rng(1)
        self.r = rng.normal(0.0005, 0.02, (300, 3))
        w = rng.dirichlet([1, 1, 1], 300)
        self.w = w

    def test_exact_identity(self):
        a = gauge.attribute(self.w, self.r)
        assert np.allclose(a.exposure + a.timing + a.convexity, np.log1p((self.w * self.r).sum(1)))

    def test_constant_weights_have_no_timing(self):
        w = np.tile([0.5, 0.3, 0.2], (300, 1))
        assert abs(gauge.attribute(w, self.r).timing.sum()) < 1e-12

    def test_convexity_nonnegative_long_only(self):
        assert (gauge.attribute(self.w, self.r).convexity >= -1e-12).all()

    def test_numeraire_invariance(self):
        num = np.random.default_rng(2).normal(0.0002, 0.01, 300)
        a = gauge.attribute(self.w, self.r)
        b = gauge.attribute(self.w, gauge.change_numeraire(self.r, num))
        assert np.allclose(a.timing, b.timing)
        assert np.allclose(a.convexity, b.convexity)
        assert not np.allclose(a.exposure, b.exposure)

    def test_holonomy_on_closed_price_loop(self):
        # Price goes up 10% then back: a closed loop. Buy-and-hold ends flat; a 50/50
        # constant-mix sells high and buys low (Shannon's demon), so its holonomy is
        # positive and lives entirely in the convexity term.
        r = np.array([[0.10, 0.0], [-1 / 11, 0.0]])
        w = np.array([[0.5, 0.5], [0.5, 0.5]])
        a = gauge.attribute(w, r)
        assert abs(a.exposure.sum()) < 1e-12
        assert abs(a.timing.sum()) < 1e-12
        assert a.total.sum() > 0
        assert np.isclose(a.total.sum(), a.convexity.sum())


class TestSignals:
    def test_hurst_white_noise_near_half(self):
        x = np.random.default_rng(3).normal(size=2000)
        assert 0.4 < dfa_hurst(x) < 0.6

    def test_hurst_persistent_above_half(self):
        e = np.random.default_rng(4).normal(size=2100)
        x = np.convolve(e, np.ones(20) / 20, mode="valid")
        assert dfa_hurst(x) > 0.7

    def test_hill_detects_fat_tails(self):
        rng = np.random.default_rng(5)
        fat = hill_tail_exponent(rng.standard_t(3, 20000))
        thin = hill_tail_exponent(rng.normal(size=20000))
        assert 2.2 < fat < 4.0
        assert thin > fat

    def test_tail_es_conservative(self):
        x = np.random.default_rng(6).standard_t(3, 3000) * 0.01
        assert tail_es(x, 2.5) >= historical_es(x) > 0

    def test_trend_sign(self):
        up = np.log(np.linspace(100, 150, 300))
        assert trend_score(up, [21, 63, 126]) > 0
        assert trend_score(up[::-1], [21, 63, 126]) < 0


class TestPortfolio:
    def setup_method(self):
        md = make_market()
        self.syms = ["UP", "DOWN", "FLAT", "UP2"]
        self.lp = np.log(md.close[self.syms].to_numpy())
        self.params = StrategyParams(horizons=[21, 63, 126], risky_budget=0.3)

    def test_long_only_within_budget(self):
        t = build_target(self.syms, self.lp, self.params, RiskLimits(lookback_days=252))
        assert all(w >= 0 for w in t.weights.values())
        assert t.risky_exposure <= 0.3 + 1e-9
        assert np.isclose(t.safe_weight + t.risky_exposure, 1.0)
        assert all(w <= 0.10 + 1e-12 for w in t.weights.values())
        assert "DOWN" not in t.weights

    def test_es_cap_binds(self):
        t = build_target(self.syms, self.lp, self.params, RiskLimits(lookback_days=252, max_cvar_99_daily=0.0005))
        assert any("Tail risk" in v for v in t.vetoes)
        assert t.portfolio_es99 <= 0.0005 + 1e-9

    def test_drawdown_brake(self):
        base = build_target(self.syms, self.lp, self.params, RiskLimits(lookback_days=252))
        braked = build_target(self.syms, self.lp, self.params, RiskLimits(lookback_days=252), drawdown=0.5)
        assert np.isclose(braked.risky_exposure, base.risky_exposure * 0.5)

    def test_explanations_present(self):
        t = build_target(self.syms, self.lp, self.params, RiskLimits(lookback_days=252))
        assert all(a.reason for a in t.assets)


class TestBacktest:
    def test_accounting_and_cash_only(self):
        md, cfg = make_market(), cfg_for_tests()
        run = run_backtest(md, cfg)
        safe = run.columns.index("SAFE")
        assert (run.weights[:, safe] >= -1e-9).all()
        assert np.allclose(run.weights.sum(1), 1.0)
        g = gauge.attribute(run.weights, run.period_returns).total.sum()
        cost_drag = np.sum(np.log(1 - run.costs[1:] / (run.equity[1:] + run.costs[1:])))
        assert np.isclose(g + cost_drag, np.log(run.equity[-1] / run.equity[0]), atol=1e-9)
        assert len(run.orders) > 0 and len(run.round_trips) > 0

    def test_put_hedge_is_labelled_and_accounted(self):
        from engine.config import HedgeConfig

        md = make_market()
        cfg = cfg_for_tests(hedge=HedgeConfig(enabled=True, underlying="UP", annual_budget=0.02))
        run = run_backtest(md, cfg)
        assert "HEDGE" in run.columns and "model-priced" in run.hedge_note
        assert np.allclose(run.weights.sum(1), 1.0)
        g = gauge.attribute(run.weights, run.period_returns).total.sum()
        cost_drag = np.sum(np.log(1 - run.costs[1:] / (run.equity[1:] + run.costs[1:])))
        assert np.isclose(g + cost_drag, np.log(run.equity[-1] / run.equity[0]), atol=1e-9)

    def test_no_lookahead(self):
        md, cfg = make_market(), cfg_for_tests()
        base = run_backtest(md, cfg)
        k = 1000
        shocked_close = md.close.copy()
        shocked_close.iloc[k + 1:, :4] *= 3.0
        shocked = run_backtest(MarketData(shocked_close, md.volume, "x"), cfg)
        cut = base.dates.get_loc(md.close.index[k])
        assert np.allclose(base.equity[: cut + 1], shocked.equity[: cut + 1])


class TestWalkForward:
    def test_runs_and_is_json_safe(self, state):
        md, cfg = make_market(n=1700), cfg_for_tests()
        res = walkforward.walk_forward(md, cfg, train_years=2, workers=1)
        json.dumps(res, allow_nan=False)
        assert res["folds"] and res["metrics"]["Strategy (out-of-sample)"]
        first_test = pd.Timestamp(res["period"][0])
        assert first_test.year >= md.close.index[0].year + 3
        assert (state / "model.json").exists()
        assert "Naive barbell (matched avg exposure)" in res["bootstrap"]


class TestPlanAndPaper:
    def test_plan_orders_and_checks(self, state):
        md, cfg = make_market(), cfg_for_tests()
        p = plan.make_plan(cfg, {"DOWN": 10, "UP": 1}, 5000.0, md=md)
        assert not p["blocked"]
        sides = [o["side"] for o in p["orders"]]
        assert sides == sorted(sides, key=lambda s: s != "sell")
        assert any(o["symbol"] == "DOWN" and o["sell_all"] for o in p["orders"])
        buys = sum(o["notional_usd"] for o in p["orders"] if o["side"] == "buy")
        sells = sum(o["notional_usd"] for o in p["orders"] if o["side"] == "sell")
        assert buys <= 5000 + sells + 1e-6

    def test_plan_blocks_on_stale_data(self, state):
        md, cfg = make_market(end=pd.Timestamp("2020-01-31")), cfg_for_tests()
        p = plan.make_plan(cfg, {}, 1000.0, md=md)
        assert p["blocked"]

    def test_paper_trades_once_per_day(self, state):
        md, cfg = make_market(), cfg_for_tests()
        paper.init(10_000)
        first = paper.step(cfg, md=md)
        second = paper.step(cfg, md=md)
        assert first["traded"] and not second["traded"]
        assert first["ledger"]["cash"] >= 0
        assert abs(second["equity"] - first["equity"]) < 1e-6
