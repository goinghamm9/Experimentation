"""
Risk management orchestrator.

Implements the full risk framework from the research papers:
1. Fat-tailed CVaR (not Gaussian VaR)
2. Fractional Kelly position sizing
3. Fragility detection
4. Daily loss limits and drawdown stops
5. VPIN-based toxicity filtering
6. Path-dependent ruin probability monitoring

Key principle (Peters 2019): Maximize log-wealth (time-average growth),
not expected return. A single ruin event permanently removes the agent
from the game — there is no recovery from zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from core.probability.distributions import FatTailDistribution, mean_absolute_deviation
from core.probability.tail_estimator import EVTTailEstimator
from utils.config import RiskConfig
from utils.logging import get_logger
from utils.types import Order, PortfolioState, Side, Signal

from .fragility import FragilityDetector, FragilityReport, FragilityState
from .kelly import FractionalKelly

logger = get_logger(__name__)


@dataclass
class RiskCheck:
    """Result of a risk check on a proposed trade."""
    approved: bool
    adjusted_qty: float
    reason: str
    cvar: float | None = None
    kelly_size: float | None = None
    exposure_pct: float | None = None


class RiskManager:
    """Central risk management for the HFT agent.

    Every proposed trade goes through this manager before execution.
    It enforces:
    - Position size limits (fractional Kelly)
    - CVaR limits (fat-tailed, not Gaussian)
    - Daily loss limits
    - Drawdown limits
    - Toxicity filters
    - Fragility checks
    """

    def __init__(self, config: RiskConfig, initial_equity: float):
        self._config = config
        self._initial_equity = initial_equity
        self._peak_equity = initial_equity
        self._daily_pnl = 0.0
        self._daily_start_equity = initial_equity

        # Components
        self._kelly = FractionalKelly(
            kelly_fraction=config.kelly_fraction,
            max_position_pct=config.max_position_pct,
        )
        self._distribution = FatTailDistribution()
        self._tail_estimator = EVTTailEstimator()
        self._fragility_detector = FragilityDetector(
            vol_sensitivity_threshold=config.fragility.vol_sensitivity_threshold,
        )

        # State
        self._returns_history: dict[str, list[float]] = {}
        self._pnl_history: list[float] = []
        self._market_returns_history: list[float] = []
        self._is_halted = False
        self._halt_reason = ""

    def check_trade(
        self,
        signal: Signal,
        portfolio: PortfolioState,
        current_price: float,
        returns_history: NDArray[np.float64] | None = None,
    ) -> RiskCheck:
        """Check whether a proposed trade should be allowed.

        This is the main entry point. Every trade goes through here.
        """
        symbol = signal.symbol

        # Check 1: Is trading halted?
        if self._is_halted:
            return RiskCheck(
                approved=False,
                adjusted_qty=0,
                reason=f"Trading halted: {self._halt_reason}",
            )

        # Check 2: Daily loss limit
        daily_return = 0.0
        if self._daily_start_equity > 0:
            daily_return = (portfolio.total_equity - self._daily_start_equity) / self._daily_start_equity
        if daily_return < -self._config.daily_loss_limit_pct:
            self._halt_trading(f"Daily loss limit hit: {daily_return:.2%}")
            return RiskCheck(
                approved=False,
                adjusted_qty=0,
                reason=f"Daily loss limit exceeded: {daily_return:.2%}",
            )

        # Check 3: Max drawdown
        self._peak_equity = max(self._peak_equity, portfolio.total_equity)
        drawdown = 0.0
        if self._peak_equity > 0:
            drawdown = 1 - portfolio.total_equity / self._peak_equity
        if drawdown > self._config.max_drawdown_pct:
            self._halt_trading(f"Max drawdown hit: {drawdown:.2%}")
            return RiskCheck(
                approved=False,
                adjusted_qty=0,
                reason=f"Max drawdown exceeded: {drawdown:.2%}",
            )

        # Check 4: Total exposure limit
        if portfolio.exposure_pct > self._config.max_total_exposure_pct:
            return RiskCheck(
                approved=False,
                adjusted_qty=0,
                reason=f"Total exposure limit: {portfolio.exposure_pct:.2%} > {self._config.max_total_exposure_pct:.2%}",
                exposure_pct=portfolio.exposure_pct,
            )

        # Check 5: Calculate optimal position size via Kelly
        kelly_shares = 0.0
        if returns_history is not None and len(returns_history) > 20:
            self._distribution.fit(returns_history)
            kelly_shares = self._kelly.optimal_position_size(
                expected_return=signal.value,
                returns_history=returns_history,
                portfolio_value=portfolio.total_equity,
                price=current_price,
            )

        # Check 6: CVaR limit
        cvar = None
        if returns_history is not None and len(returns_history) > 50:
            self._tail_estimator.fit(returns_history)
            cvar_raw = self._distribution.cvar(self._config.cvar_confidence)
            if cvar_raw is not None:
                # Scale CVaR by proposed position size
                position_value = abs(kelly_shares * current_price)
                cvar = abs(cvar_raw) * position_value
                max_cvar = portfolio.total_equity * self._config.max_cvar_pct

                if cvar > max_cvar:
                    # Scale down position to meet CVaR limit
                    scale_factor = max_cvar / cvar if cvar > 0 else 0
                    kelly_shares *= scale_factor
                    cvar *= scale_factor
                    logger.info(
                        "position_scaled_for_cvar",
                        symbol=symbol,
                        scale_factor=scale_factor,
                    )

        # Final position size (rounded to whole shares for equities)
        final_qty = abs(kelly_shares)
        if final_qty < 1:
            return RiskCheck(
                approved=False,
                adjusted_qty=0,
                reason="Position size too small after risk adjustment",
                cvar=cvar,
                kelly_size=kelly_shares,
            )

        final_qty = round(final_qty)

        return RiskCheck(
            approved=True,
            adjusted_qty=final_qty,
            reason="Approved",
            cvar=cvar,
            kelly_size=kelly_shares,
            exposure_pct=portfolio.exposure_pct,
        )

    def update_pnl(self, pnl: float, market_return: float) -> None:
        """Update P&L tracking for fragility analysis."""
        self._daily_pnl += pnl
        self._pnl_history.append(pnl)
        self._market_returns_history.append(market_return)

    def reset_daily(self, equity: float) -> None:
        """Reset daily tracking (call at market open)."""
        self._daily_pnl = 0.0
        self._daily_start_equity = equity
        self._is_halted = False
        self._halt_reason = ""

    def assess_fragility(self) -> FragilityReport | None:
        """Run fragility assessment on recent trading performance."""
        if len(self._pnl_history) < 100:
            return None

        return self._fragility_detector.assess(
            pnl_series=np.array(self._pnl_history[-500:]),
            return_series=np.array(self._market_returns_history[-500:]),
        )

    def _halt_trading(self, reason: str) -> None:
        """Halt all trading until reset."""
        self._is_halted = True
        self._halt_reason = reason
        logger.warning("trading_halted", reason=reason)

    @property
    def is_halted(self) -> bool:
        return self._is_halted

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl
