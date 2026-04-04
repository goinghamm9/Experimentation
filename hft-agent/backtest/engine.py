"""
Backtesting engine for strategy evaluation.

Supports:
- Tick-level and bar-level backtesting
- Realistic slippage modeling (power-law impact)
- Fat-tailed performance metrics (not Sharpe ratio)
- Walk-forward validation
- Monte Carlo ruin probability estimation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from core.probability.distributions import (
    FatTailDistribution,
    estimate_tail_exponent,
    mean_absolute_deviation,
)
from core.risk.kelly import FractionalKelly
from utils.logging import get_logger
from utils.types import Bar, Order, OrderType, PortfolioState, Position, Side, Tick

logger = get_logger(__name__)


@dataclass
class BacktestResult:
    """Comprehensive backtest performance report.

    Uses fat-tail aware metrics per Taleb (2020):
    - MAD ratio instead of Sharpe ratio
    - CVaR instead of VaR
    - Log-wealth growth rate (ergodically correct)
    - Tail exponent estimation
    - Maximum drawdown with path statistics
    """
    # Returns
    total_return: float = 0.0
    annualized_return: float = 0.0
    log_growth_rate: float = 0.0  # Time-average (ergodic) growth

    # Risk metrics (fat-tail aware)
    mad: float = 0.0          # Mean Absolute Deviation (replaces std dev)
    mad_ratio: float = 0.0    # MAD ratio (replaces Sharpe ratio)
    cvar_99: float = 0.0      # 99% Conditional VaR
    tail_exponent: float = 0.0  # Estimated power-law tail exponent
    max_drawdown: float = 0.0
    avg_drawdown: float = 0.0
    calmar_ratio: float = 0.0  # Return / Max Drawdown

    # Trade statistics
    total_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    avg_trade_pnl: float = 0.0

    # Kelly analysis
    optimal_kelly_fraction: float = 0.0
    optimal_kelly_growth: float = 0.0
    ruin_probability: float = 0.0

    # Path statistics
    equity_curve: list[float] = field(default_factory=list)
    returns_series: list[float] = field(default_factory=list)
    trade_log: list[dict] = field(default_factory=list)


class BacktestEngine:
    """Event-driven backtesting engine."""

    def __init__(
        self,
        initial_capital: float = 100_000,
        commission_per_share: float = 0.0,  # Commission-free for Robinhood/Alpaca
        slippage_model: str = "power_law",
    ):
        self._initial_capital = initial_capital
        self._commission = commission_per_share
        self._slippage_model = slippage_model

        # State
        self._cash = initial_capital
        self._positions: dict[str, Position] = {}
        self._equity_curve: list[float] = [initial_capital]
        self._returns: list[float] = []
        self._trades: list[dict] = []
        self._peak_equity = initial_capital

    def reset(self) -> None:
        """Reset backtester state."""
        self._cash = self._initial_capital
        self._positions.clear()
        self._equity_curve = [self._initial_capital]
        self._returns = []
        self._trades = []
        self._peak_equity = self._initial_capital

    def execute_order(self, order: Order, current_price: float, timestamp: datetime) -> bool:
        """Simulate order execution with slippage.

        Returns True if order was filled.
        """
        # Apply slippage
        if self._slippage_model == "power_law":
            slippage = current_price * 0.0001 * np.sqrt(order.qty / 1000)
        elif self._slippage_model == "linear":
            slippage = current_price * 0.0001 * (order.qty / 1000)
        else:
            slippage = 0.0

        fill_price = current_price + slippage if order.side == Side.BUY else current_price - slippage
        commission = self._commission * order.qty

        # Check if we have enough cash for buys
        cost = fill_price * order.qty + commission
        if order.side == Side.BUY and cost > self._cash:
            return False

        # Update position
        symbol = order.symbol
        if symbol in self._positions:
            pos = self._positions[symbol]
            if order.side == Side.BUY:
                # Add to or open long position
                new_qty = pos.qty + order.qty
                pos.avg_entry_price = (
                    (pos.avg_entry_price * pos.qty + fill_price * order.qty) / new_qty
                )
                pos.qty = new_qty
                self._cash -= cost
            else:
                # Reduce or close position
                pnl = (fill_price - pos.avg_entry_price) * min(order.qty, pos.qty)
                pos.qty -= order.qty
                self._cash += fill_price * order.qty - commission
                pos.realized_pnl += pnl

                if abs(pos.qty) < 0.001:
                    del self._positions[symbol]
        else:
            if order.side == Side.BUY:
                self._positions[symbol] = Position(
                    symbol=symbol,
                    qty=order.qty,
                    avg_entry_price=fill_price,
                    current_price=fill_price,
                )
                self._cash -= cost
            else:
                # Short position
                self._positions[symbol] = Position(
                    symbol=symbol,
                    qty=-order.qty,
                    avg_entry_price=fill_price,
                    current_price=fill_price,
                )
                self._cash += fill_price * order.qty - commission

        # Log trade
        self._trades.append({
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "side": order.side.value,
            "qty": order.qty,
            "price": fill_price,
            "commission": commission,
            "slippage": slippage,
        })

        return True

    def update_prices(self, prices: dict[str, float]) -> None:
        """Update position mark-to-market with current prices."""
        for symbol, price in prices.items():
            if symbol in self._positions:
                pos = self._positions[symbol]
                pos.current_price = price
                pos.unrealized_pnl = (price - pos.avg_entry_price) * pos.qty

        # Update equity curve
        equity = self._cash + sum(
            pos.current_price * pos.qty for pos in self._positions.values()
        )
        self._equity_curve.append(equity)

        # Track returns
        if len(self._equity_curve) >= 2 and self._equity_curve[-2] > 0:
            ret = (equity - self._equity_curve[-2]) / self._equity_curve[-2]
            self._returns.append(ret)

        self._peak_equity = max(self._peak_equity, equity)

    def get_portfolio_state(self) -> PortfolioState:
        """Get current portfolio state for strategy use."""
        equity = self._cash + sum(
            pos.current_price * pos.qty for pos in self._positions.values()
        )
        drawdown = 1 - equity / self._peak_equity if self._peak_equity > 0 else 0

        return PortfolioState(
            cash=self._cash,
            positions=dict(self._positions),
            total_equity=equity,
            peak_equity=self._peak_equity,
            max_drawdown=drawdown,
        )

    def generate_report(self) -> BacktestResult:
        """Generate comprehensive performance report with fat-tail aware metrics."""
        if not self._returns:
            return BacktestResult()

        returns = np.array(self._returns, dtype=np.float64)
        equity = np.array(self._equity_curve, dtype=np.float64)

        # Basic returns
        total_return = (equity[-1] - equity[0]) / equity[0] if equity[0] > 0 else 0
        n_periods = len(returns)
        # Assume ~252 trading days, ~390 min/day
        periods_per_year = 252 * 390 if n_periods > 1000 else 252
        annualized_return = (1 + total_return) ** (periods_per_year / max(n_periods, 1)) - 1

        # Log-growth rate (ergodically correct metric per Peters 2019)
        log_returns = np.log(1 + returns[returns > -1])
        log_growth = float(np.mean(log_returns)) if len(log_returns) > 0 else 0

        # MAD (robust dispersion under fat tails, per Taleb 2020)
        mad = mean_absolute_deviation(returns)

        # MAD ratio (replaces Sharpe ratio)
        mean_return = float(np.mean(returns))
        mad_ratio = mean_return / mad if mad > 0 else 0

        # CVaR (Expected Shortfall) at 99%
        var_99 = float(np.percentile(returns, 1))
        tail_returns = returns[returns <= var_99]
        cvar_99 = float(np.mean(tail_returns)) if len(tail_returns) > 0 else var_99

        # Tail exponent (Hill estimator)
        tail_exp = estimate_tail_exponent(returns) if len(returns) > 100 else 3.0

        # Drawdown analysis
        peaks = np.maximum.accumulate(equity)
        drawdowns = 1 - equity / peaks
        max_dd = float(np.max(drawdowns))
        avg_dd = float(np.mean(drawdowns[drawdowns > 0])) if np.any(drawdowns > 0) else 0

        calmar = annualized_return / max_dd if max_dd > 0 else 0

        # Trade statistics
        trade_pnls = []
        for i, trade in enumerate(self._trades):
            if i > 0 and i < len(self._returns):
                trade_pnls.append(self._returns[i])

        if trade_pnls:
            pnl_arr = np.array(trade_pnls)
            wins = pnl_arr[pnl_arr > 0]
            losses = pnl_arr[pnl_arr < 0]
            win_rate = len(wins) / len(pnl_arr) if len(pnl_arr) > 0 else 0
            avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
            avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0
            gross_profit = float(np.sum(wins))
            gross_loss = float(np.abs(np.sum(losses)))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
            avg_trade = float(np.mean(pnl_arr))
        else:
            win_rate = avg_win = avg_loss = profit_factor = avg_trade = 0.0

        # Kelly analysis
        kelly = FractionalKelly()
        if len(returns) > 50:
            opt_f, opt_g = kelly.find_optimal_fraction(returns)
            ruin_prob = kelly.ruin_probability(opt_f * 0.25, returns)
        else:
            opt_f = opt_g = ruin_prob = 0.0

        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            log_growth_rate=log_growth,
            mad=mad,
            mad_ratio=mad_ratio,
            cvar_99=cvar_99,
            tail_exponent=tail_exp,
            max_drawdown=max_dd,
            avg_drawdown=avg_dd,
            calmar_ratio=calmar,
            total_trades=len(self._trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            avg_trade_pnl=avg_trade,
            optimal_kelly_fraction=opt_f,
            optimal_kelly_growth=opt_g,
            ruin_probability=ruin_prob,
            equity_curve=self._equity_curve,
            returns_series=self._returns,
            trade_log=self._trades,
        )
