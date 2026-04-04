"""Configuration management using Pydantic settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class BrokerRobinhoodConfig(BaseModel):
    account_type: Literal["cash", "margin"] = "cash"


class BrokerAlpacaConfig(BaseModel):
    base_url: str = "https://paper-api.alpaca.markets"
    data_feed: Literal["iex", "sip"] = "iex"


class BrokerIBKRConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1


class BrokersConfig(BaseModel):
    primary: Literal["alpaca", "robinhood", "ibkr"] = "alpaca"
    robinhood: BrokerRobinhoodConfig = BrokerRobinhoodConfig()
    alpaca: BrokerAlpacaConfig = BrokerAlpacaConfig()
    ibkr: BrokerIBKRConfig = BrokerIBKRConfig()


class TimescaleDBConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    dbname: str = "hft_agent"
    user: str = "hft"
    password: str = ""
    pool_size: int = 10

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class DatabaseConfig(BaseModel):
    timescaledb: TimescaleDBConfig = TimescaleDBConfig()
    redis: RedisConfig = RedisConfig()


class DataConfig(BaseModel):
    symbols: list[str] = ["SPY", "QQQ", "AAPL"]
    bar_interval: str = "1Min"
    orderbook_depth: int = 10


class ProbabilityConfig(BaseModel):
    return_distribution: str = "student_t"
    tail_exponent_prior: float = 3.0
    tail_exponent_min: float = 2.0
    asymmetry_factor: float = 1.15
    dispersion_metric: Literal["mad", "std", "iqr"] = "mad"
    estimation_window: int = 5000


class OFIConfig(BaseModel):
    enabled: bool = True
    lookback_ticks: int = 50
    smoothing_window: int = 10


class HurstConfig(BaseModel):
    enabled: bool = True
    window: int = 500
    regime_threshold_persistence: float = 0.55
    regime_threshold_mean_reversion: float = 0.45


class VPINConfig(BaseModel):
    enabled: bool = True
    bucket_size: int = 50
    n_buckets: int = 50
    toxicity_threshold: float = 0.7


class MultifractalConfig(BaseModel):
    enabled: bool = True
    scales: list[int] = [16, 32, 64, 128, 256]


class SignalsConfig(BaseModel):
    ofi: OFIConfig = OFIConfig()
    hurst: HurstConfig = HurstConfig()
    vpin: VPINConfig = VPINConfig()
    multifractal: MultifractalConfig = MultifractalConfig()


class FragilityConfig(BaseModel):
    enabled: bool = True
    vol_sensitivity_threshold: float = -0.5


class RiskConfig(BaseModel):
    kelly_fraction: float = 0.25
    max_position_pct: float = 0.05
    max_total_exposure_pct: float = 0.30
    cvar_confidence: float = 0.99
    max_cvar_pct: float = 0.02
    daily_loss_limit_pct: float = 0.03
    max_drawdown_pct: float = 0.10
    fragility: FragilityConfig = FragilityConfig()


class StrategyConfig(BaseModel):
    name: str = "adaptive_microstructure"
    regime_adaptive: bool = True
    min_signal_strength: float = 0.6
    prefer_limit_orders: bool = True
    min_spread_bps: float = 2.0
    max_orders_per_second: int = 5


class ExecutionConfig(BaseModel):
    slippage_model: Literal["power_law", "linear", "none"] = "power_law"
    max_retries: int = 3
    order_timeout_s: int = 5


class PrometheusConfig(BaseModel):
    enabled: bool = True
    port: int = 9090


class HealthCheckConfig(BaseModel):
    enabled: bool = True
    port: int = 8080


class MonitoringConfig(BaseModel):
    prometheus: PrometheusConfig = PrometheusConfig()
    health_check: HealthCheckConfig = HealthCheckConfig()


class AppConfig(BaseModel):
    name: str = "hft-agent"
    mode: Literal["paper", "live"] = "paper"
    log_level: str = "INFO"
    tick_interval_ms: int = 100


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    brokers: BrokersConfig = BrokersConfig()
    database: DatabaseConfig = DatabaseConfig()
    data: DataConfig = DataConfig()
    probability: ProbabilityConfig = ProbabilityConfig()
    signals: SignalsConfig = SignalsConfig()
    risk: RiskConfig = RiskConfig()
    strategy: StrategyConfig = StrategyConfig()
    execution: ExecutionConfig = ExecutionConfig()
    monitoring: MonitoringConfig = MonitoringConfig()


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Load settings from YAML config file with environment variable overrides."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"

    config_path = Path(config_path)
    if not config_path.exists():
        return Settings()

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    # Resolve environment variable references like ${VAR_NAME}
    _resolve_env_vars(raw)

    return Settings(**raw)


def _resolve_env_vars(obj: dict | list | str) -> None:
    """Recursively resolve ${ENV_VAR} patterns in config values."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                obj[key] = os.environ.get(env_var, "")
            elif isinstance(value, (dict, list)):
                _resolve_env_vars(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                env_var = item[2:-1]
                obj[i] = os.environ.get(env_var, "")
            elif isinstance(item, (dict, list)):
                _resolve_env_vars(item)
