from __future__ import annotations

import collections
from datetime import datetime
from typing import Any

from strategies.adaptive_microstructure import TradeDecision
from utils.types import PortfolioState, Signal, Tick

from .explainer import Explainer


class Narrator:
    """Running commentary on agent activity in plain English."""

    def __init__(self, max_feed_size: int = 500):
        self._feed: collections.deque[str] = collections.deque(maxlen=max_feed_size)
        self._explainer = Explainer()
        self._trade_count = 0
        self._skip_count = 0
        self._risk_event_count = 0
        self._session_start: datetime | None = None
        self._session_pnl = 0.0

    def narrate_tick(
        self,
        tick: Tick,
        signals: dict[str, Signal] | None,
        decision: TradeDecision | None,
        portfolio: PortfolioState | None,
    ) -> str:
        if self._session_start is None:
            self._session_start = tick.timestamp

        ts = tick.timestamp.strftime("%H:%M:%S")

        if decision is None:
            entry = f"{ts} -- Received tick for {tick.symbol} at ${tick.price:.2f}. No decision generated."
            self._feed.append(entry)
            return entry

        if decision.should_trade and decision.order is not None:
            return self._narrate_trade(ts, tick, decision, signals, portfolio)

        return self._narrate_skip(ts, tick, decision, signals)

    def narrate_session_summary(self, results: Any) -> str:
        parts = ["SESSION SUMMARY", "=" * 40]

        if hasattr(results, "ticks_processed"):
            parts.append(f"Ticks processed: {results.ticks_processed:,}")
        if hasattr(results, "total_trades"):
            parts.append(f"Total trades: {results.total_trades}")
        if hasattr(results, "total_return"):
            ret = results.total_return
            emoji = "up" if ret > 0 else "down" if ret < 0 else "flat"
            parts.append(f"Total return: {ret:+.2%} ({emoji})")
        if hasattr(results, "win_rate"):
            parts.append(f"Win rate: {results.win_rate:.1%}")
        if hasattr(results, "wall_clock_seconds"):
            parts.append(f"Wall clock: {results.wall_clock_seconds:.1f}s")

        report = getattr(results, "backtest_report", None)
        if report:
            parts.append("")
            parts.append("KEY METRICS (fat-tail aware):")
            parts.append(f"  MAD Ratio: {report.mad_ratio:.4f} (replaces Sharpe -- honest risk measurement)")
            parts.append(f"  Max Drawdown: {report.max_drawdown:.2%} (worst peak-to-trough decline)")
            parts.append(f"  CVaR 99%: {report.cvar_99:.4f} (expected loss in worst 1% of scenarios)")
            parts.append(f"  Tail Exponent: {report.tail_exponent:.2f} (how fat the tails are; <3 = very fat)")
            parts.append(f"  Log Growth Rate: {report.log_growth_rate:.6f} (ergodically correct growth)")
            parts.append(f"  Calmar Ratio: {report.calmar_ratio:.3f} (return per unit of drawdown pain)")
            if report.ruin_probability > 0:
                parts.append(f"  Ruin Probability: {report.ruin_probability:.4f} (chance of catastrophic loss)")
            parts.append(f"  Profit Factor: {report.profit_factor:.2f} (gross profit / gross loss)")

        if hasattr(results, "decisions"):
            risk_rejects = [d for d in results.decisions if d.risk_approved is False]
            if risk_rejects:
                parts.append(f"\nRisk system vetoed {len(risk_rejects)} trades to protect capital.")

        parts.append("")
        if report and report.mad_ratio > 0.3:
            parts.append(
                "ASSESSMENT: Strategy showed positive risk-adjusted returns with honest "
                "fat-tail metrics. The MAD ratio exceeded 0.3, indicating genuine edge."
            )
        elif report and report.total_return > 0:
            parts.append(
                "ASSESSMENT: Strategy was profitable but risk-adjusted returns are modest. "
                "Consider parameter tuning or reviewing signal quality."
            )
        else:
            parts.append(
                "ASSESSMENT: Strategy did not produce positive returns in this period. "
                "This may be due to market conditions, parameter choice, or insufficient data. "
                "Review the decision log for patterns."
            )

        summary = "\n".join(parts)
        self._feed.append(summary)
        return summary

    def narrate_risk_event(self, event_type: str, details: dict[str, Any]) -> str:
        self._risk_event_count += 1
        ts = details.get("timestamp", datetime.utcnow()).strftime("%H:%M:%S") if isinstance(details.get("timestamp"), datetime) else "now"
        reason = details.get("reason", "unspecified")
        daily_pnl = details.get("daily_pnl", 0)
        exposure = details.get("exposure_pct", 0)

        if event_type == "halt":
            entry = (
                f"{ts} -- TRADING HALTED. {reason}. "
                f"All new trades blocked until next session reset. "
                f"This is the circuit breaker protecting capital from further losses."
            )
        elif event_type == "daily_loss_warning":
            daily_limit = details.get("daily_limit", 0.03)
            consumed = abs(daily_pnl / (daily_limit * details.get("equity", 100000))) * 100 if daily_limit else 0
            entry = (
                f"{ts} -- RISK ALERT: Daily loss approaching limit "
                f"(${daily_pnl:+,.2f}, {consumed:.0f}% of cap consumed). "
                f"Tightening position sizes."
            )
        elif event_type == "cvar_breach":
            entry = (
                f"{ts} -- RISK: CVaR limit reached. Position size reduced to meet "
                f"tail-risk constraints. The worst-case loss scenario exceeds our threshold."
            )
        elif event_type == "exposure_limit":
            entry = (
                f"{ts} -- RISK: Exposure limit reached ({exposure:.0%}). "
                f"No new positions until existing ones are reduced."
            )
        elif event_type == "toxicity_warning":
            vpin = details.get("vpin", 0)
            entry = (
                f"{ts} -- Stepping aside. Smart money detected (VPIN: {vpin:.2f}). "
                f"The informed traders appear active -- our edge disappears in these conditions."
            )
        elif event_type == "fragility_warning":
            state = details.get("fragility_state", "unknown")
            entry = (
                f"{ts} -- FRAGILITY ALERT: Strategy is {state}. "
                f"P&L is negatively correlated with volatility -- the strategy loses "
                f"disproportionately when markets get choppy. Consider reducing exposure."
            )
        else:
            entry = f"{ts} -- Risk event ({event_type}): {reason}."

        self._feed.append(entry)
        return entry

    def get_activity_feed(self, last_n: int = 20) -> list[str]:
        feed = list(self._feed)
        return feed[-last_n:]

    def clear_feed(self) -> None:
        self._feed.clear()
        self._trade_count = 0
        self._skip_count = 0
        self._risk_event_count = 0
        self._session_start = None
        self._session_pnl = 0.0

    def _narrate_trade(
        self,
        ts: str,
        tick: Tick,
        decision: TradeDecision,
        signals: dict[str, Signal] | None,
        portfolio: PortfolioState | None,
    ) -> str:
        self._trade_count += 1
        order = decision.order
        signal = decision.signal
        rc = decision.risk_check

        side_str = "Bought" if order.side.value == "buy" else "Sold"
        qty = order.qty
        sym = order.symbol
        price = tick.price

        parts = [f"{ts} -- {side_str} {qty:.0f} shares of {sym} at ${price:.2f}."]

        context_parts = []
        if signal:
            if signal.strength > 0.7:
                context_parts.append("strongly bullish" if order.side.value == "buy" else "strongly bearish")
            else:
                context_parts.append("bullish" if order.side.value == "buy" else "bearish")

            regime = signal.metadata.get("regime", "")
            if regime:
                context_parts.append(f"market is {regime.replace('_', ' ')}")

        if context_parts:
            parts.append(f"The order flow was {context_parts[0]}")
            if len(context_parts) > 1:
                parts[-1] += f" and the {context_parts[1]}"
            parts[-1] += "."

        if rc and rc.kelly_size:
            kelly_pct = abs(rc.kelly_size * price / (portfolio.total_equity if portfolio else 100000)) * 100
            parts.append(f"Position sized at {kelly_pct:.0f}% Kelly.")

        entry = " ".join(parts)
        self._feed.append(entry)
        return entry

    def _narrate_skip(
        self,
        ts: str,
        tick: Tick,
        decision: TradeDecision,
        signals: dict[str, Signal] | None,
    ) -> str:
        self._skip_count += 1
        sym = tick.symbol
        reason = decision.reason
        signal = decision.signal
        rc = decision.risk_check

        if rc and not rc.approved:
            if "daily loss" in rc.reason.lower():
                entry = (
                    f"{ts} -- Skipped {sym}. Risk system vetoed: daily loss limit "
                    f"nearly consumed. Capital preservation overrides signal."
                )
            elif "drawdown" in rc.reason.lower():
                entry = f"{ts} -- Skipped {sym}. Max drawdown threshold reached. Protecting capital."
            elif "exposure" in rc.reason.lower():
                entry = f"{ts} -- Skipped {sym}. Portfolio exposure at maximum. No room for new positions."
            elif "size too small" in rc.reason.lower():
                entry = f"{ts} -- Skipped {sym}. After risk adjustment, position size rounded to zero."
            else:
                entry = f"{ts} -- Skipped {sym}. Risk system said no: {rc.reason}."
        elif signal and "toxic" in reason.lower():
            vpin_val = ""
            if signals and "vpin" in signals:
                vpin_val = f" (VPIN: {signals['vpin'].value:.2f})"
            entry = (
                f"{ts} -- Skipped {sym}. Order flow is toxic{vpin_val}. "
                f"Smart money appears active -- stepping aside."
            )
        elif signal and signal.strength < 0.3:
            entry = f"{ts} -- Watching {sym}. Signal too weak ({signal.strength:.2f}) to act on."
        elif "no composite" in reason.lower() or "no clear direction" in reason.lower():
            entry = f"{ts} -- Watching {sym}. Insufficient signal -- waiting for clarity."
        else:
            entry = f"{ts} -- Skipped {sym}. {reason}."

        if self._skip_count % 50 == 0:
            self._feed.append(entry)
        elif rc and not rc.approved:
            self._feed.append(entry)
        elif signal and "toxic" in reason.lower():
            self._feed.append(entry)

        return entry
