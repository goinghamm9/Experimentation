"""Engine configuration. Defaults match a Robinhood agentic account: cash-only, long-only."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

WORK_DIR = Path(os.environ.get("HFT_HOME", Path.cwd()))
STATE_DIR = WORK_DIR / "state"
CACHE_DIR = WORK_DIR / ".cache" / "prices"
_SOURCE_CONFIG = Path(__file__).resolve().parent.parent / "config" / "engine.yaml"
DEFAULT_CONFIG = WORK_DIR / "config" / "engine.yaml" if (WORK_DIR / "config" / "engine.yaml").exists() else _SOURCE_CONFIG


class StrategyParams(BaseModel):
    """Parameters the walk-forward search is allowed to choose between."""

    risky_budget: float = Field(0.25, description="Max fraction of equity in the risky sleeve")
    horizons: list[int] = Field(default_factory=lambda: [21, 63, 126, 252])
    use_hurst: bool = True
    kelly_fraction: float = 0.25


class RiskLimits(BaseModel):
    max_weight_per_asset: float = 0.10
    max_cvar_99_daily: float = 0.015
    max_drawdown_brake: float = 0.15
    tail_exponent_floor: float = 2.0
    metaprobability_discount: float = 0.85
    lookback_days: int = 504


class Costs(BaseModel):
    half_spread_bps: float = 2.0
    impact_coef: float = 0.1
    cash_rate_annual: float = 0.0


class HedgeConfig(BaseModel):
    enabled: bool = False
    underlying: str = "SPY"
    annual_budget: float = 0.01
    moneyness: float = 0.90
    tenor_days: int = 21
    vol_markup: float = 1.25


class EngineConfig(BaseModel):
    universe: list[str] = Field(
        default_factory=lambda: ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ"]
    )
    safe_asset: str = "SGOV"
    safe_asset_fallbacks: list[str] = Field(default_factory=lambda: ["BIL", "SHV"])
    benchmark: str = "SPY"
    rebalance_every_days: int = 5
    no_trade_band: float = Field(0.25, description="Rebalance only if a position is this far (relative) from target")
    min_order_usd: float = 1.0
    params: StrategyParams = StrategyParams()
    param_grid: dict[str, list] = Field(
        default_factory=lambda: {
            "risky_budget": [0.15, 0.25, 0.35],
            "horizons": [[21, 63, 126, 252], [63, 126, 252]],
            "use_hurst": [True, False],
        }
    )
    risk: RiskLimits = RiskLimits()
    costs: Costs = Costs()
    hedge: HedgeConfig = HedgeConfig()
    data_source: str = "auto"
    csv_path: str | None = None


def load_config(path: str | Path | None = None) -> EngineConfig:
    p = Path(path) if path else DEFAULT_CONFIG
    if not p.exists():
        return EngineConfig()
    with open(p) as f:
        raw = yaml.safe_load(f) or {}
    return EngineConfig(**raw)
