"""
Explainability engine for the HFT agent.

Translates quantitative trading signals, risk decisions, regime detections,
trade executions, halts, portfolio states, and fragility assessments into
plain-English explanations that non-technical stakeholders can understand.

Every public method returns an ``ExplanationBlock`` -- a self-contained unit
carrying a headline, a one-sentence summary, a longer narrative, the raw
numbers, a severity tag, real-world analogies, and a category label.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.risk.fragility import FragilityReport, FragilityState
from core.risk.manager import RiskCheck
from utils.types import Order, PortfolioState, Regime, Side, Signal


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ExplanationBlock:
    """Self-contained explanation of a single agent decision or observation.

    Attributes:
        title:     Short headline (suitable for a dashboard card).
        summary:   One to two plain-English sentences for a non-technical reader.
        detail:    Longer explanation with reasoning chain and context.
        technical: Raw numeric values for programmatic consumers.
        severity:  One of ``"info"``, ``"warning"``, ``"critical"``.
        analogies: Real-world comparisons aimed at non-technical understanding.
        category:  One of ``"signal"``, ``"risk"``, ``"execution"``,
                   ``"regime"``, ``"portfolio"``.
    """

    title: str
    summary: str
    detail: str
    technical: dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    analogies: list[str] = field(default_factory=list)
    category: str = "signal"


# ---------------------------------------------------------------------------
# Concept glossary (used by ``explain_concept``)
# ---------------------------------------------------------------------------

_CONCEPT_EXPLANATIONS: dict[str, str] = {
    "fat_tails": (
        "Financial returns have 'fat tails' -- extreme events happen far more often "
        "than a bell curve predicts. A move that a normal distribution says should "
        "happen once every 10,000 years actually happens every few years. Think of it "
        "like earthquakes: most days are calm, but when a big one hits, it is much "
        "bigger than simple models expect. Our agent treats this as reality, not an "
        "anomaly, and sizes positions accordingly."
    ),
    "kelly_criterion": (
        "The Kelly Criterion tells you the optimal bet size to maximize long-term "
        "wealth growth. Bet too little and you leave money on the table. Bet too much "
        "and a losing streak wipes you out. The key insight: it maximizes the GROWTH "
        "RATE of your wealth (the geometric mean), not the expected profit (the "
        "arithmetic mean). We use 'fractional Kelly' (25% of the theoretical optimum) "
        "because in practice you never know the true odds perfectly, and over-betting "
        "is far more dangerous than under-betting."
    ),
    "ergodicity": (
        "Ergodicity is the most important concept most investors have never heard of. "
        "In an 'ergodic' system, the average outcome across many people equals the "
        "average outcome for one person over time. Financial markets are NOT ergodic. "
        "Example: a coin flip game where you gain 50% on heads and lose 40% on tails. "
        "The AVERAGE across 1000 players goes up. But a SINGLE player over 1000 flips "
        "goes broke. Our agent optimizes for the single-player (time-average) outcome, "
        "which is what actually matters for your one portfolio."
    ),
    "ofi": (
        "Order Flow Imbalance measures the balance of buying vs selling pressure in "
        "the market. When more large orders are coming in on the buy side than the "
        "sell side, the price tends to move up -- and vice versa. It is like watching "
        "who is showing up at an auction: if you see a crowd of aggressive bidders and "
        "few sellers, you can anticipate the price will rise. Research shows OFI "
        "explains about 65% of short-term price changes."
    ),
    "hurst": (
        "The Hurst Exponent measures whether a market is trending, mean-reverting, or "
        "random. H > 0.5: trending (a rising price is likely to keep rising). "
        "H < 0.5: mean-reverting (a rising price is likely to fall back). H = 0.5: "
        "random walk (past tells you nothing). Think of it like weather: some days the "
        "temperature steadily climbs (trending), some days it oscillates around "
        "average (mean-reverting), and some days it is just noise."
    ),
    "vpin": (
        "Volume-Synchronized Probability of Informed Trading measures how much 'smart "
        "money' (institutional traders with better information) is currently trading. "
        "When VPIN is high, it means informed traders are active and the market is "
        "dangerous for everyone else. It is like being at a poker table and realizing "
        "half the players are professionals -- the smart move is to sit out until they "
        "leave. High VPIN preceded the 2010 Flash Crash by about an hour."
    ),
    "multifractal": (
        "Markets are 'multifractal' -- they look similar at different time scales, but "
        "the patterns shift. A chart of 1-minute data often looks like a chart of "
        "daily data. Multifractal analysis measures how 'rough' or 'smooth' the price "
        "path is across different scales. When the multifractal spectrum narrows, the "
        "market is becoming more predictable. When it widens, the market structure is "
        "breaking down and becoming chaotic. Think of it like ocean waves: sometimes "
        "they are regular and predictable, sometimes they are choppy and dangerous."
    ),
    "fragility": (
        "Fragility measures whether a strategy breaks under stress. A 'fragile' "
        "strategy makes small profits in calm markets but loses disproportionately "
        "when volatility spikes -- like selling insurance: steady premiums until the "
        "earthquake hits. An 'antifragile' strategy actually benefits from volatility. "
        "Our agent monitors its own fragility: if it detects that its P&L drops when "
        "volatility rises, it reduces exposure before the next crisis hits."
    ),
    "cvar": (
        "Conditional Value at Risk (CVaR) answers: 'When things go bad, how bad do "
        "they actually get?' Regular VaR says 'you won't lose more than X with 99% "
        "confidence.' CVaR says 'in the worst 1% of cases, you'll lose Y on average.' "
        "CVaR is better because it accounts for extreme events. It is the difference "
        "between saying 'the river usually doesn't flood' (VaR) and 'when it does "
        "flood, here's how much damage to expect' (CVaR)."
    ),
}


# ---------------------------------------------------------------------------
# Explainer
# ---------------------------------------------------------------------------

class Explainer:
    """Translates HFT agent internals into plain-English explanations.

    Every public ``explain_*`` method takes the relevant domain objects and
    returns an :class:`ExplanationBlock` suitable for dashboards, logs, and
    non-technical stakeholders.
    """

    # -- Signal explanation ---------------------------------------------------

    def explain_signal(self, signal: Signal) -> ExplanationBlock:
        """Explain what a trading signal means in plain English.

        Dispatches to specialised handlers for known signal types (OFI, Hurst,
        VPIN, Multifractal, Composite) and falls back to a generic explanation
        for anything else.
        """
        name = signal.name.lower()

        if "ofi" in name:
            return self._explain_ofi(signal)
        if "hurst" in name:
            return self._explain_hurst(signal)
        if "vpin" in name:
            return self._explain_vpin(signal)
        if "multifractal" in name:
            return self._explain_multifractal(signal)
        if "composite" in name:
            return self._explain_composite(signal)

        # Generic fallback
        direction_str = signal.direction.value if signal.direction else "neutral"
        return ExplanationBlock(
            title=f"Signal: {signal.name}",
            summary=(
                f"{signal.name} signal for {signal.symbol} at "
                f"{signal.strength:.2f} strength, direction {direction_str}."
            ),
            detail=(
                f"The {signal.name} signal has value {signal.value:.4f} with "
                f"strength {signal.strength:.2f}/1.0. Direction: {direction_str}. "
                f"The agent uses this as one input among several before deciding "
                f"whether to trade."
            ),
            technical={
                "name": signal.name,
                "symbol": signal.symbol,
                "value": signal.value,
                "strength": signal.strength,
                "direction": direction_str,
                **signal.metadata,
            },
            severity="info",
            analogies=["A trading signal is like a weather forecast -- it gives "
                       "a probabilistic indication, not a guarantee."],
            category="signal",
        )

    # -- Risk decision --------------------------------------------------------

    def explain_risk_decision(
        self,
        risk_check: RiskCheck,
        signal: Signal,
        portfolio: PortfolioState,
    ) -> ExplanationBlock:
        """Explain why a trade was approved or rejected by the risk system.

        Covers Kelly sizing, CVaR limits, exposure limits, daily loss limits,
        and drawdown stops -- all translated into plain English.
        """
        sym = signal.symbol
        direction_str = signal.direction.value.upper() if signal.direction else "NEUTRAL"

        if risk_check.approved:
            return self._explain_risk_approved(risk_check, signal, portfolio)
        return self._explain_risk_rejected(risk_check, signal, portfolio)

    # -- Regime ---------------------------------------------------------------

    def explain_regime(self, regime: Regime, hurst_value: float) -> ExplanationBlock:
        """Explain the current market regime in plain English.

        Args:
            regime:      The detected :class:`Regime` enum value.
            hurst_value: The Hurst exponent that determined the regime.
        """
        descriptions: dict[Regime, str] = {
            Regime.TRENDING: (
                f"The market is TRENDING (Hurst exponent: {hurst_value:.2f}, above "
                f"the 0.5 random threshold). Price moves tend to continue in the same "
                f"direction -- a rise is likely followed by more rises, and a fall by "
                f"more falls. The agent follows momentum, buying what is rising and "
                f"selling what is falling. This is the most favorable regime for "
                f"directional strategies."
            ),
            Regime.MEAN_REVERTING: (
                f"The market is MEAN-REVERTING (Hurst exponent: {hurst_value:.2f}, "
                f"below the 0.5 random threshold). Price moves tend to reverse -- "
                f"overshoots snap back to the average. The agent plays contrarian, "
                f"fading extreme moves: buying after drops and selling after spikes. "
                f"Using a momentum strategy here would be costly."
            ),
            Regime.RANDOM_WALK: (
                f"The market is in a RANDOM WALK (Hurst exponent: {hurst_value:.2f}, "
                f"near 0.5). Past price moves tell us nothing about future direction. "
                f"The agent reduces directional bets and focuses on spread capture "
                f"with smaller position sizes. No directional edge exists."
            ),
            Regime.TOXIC: (
                f"The market flow is TOXIC. Large informed traders appear to be "
                f"operating with superior information (Hurst: {hurst_value:.2f}). "
                f"The agent steps aside entirely to avoid being picked off by "
                f"better-informed counterparties. Trading against informed flow is "
                f"like playing poker against someone who can see your cards."
            ),
        }

        analogies_map: dict[Regime, list[str]] = {
            Regime.TRENDING: [
                "The market is moving like a river flowing downhill -- momentum "
                "carries it forward.",
                "Like a snowball rolling: once it starts, it gathers mass and "
                "keeps going in the same direction.",
            ],
            Regime.MEAN_REVERTING: [
                "Like a rubber band -- the further it stretches from its resting "
                "point, the harder it snaps back.",
                "Like a thermostat: when the temperature overshoots the setpoint, "
                "the system pushes it back.",
            ],
            Regime.RANDOM_WALK: [
                "Like flipping a fair coin -- knowing the last result tells you "
                "nothing about the next one.",
                "Like a leaf blowing in the wind -- each gust is independent of "
                "the last.",
            ],
            Regime.TOXIC: [
                "Large informed traders detected -- like a card counter at a "
                "blackjack table, giving them an unfair edge.",
                "Like realizing the poker table is full of professionals -- the "
                "smart move is to fold and wait.",
            ],
        }

        severity = "info"
        if regime == Regime.TOXIC:
            severity = "critical"
        elif regime == Regime.RANDOM_WALK:
            severity = "warning"

        return ExplanationBlock(
            title=f"Market Regime: {regime.value.replace('_', ' ').title()}",
            summary=(
                f"Market is {regime.value.replace('_', ' ')} "
                f"(Hurst: {hurst_value:.2f})."
            ),
            detail=descriptions.get(
                regime,
                f"Unknown regime with Hurst exponent {hurst_value:.2f}.",
            ),
            technical={
                "regime": regime.value,
                "hurst": hurst_value,
            },
            severity=severity,
            analogies=analogies_map.get(regime, []),
            category="regime",
        )

    # -- Trade execution ------------------------------------------------------

    def explain_trade(
        self,
        order: Order,
        signal: Signal,
        risk_check: RiskCheck,
    ) -> ExplanationBlock:
        """Explain a trade execution: what was done, why, and how it was sized.

        Covers the order itself, the signal that triggered it, the regime
        context, and the risk sizing that shaped the final quantity.
        """
        side = order.side.value.upper()
        sym = order.symbol
        qty = order.qty
        order_type = order.order_type.value
        price_str = f"${order.limit_price:.2f}" if order.limit_price else "market price"

        pressure = "buying" if side == "BUY" else "selling"

        # Build the reasoning chain
        reasons: list[str] = [
            f"The agent executed a {side} of {qty:.0f} shares of {sym} "
            f"at {price_str} ({order_type} order).",
            "",
            "Why this trade:",
        ]

        # (1) Signal
        sig_strength_label = "strong" if signal.strength > 0.6 else "moderate"
        reasons.append(
            f"  1. Order flow shows {sig_strength_label} {pressure} pressure "
            f"(signal strength: {signal.strength:.2f}/1.0)."
        )

        # (2) Regime context
        regime = signal.metadata.get("regime", "")
        if regime:
            regime_label = regime.replace("_", " ")
            if regime == "trending":
                reasons.append(
                    f"  2. The market is {regime_label}, so the agent follows "
                    f"momentum -- going with the flow."
                )
            elif regime == "mean_reverting":
                reasons.append(
                    f"  2. The market is {regime_label}, so the agent plays "
                    f"contrarian -- fading the move."
                )
            else:
                reasons.append(
                    f"  2. The market regime is {regime_label}."
                )

        # (3) Risk sizing
        if risk_check.kelly_size is not None:
            theoretical = abs(risk_check.kelly_size)
            if theoretical > qty:
                reasons.append(
                    f"  3. Risk system approved {qty:.0f} shares (reduced from "
                    f"theoretical {theoretical:.0f} to protect against tail events "
                    f"and parameter uncertainty)."
                )
            else:
                reasons.append(
                    f"  3. Risk system approved full size of {qty:.0f} shares."
                )
        else:
            reasons.append(
                f"  3. Risk system approved position size of {qty:.0f} shares."
            )

        # (4) CVaR
        if risk_check.cvar is not None:
            reasons.append(
                f"  4. Worst-case expected loss (CVaR): ${risk_check.cvar:,.2f}."
            )

        # Execution method note
        if order_type == "limit":
            reasons.append(
                f"\nExecution: Used a limit order at {price_str} to capture "
                f"the bid-ask spread rather than crossing it."
            )

        return ExplanationBlock(
            title=f"{side} {sym}",
            summary=(
                f"{'Bought' if side == 'BUY' else 'Sold'} {qty:.0f} shares "
                f"of {sym} at {price_str}."
            ),
            detail="\n".join(reasons),
            technical={
                "side": side,
                "symbol": sym,
                "qty": qty,
                "order_type": order_type,
                "limit_price": order.limit_price,
                "signal_strength": signal.strength,
                "signal_direction": signal.direction.value if signal.direction else None,
                "kelly_size": risk_check.kelly_size,
                "cvar": risk_check.cvar,
                "exposure_pct": risk_check.exposure_pct,
            },
            severity="info",
            analogies=[
                "Like a poker player betting proportional to their edge -- enough "
                "to grow but not enough to go bust.",
                f"The agent saw a crowd of {pressure.rstrip('ing')}ers forming "
                f"and joined before the price moves further.",
            ],
            category="execution",
        )

    # -- Trading halt ---------------------------------------------------------

    def explain_halt(self, reason: str, source: str) -> ExplanationBlock:
        """Explain a trading halt -- why the agent stopped trading entirely.

        Args:
            reason: Human-readable reason the halt was triggered (e.g.
                    ``"Daily loss limit hit: -3.20%"``).
            source: Which subsystem triggered the halt (e.g. ``"risk_manager"``,
                    ``"surveillance"``, ``"manual"``).
        """
        source_labels: dict[str, str] = {
            "risk_manager": "the risk management system",
            "surveillance": "the surveillance agent",
            "manual": "a manual override",
            "coordinator": "the agent coordinator",
            "fragility": "the fragility detector",
        }
        source_label = source_labels.get(source, source)

        # Determine which kind of halt and craft the narrative
        detail_parts: list[str] = [
            f"ALL TRADING HAS BEEN HALTED by {source_label}.",
            f"Reason: {reason}.",
            "",
        ]

        reason_lower = reason.lower()
        if "daily loss" in reason_lower:
            detail_parts.append(
                "The agent's losses today have reached the pre-set daily limit. "
                "This is a hard stop -- no new trades will be placed until the next "
                "trading session begins. The purpose is to prevent a bad day from "
                "becoming a catastrophic day. Even if the market immediately "
                "rebounds, the agent stays out. Discipline over conviction."
            )
        elif "drawdown" in reason_lower:
            detail_parts.append(
                "The portfolio has fallen too far from its peak value. This "
                "drawdown stop prevents the agent from digging a deeper hole. "
                "Recovery from large drawdowns requires disproportionate gains "
                "(a 50% loss needs a 100% gain to recover), so cutting losses "
                "early is mathematically critical."
            )
        elif "toxic" in reason_lower or "vpin" in reason_lower:
            detail_parts.append(
                "Informed traders appear to dominate the current order flow. "
                "Continuing to trade would be like playing poker against opponents "
                "who can see your cards. The agent will resume when toxicity "
                "returns to normal levels."
            )
        elif "fragil" in reason_lower:
            detail_parts.append(
                "The agent's strategy has become fragile -- its P&L drops "
                "disproportionately when volatility rises. This is the trading "
                "equivalent of selling earthquake insurance right before seismic "
                "activity increases. The halt prevents further exposure to a "
                "structurally vulnerable position."
            )
        else:
            detail_parts.append(
                "The halt acts as a circuit breaker, preventing further losses "
                "and giving the system time to reassess conditions. No new "
                "positions will be opened until the halt is lifted."
            )

        detail_parts.append(
            "\nThis is by design. As Nassim Taleb writes: 'The first rule is to "
            "survive.' A single catastrophic loss permanently removes the agent "
            "from the game -- there is no recovery from zero."
        )

        return ExplanationBlock(
            title="Trading Halted",
            summary=f"All trading stopped. {reason}.",
            detail="\n".join(detail_parts),
            technical={
                "reason": reason,
                "source": source,
                "halted": True,
            },
            severity="critical",
            analogies=[
                "Like a circuit breaker in an electrical panel -- it cuts power "
                "automatically when things get dangerous, preventing a fire.",
                "Like a pilot pulling up when wind shear is detected -- better "
                "to abort the landing and go around than risk a crash.",
            ],
            category="risk",
        )

    # -- Portfolio state ------------------------------------------------------

    def explain_portfolio(self, portfolio_state: PortfolioState) -> ExplanationBlock:
        """Explain the current portfolio state in plain English."""
        equity = portfolio_state.total_equity
        cash = portfolio_state.cash
        exposure = portfolio_state.exposure_pct
        positions = portfolio_state.positions
        drawdown = portfolio_state.max_drawdown
        daily_pnl = portfolio_state.daily_pnl

        # Position details
        pos_lines: list[str] = []
        for sym, pos in positions.items():
            direction = "LONG" if pos.qty > 0 else "SHORT"
            pos_lines.append(
                f"  {sym}: {direction} {abs(pos.qty):.0f} shares "
                f"@ ${pos.avg_entry_price:.2f} "
                f"(current: ${pos.current_price:.2f}, "
                f"unrealized: ${pos.unrealized_pnl:+,.2f})"
            )

        detail = (
            f"Total equity: ${equity:,.2f}\n"
            f"Cash available: ${cash:,.2f}\n"
            f"Total exposure: {exposure:.1%} of equity\n"
            f"Daily P&L: ${daily_pnl:+,.2f}\n"
            f"Max drawdown: {drawdown:.2%}\n"
        )
        if pos_lines:
            detail += (
                f"\nOpen positions ({len(positions)}):\n"
                + "\n".join(pos_lines)
            )
        else:
            detail += "\nNo open positions -- fully in cash."

        detail += (
            "\n\nPosition sizing uses fractional Kelly (25% of theoretical "
            "optimum). This sacrifices roughly 44% of optimal growth rate but "
            "reduces drawdown risk by roughly 75%. Every proposed trade must "
            "pass CVaR limits, daily loss limits, and drawdown stops before "
            "execution."
        )

        severity = "info"
        if drawdown > 0.08:
            severity = "critical"
        elif drawdown > 0.05:
            severity = "warning"

        return ExplanationBlock(
            title="Portfolio Summary",
            summary=(
                f"Equity ${equity:,.2f}, {len(positions)} position(s), "
                f"{exposure:.0%} exposed, daily P&L ${daily_pnl:+,.2f}."
            ),
            detail=detail,
            technical={
                "equity": equity,
                "cash": cash,
                "exposure_pct": exposure,
                "positions": {
                    s: {
                        "qty": p.qty,
                        "avg_entry_price": p.avg_entry_price,
                        "current_price": p.current_price,
                        "unrealized_pnl": p.unrealized_pnl,
                    }
                    for s, p in positions.items()
                },
                "daily_pnl": daily_pnl,
                "drawdown": drawdown,
            },
            severity=severity,
            analogies=[
                "Your portfolio is like a ship: equity is the hull, positions "
                "are cargo, and exposure is how much cargo you are carrying "
                "relative to capacity. Too much cargo in rough seas capsizes "
                "even the strongest vessel.",
            ],
            category="portfolio",
        )

    # -- Fragility ------------------------------------------------------------

    def explain_fragility(self, fragility_report: FragilityReport) -> ExplanationBlock:
        """Explain a fragility assessment in plain English.

        The fragility framework (Taleb & Douady 2012) classifies strategies
        as fragile, robust, or antifragile based on their sensitivity to
        volatility changes.
        """
        state = fragility_report.state
        vega = fragility_report.vega
        vol_sensitivity = fragility_report.vol_sensitivity
        recommendation = fragility_report.recommendation

        state_labels: dict[FragilityState, tuple[str, str, str]] = {
            FragilityState.FRAGILE: (
                "FRAGILE",
                "critical",
                (
                    f"The strategy is FRAGILE (volatility sensitivity: "
                    f"{vol_sensitivity:+.2f}, vega: {vega:+.4f}). This means "
                    f"the agent's P&L drops disproportionately when market "
                    f"volatility increases. In calm markets, the strategy "
                    f"collects small, steady profits. But when a volatility "
                    f"spike hits, losses far exceed those gains.\n\n"
                    f"This is the most dangerous payoff profile in finance -- "
                    f"it feels safe right up until it is not. Many funds that "
                    f"blew up (LTCM, XIV) had exactly this shape: steady "
                    f"returns punctuated by catastrophic losses.\n\n"
                    f"Recommended action: {recommendation}"
                ),
            ),
            FragilityState.ROBUST: (
                "ROBUST",
                "info",
                (
                    f"The strategy is ROBUST (volatility sensitivity: "
                    f"{vol_sensitivity:+.2f}, vega: {vega:+.4f}). P&L has "
                    f"limited sensitivity to changes in market volatility. "
                    f"The strategy neither benefits from nor is harmed by "
                    f"volatility spikes.\n\n"
                    f"This is an acceptable risk profile. The strategy can "
                    f"withstand normal market turbulence without outsized "
                    f"losses.\n\n"
                    f"Assessment: {recommendation}"
                ),
            ),
            FragilityState.ANTIFRAGILE: (
                "ANTIFRAGILE",
                "info",
                (
                    f"The strategy is ANTIFRAGILE (volatility sensitivity: "
                    f"{vol_sensitivity:+.2f}, vega: {vega:+.4f}). The agent's "
                    f"P&L actually improves when market volatility increases. "
                    f"This is the ideal payoff profile -- the strategy benefits "
                    f"from disorder.\n\n"
                    f"Antifragile strategies are rare and valuable. They act as "
                    f"natural hedges: when everything else in the portfolio "
                    f"suffers during a crisis, this strategy gains.\n\n"
                    f"Assessment: {recommendation}"
                ),
            ),
        }

        label, severity, detail = state_labels.get(
            state,
            ("UNKNOWN", "warning", f"Unknown fragility state. Vega: {vega:+.4f}."),
        )

        analogies_map: dict[FragilityState, list[str]] = {
            FragilityState.FRAGILE: [
                "Like selling earthquake insurance -- you collect steady premiums "
                "until the big one hits, then the payout dwarfs everything you "
                "ever collected.",
                "Like a turkey being fed every day -- each day 'confirms' that "
                "the farmer is a friend, right up until Thanksgiving.",
            ],
            FragilityState.ROBUST: [
                "Like a well-built house -- it can handle normal storms without "
                "damage, though a hurricane would still be trouble.",
                "Like a diversified diet -- no single food group dominates, "
                "so a shortage of one does not cause a crisis.",
            ],
            FragilityState.ANTIFRAGILE: [
                "Like a vaccine -- exposure to small stresses (volatility) "
                "makes the system stronger, not weaker.",
                "Like a hydra: cut off one head, two grow back. Disorder "
                "actually makes the strategy perform better.",
            ],
        }

        return ExplanationBlock(
            title=f"Fragility: {label}",
            summary=(
                f"Strategy is {label.lower()} -- "
                f"{'loses disproportionately' if state == FragilityState.FRAGILE else 'unaffected by' if state == FragilityState.ROBUST else 'benefits from'}"
                f" volatility spikes."
            ),
            detail=detail,
            technical={
                "state": state.value,
                "vega": vega,
                "gamma": getattr(fragility_report, "gamma", None),
                "vol_sensitivity": vol_sensitivity,
                "recommendation": recommendation,
            },
            severity=severity,
            analogies=analogies_map.get(state, []),
            category="risk",
        )

    # -- Concept glossary (public helper) -------------------------------------

    def explain_concept(self, concept: str) -> str:
        """Return a plain-English explanation of a trading concept.

        Falls back to a not-found message for unknown concepts.
        """
        key = concept.lower().strip()
        return _CONCEPT_EXPLANATIONS.get(
            key,
            f"No explanation available for '{concept}'.",
        )

    # ======================================================================
    # Private helpers -- signal subtypes
    # ======================================================================

    def _explain_ofi(self, signal: Signal) -> ExplanationBlock:
        """Explain an Order Flow Imbalance signal."""
        strength = signal.strength
        direction = signal.direction
        meta = signal.metadata
        pressure = "buying" if direction and direction == Side.BUY else "selling"
        strength_label = "strong" if strength > 0.6 else "moderate" if strength > 0.3 else "weak"

        severity = "warning" if strength > 0.7 else "info"

        summary = (
            f"Order flow shows {strength_label} {pressure} pressure for "
            f"{signal.symbol} (strength: {strength:.2f}/1.0)."
        )

        detail = (
            f"There are significantly more "
            f"{'buyers' if pressure == 'buying' else 'sellers'} than "
            f"{'sellers' if pressure == 'buying' else 'buyers'} for "
            f"{signal.symbol} right now. The {pressure} pressure is "
            f"{strength_label} (strength: {strength:.2f}/1.0).\n\n"
            f"Order Flow Imbalance (OFI) is the primary signal the agent uses. "
            f"Academic research shows it explains about 65% of short-term price "
            f"changes. When this pressure is strong enough and the regime is "
            f"favorable, the agent will place a trade in the direction of the "
            f"flow."
        )

        return ExplanationBlock(
            title=f"Order Flow: {pressure.upper()} Pressure",
            summary=summary,
            detail=detail,
            technical={
                "ofi_value": signal.value,
                "strength": strength,
                "direction": direction.value if direction else "neutral",
                **meta,
            },
            severity=severity,
            analogies=[
                "More buyers lining up than sellers, like a popular concert "
                "where demand exceeds tickets -- the price gets bid up.",
                "Order flow is the closest thing to reading the market's mind "
                "in real time.",
            ],
            category="signal",
        )

    def _explain_hurst(self, signal: Signal) -> ExplanationBlock:
        """Explain a Hurst exponent signal."""
        h = signal.value
        meta = signal.metadata
        regime = meta.get("regime", "random_walk")
        duration = meta.get("regime_duration_minutes", 0)

        if h > 0.55:
            regime_label = "TRENDING"
            behavior = "price moves tend to continue in the same direction"
            action = "follows the trend rather than betting against it"
        elif h < 0.45:
            regime_label = "MEAN-REVERTING"
            behavior = "price moves tend to reverse -- overshoots snap back"
            action = "plays contrarian, fading extreme moves"
        else:
            regime_label = "RANDOM WALK"
            behavior = "past price moves give no information about future direction"
            action = "reduces directional bets and focuses on spread capture"

        detail = (
            f"The market for {signal.symbol} is in a {regime_label} regime "
            f"(Hurst exponent: {h:.2f}). This means {behavior}. The agent "
            f"{action}."
        )
        if duration > 0:
            detail += (
                f" This regime has persisted for the last "
                f"{duration:.0f} minutes."
            )

        return ExplanationBlock(
            title=f"Regime: {regime_label}",
            summary=f"{signal.symbol} is {regime_label.lower()} (Hurst: {h:.2f}).",
            detail=detail,
            technical={"hurst": h, "regime": regime, **meta},
            severity="warning" if regime_label == "RANDOM WALK" else "info",
            analogies=[
                "The market is moving like a river flowing downhill -- momentum "
                "carries it forward."
                if h > 0.55
                else "Like a rubber band -- the further it stretches, the harder "
                "it snaps back."
                if h < 0.45
                else "Like flipping a fair coin -- past results tell you nothing "
                "about the next flip.",
            ],
            category="signal",
        )

    def _explain_vpin(self, signal: Signal) -> ExplanationBlock:
        """Explain a VPIN toxicity signal."""
        vpin = signal.value
        meta = signal.metadata
        is_toxic = meta.get("is_toxic", False)

        if vpin > 0.8:
            severity = "critical"
            level = "VERY HIGH"
        elif vpin > 0.6:
            severity = "warning"
            level = "HIGH" if is_toxic else "ELEVATED"
        else:
            severity = "info"
            level = "NORMAL"

        if is_toxic:
            detail = (
                f"Order flow toxicity is {level} (VPIN: {vpin:.2f}). 'Smart "
                f"money' -- institutional traders with better information -- "
                f"appears to be trading aggressively. This pattern resembles "
                f"conditions seen before major market dislocations (VPIN "
                f"produced a warning signal over an hour before the 2010 Flash "
                f"Crash). The agent is reducing exposure to protect capital."
            )
        else:
            detail = (
                f"Order flow toxicity is {level} (VPIN: {vpin:.2f}). The market "
                f"appears to be trading normally with no unusual informed "
                f"activity. It is safe for the agent to trade at normal position "
                f"sizes."
            )

        return ExplanationBlock(
            title=f"Toxicity: {level}",
            summary=(
                f"VPIN toxicity is {level.lower()} ({vpin:.2f}). "
                f"{'Agent reducing exposure.' if is_toxic else 'Normal conditions.'}"
            ),
            detail=detail,
            technical={"vpin": vpin, "is_toxic": is_toxic, **meta},
            severity=severity,
            analogies=[
                "VPIN toxic flow is like a card counter at a blackjack table "
                "-- giving informed traders an unfair edge. Best to sit out.",
                "Like a canary in a coal mine -- VPIN warns of danger before "
                "it becomes obvious to everyone.",
            ],
            category="signal",
        )

    def _explain_multifractal(self, signal: Signal) -> ExplanationBlock:
        """Explain a multifractal market-structure signal."""
        meta = signal.metadata
        stability = meta.get("stability_score", 1.0)
        width = meta.get("spectrum_width", 0)

        if stability < 0.3:
            level = "UNSTABLE"
            severity = "critical"
        elif stability < 0.6:
            level = "DEGRADING"
            severity = "warning"
        else:
            level = "STABLE"
            severity = "info"

        if stability < 0.3:
            detail = (
                f"Market microstructure is {level} (stability: "
                f"{stability:.2f}). The multifractal spectrum is widening, "
                f"meaning market structure is breaking down. Price patterns are "
                f"becoming chaotic across multiple time scales. Position sizes "
                f"are being reduced as a precaution."
            )
        elif stability < 0.6:
            detail = (
                f"Market microstructure is {level} (stability: "
                f"{stability:.2f}). Some degradation in market structure "
                f"detected. The usual price patterns are less reliable than "
                f"normal. The agent is exercising additional caution."
            )
        else:
            detail = (
                f"Market microstructure is {level} (stability: "
                f"{stability:.2f}). Market structure is healthy and price "
                f"patterns are consistent across time scales, making signals "
                f"more reliable."
            )

        return ExplanationBlock(
            title=f"Market Structure: {level}",
            summary=(
                f"Microstructure is {level.lower()} "
                f"(stability: {stability:.2f})."
            ),
            detail=detail,
            technical={
                "stability": stability,
                "spectrum_width": width,
                **meta,
            },
            severity=severity,
            analogies=[
                "Like checking if the ice is solid before skating -- when "
                "market structure degrades, the foundation becomes unreliable "
                "and you slow down or stop.",
            ],
            category="signal",
        )

    def _explain_composite(self, signal: Signal) -> ExplanationBlock:
        """Explain a composite (aggregated) signal."""
        strength = signal.strength
        direction = signal.direction
        meta = signal.metadata
        regime = meta.get("regime", "random_walk")
        toxicity_discount = meta.get("toxicity_discount", 1.0)
        stability_discount = meta.get("stability_discount", 1.0)
        raw_ofi = meta.get("raw_ofi_strength", 0.0)
        components = meta.get("component_signals", [])

        dir_str = direction.value.upper() if direction else "NEUTRAL"

        parts: list[str] = [
            f"The combined signal points {dir_str} with composite strength "
            f"{strength:.3f}.",
            "",
            "How it was calculated:",
            f"  - Raw order flow strength: {raw_ofi:.3f}",
            f"  - Regime ({regime.replace('_', ' ')}): weight applied to raw signal",
        ]
        if toxicity_discount < 1.0:
            parts.append(
                f"  - Toxicity discount: {toxicity_discount:.0%} (signal "
                f"reduced due to informed trading activity)"
            )
        if stability_discount < 1.0:
            parts.append(
                f"  - Stability discount: {stability_discount:.0%} (signal "
                f"reduced due to structural instability)"
            )
        parts.append(f"  - Component signals used: {', '.join(components)}")

        return ExplanationBlock(
            title=f"Composite Signal: {dir_str}",
            summary=(
                f"Combined {dir_str} signal at {strength:.3f} strength "
                f"({regime.replace('_', ' ')} regime)."
            ),
            detail="\n".join(parts),
            technical={
                "strength": strength,
                "direction": dir_str,
                **meta,
            },
            severity="warning" if strength > 0.7 else "info",
            analogies=[
                "The composite signal is like a vote -- all the individual "
                "signals (OFI, Hurst, VPIN, multifractal) contribute, weighted "
                "by how reliable each is in the current conditions.",
            ],
            category="signal",
        )

    # ======================================================================
    # Private helpers -- risk sub-explanations
    # ======================================================================

    def _explain_risk_approved(
        self,
        risk_check: RiskCheck,
        signal: Signal,
        portfolio: PortfolioState,
    ) -> ExplanationBlock:
        """Build explanation for an approved trade."""
        sym = signal.symbol
        direction_str = signal.direction.value.upper() if signal.direction else "NEUTRAL"
        qty = risk_check.adjusted_qty

        parts: list[str] = [
            f"Trade APPROVED for {sym} ({direction_str}).",
            "",
            "The risk system checked the following and all passed:",
        ]

        # Kelly sizing
        if risk_check.kelly_size is not None:
            theoretical = abs(risk_check.kelly_size)
            parts.append(
                f"  1. Position sizing (Fractional Kelly): {qty:.0f} shares "
                f"approved."
            )
            if theoretical > qty:
                parts.append(
                    f"     The theoretical optimum was {theoretical:.0f} shares, "
                    f"but the agent uses only 25% of Kelly to guard against "
                    f"parameter uncertainty."
                )
        else:
            parts.append(
                f"  1. Position sizing: {qty:.0f} shares approved."
            )

        # CVaR
        if risk_check.cvar is not None:
            parts.append(
                f"  2. Tail-risk check (CVaR): Worst-case expected loss is "
                f"${risk_check.cvar:,.2f}, within limits."
            )

        # Exposure
        if risk_check.exposure_pct is not None:
            parts.append(
                f"  3. Portfolio exposure: {risk_check.exposure_pct:.1%} of "
                f"equity (within limits)."
            )

        # Daily loss and drawdown (implied pass)
        parts.append(
            "  4. Daily loss limit: not breached."
        )
        parts.append(
            "  5. Drawdown limit: not breached."
        )

        return ExplanationBlock(
            title=f"Risk Approved: {direction_str} {sym}",
            summary=(
                f"Risk system approved {direction_str} trade on {sym} for "
                f"{qty:.0f} shares."
            ),
            detail="\n".join(parts),
            technical={
                "approved": True,
                "adjusted_qty": qty,
                "kelly_size": risk_check.kelly_size,
                "cvar": risk_check.cvar,
                "exposure_pct": risk_check.exposure_pct,
                "signal_strength": signal.strength,
                "portfolio_equity": portfolio.total_equity,
            },
            severity="info",
            analogies=[
                "Like a poker player betting proportional to their edge -- "
                "enough to grow but not enough to go bust.",
                "The worst-case scenario planning passed -- not just how bad "
                "could it get, but how bad when it is really bad (CVaR).",
            ],
            category="risk",
        )

    def _explain_risk_rejected(
        self,
        risk_check: RiskCheck,
        signal: Signal,
        portfolio: PortfolioState,
    ) -> ExplanationBlock:
        """Build explanation for a rejected trade."""
        sym = signal.symbol
        direction_str = signal.direction.value.upper() if signal.direction else "NEUTRAL"
        reason = risk_check.reason

        parts: list[str] = [
            f"Trade REJECTED for {sym} ({direction_str}).",
            f"Reason: {reason}.",
            "",
        ]

        reason_lower = reason.lower()

        if "daily loss" in reason_lower:
            parts.append(
                "The agent's daily losses have reached the pre-set limit. No "
                "new trades are allowed until the next trading session. This "
                "prevents a bad day from becoming a catastrophic one."
            )
        elif "drawdown" in reason_lower:
            parts.append(
                "The portfolio has fallen too far from its peak. The drawdown "
                "stop is a hard limit that prevents the agent from trying to "
                "'trade its way out' of a losing streak, which almost always "
                "makes things worse."
            )
        elif "exposure" in reason_lower:
            parts.append(
                "The portfolio is already too concentrated. Adding another "
                "position would exceed the maximum exposure limit, increasing "
                "the risk of correlated losses."
            )
        elif "size too small" in reason_lower:
            parts.append(
                "After applying all risk adjustments (Kelly sizing, CVaR "
                "limits, exposure scaling), the optimal position size rounded "
                "down to zero. The expected edge is too small relative to the "
                "risk to justify any trade."
            )
        elif "halted" in reason_lower:
            parts.append(
                "Trading has been halted entirely. The circuit breaker has "
                "been tripped and will not reset until conditions improve or "
                "the session resets."
            )
        else:
            parts.append(
                "The risk system determined that the potential downside of "
                "this trade outweighs the expected benefit."
            )

        if signal.strength > 0.5:
            parts.append(
                f"\nNote: the signal was relatively strong "
                f"(strength: {signal.strength:.2f}), but preserving capital "
                f"always takes absolute priority over potential profit. "
                f"As Nassim Taleb says: 'The first rule is to survive.'"
            )

        return ExplanationBlock(
            title=f"Risk Rejected: {sym}",
            summary=f"Risk system vetoed {direction_str} trade on {sym}. {reason}.",
            detail="\n".join(parts),
            technical={
                "approved": False,
                "reason": reason,
                "adjusted_qty": risk_check.adjusted_qty,
                "kelly_size": risk_check.kelly_size,
                "cvar": risk_check.cvar,
                "exposure_pct": risk_check.exposure_pct,
                "signal_strength": signal.strength,
                "portfolio_equity": portfolio.total_equity,
                "portfolio_drawdown": portfolio.max_drawdown,
            },
            severity="warning",
            analogies=[
                "Sometimes the best trade is no trade -- like a batter letting "
                "a pitch pass because it is outside the strike zone.",
                "The risk system acts as a hard veto -- even a strong signal "
                "cannot override it, just as a co-pilot's emergency stop "
                "overrides the captain.",
            ],
            category="risk",
        )
