"""
HFT Agent — Main Application Entry Point

High-Frequency Trading Agent with Fat-Tail Aware Risk Management.
Built on the research framework from Taleb, Cont, Peters, Mandelbrot et al.

Architecture:
    Data Feed → Signal Aggregator → Strategy → Risk Manager → Execution Engine → Broker
         ↓              ↓                                              ↓
    TimescaleDB     Redis Cache                                  Order Tracking

Usage:
    # Paper trading (default)
    python main.py

    # Live trading (requires explicit flag)
    python main.py --mode live

    # Backtest mode
    python main.py --backtest --start 2024-01-01 --end 2024-12-31
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from brokers.alpaca_broker import AlpacaBroker
from brokers.base import Broker
from brokers.ibkr import IBKRBroker
from brokers.robinhood import RobinhoodBroker
from core.risk.manager import RiskManager
from core.signals.aggregator import SignalAggregator
from data.feeds.alpaca_feed import AlpacaDataFeed
from data.storage.redis_cache import RedisCache
from data.storage.timescale import TimescaleStore
from execution.engine import ExecutionEngine
from strategies.adaptive_microstructure import AdaptiveMicrostructureStrategy
from utils.config import Settings, load_settings
from utils.logging import get_logger, setup_logging
from utils.types import OrderBook, PortfolioState, Tick

logger = get_logger(__name__)


class HFTAgent:
    """Main HFT Agent orchestrator.

    Connects all components and manages the trading loop.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._running = False

        # Components (initialized in start())
        self._broker: Broker | None = None
        self._data_feed: AlpacaDataFeed | None = None
        self._db: TimescaleStore | None = None
        self._cache: RedisCache | None = None
        self._signals: SignalAggregator | None = None
        self._risk: RiskManager | None = None
        self._strategy: AdaptiveMicrostructureStrategy | None = None
        self._execution: ExecutionEngine | None = None
        self._portfolio: PortfolioState | None = None

    async def start(self) -> None:
        """Initialize all components and start the trading loop."""
        setup_logging(self._settings.app.log_level)

        logger.info(
            "hft_agent_starting",
            mode=self._settings.app.mode,
            broker=self._settings.brokers.primary,
            symbols=self._settings.data.symbols,
        )

        # Safety check for live mode
        if self._settings.app.mode == "live":
            logger.warning("LIVE TRADING MODE — Real money at risk")

        try:
            await self._init_components()
            await self._run_trading_loop()
        except KeyboardInterrupt:
            logger.info("shutdown_requested")
        except Exception as e:
            logger.error("fatal_error", error=str(e), exc_info=True)
        finally:
            await self._shutdown()

    async def _init_components(self) -> None:
        """Initialize all system components."""
        # 1. Database
        try:
            self._db = TimescaleStore(
                dsn=self._settings.database.timescaledb.dsn,
                pool_size=self._settings.database.timescaledb.pool_size,
            )
            await self._db.connect()
            await self._db.initialize_schema()
        except Exception as e:
            logger.warning("timescaledb_unavailable", error=str(e)[:100])
            self._db = None

        # 2. Redis cache
        try:
            self._cache = RedisCache(
                host=self._settings.database.redis.host,
                port=self._settings.database.redis.port,
                db=self._settings.database.redis.db,
            )
            await self._cache.connect()
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e)[:100])
            self._cache = None

        # 3. Broker
        self._broker = self._create_broker()
        await self._broker.connect()

        # 4. Get initial portfolio state
        self._portfolio = await self._broker.get_account()
        logger.info(
            "portfolio_loaded",
            equity=self._portfolio.total_equity,
            cash=self._portfolio.cash,
            positions=len(self._portfolio.positions),
        )

        # 5. Signal aggregator
        self._signals = SignalAggregator(self._settings.signals)

        # 6. Risk manager
        self._risk = RiskManager(
            config=self._settings.risk,
            initial_equity=self._portfolio.total_equity,
        )

        # 7. Strategy
        self._strategy = AdaptiveMicrostructureStrategy(
            config=self._settings.strategy,
            signal_aggregator=self._signals,
            risk_manager=self._risk,
        )

        # 8. Execution engine
        self._execution = ExecutionEngine(
            broker=self._broker,
            config=self._settings.execution,
            redis_cache=self._cache,
            max_orders_per_second=self._settings.strategy.max_orders_per_second,
        )

        # 9. Data feed
        self._data_feed = AlpacaDataFeed(
            symbols=self._settings.data.symbols,
            api_key=os.environ.get("ALPACA_API_KEY", ""),
            secret_key=os.environ.get("ALPACA_SECRET_KEY", ""),
            feed=self._settings.brokers.alpaca.data_feed,
        )

        # Register callbacks
        self._data_feed.on_tick(self._on_tick)
        self._data_feed.on_orderbook(self._on_orderbook)

        logger.info("all_components_initialized")

    def _create_broker(self) -> Broker:
        """Create the appropriate broker instance."""
        primary = self._settings.brokers.primary

        if primary == "robinhood":
            return RobinhoodBroker()
        elif primary == "alpaca":
            return AlpacaBroker(
                base_url=self._settings.brokers.alpaca.base_url,
            )
        elif primary == "ibkr":
            cfg = self._settings.brokers.ibkr
            return IBKRBroker(
                host=cfg.host,
                port=cfg.port,
                client_id=cfg.client_id,
            )
        else:
            raise ValueError(f"Unknown broker: {primary}")

    async def _on_tick(self, tick: Tick) -> None:
        """Handle incoming tick data."""
        if not self._strategy or not self._portfolio or not self._execution:
            return

        # Store tick in database
        if self._db:
            await self._db.insert_tick(tick)

        # Run strategy
        decision = self._strategy.on_tick(tick, self._portfolio)

        if decision.should_trade and decision.order:
            # Execute the trade
            filled_order = await self._execution.execute(decision.order)

            # Update portfolio
            self._portfolio = await self._broker.get_account()

            # Cache signal
            if self._cache and decision.signal:
                await self._cache.set_signal(decision.signal)

    async def _on_orderbook(self, book: OrderBook) -> None:
        """Handle incoming order book update."""
        if not self._strategy or not self._portfolio or not self._execution:
            return

        # Cache order book
        if self._cache:
            await self._cache.set_orderbook(book)

        # Store in database
        if self._db:
            await self._db.insert_orderbook(book)

        # Run strategy on order book update
        decision = self._strategy.on_orderbook(book, self._portfolio)

        if decision.should_trade and decision.order:
            filled_order = await self._execution.execute(decision.order)
            self._portfolio = await self._broker.get_account()

    async def _run_trading_loop(self) -> None:
        """Main trading loop."""
        self._running = True

        # Connect and subscribe to data feed
        await self._data_feed.connect()
        await self._data_feed.subscribe()

        logger.info("trading_loop_started")

        # Start the data feed (this blocks until stopped)
        # Also run periodic tasks in the background
        await asyncio.gather(
            self._data_feed.start(),
            self._periodic_tasks(),
        )

    async def _periodic_tasks(self) -> None:
        """Background periodic tasks (portfolio sync, fill checks, etc.)."""
        while self._running:
            try:
                # Check for fills every second
                if self._execution:
                    fills = await self._execution.check_fills()
                    for fill in fills:
                        logger.info(
                            "fill_detected",
                            symbol=fill.symbol,
                            side=fill.side.value,
                            qty=fill.qty,
                        )

                # Update portfolio every 5 seconds
                if self._broker and self._broker.is_connected:
                    self._portfolio = await self._broker.get_account()

                    # Update cache
                    if self._cache and self._portfolio:
                        await self._cache.set_portfolio_value(
                            self._portfolio.total_equity,
                            self._portfolio.cash,
                        )

                # Fragility check every 5 minutes
                if self._risk:
                    report = self._risk.assess_fragility()
                    if report and report.state.value == "fragile":
                        logger.warning(
                            "fragility_detected",
                            vega=report.vega,
                            recommendation=report.recommendation,
                        )

            except Exception as e:
                logger.error("periodic_task_error", error=str(e))

            await asyncio.sleep(5)

    async def _shutdown(self) -> None:
        """Graceful shutdown — cancel all orders, disconnect."""
        self._running = False
        logger.info("shutting_down")

        # Cancel all pending orders
        if self._execution:
            cancelled = await self._execution.cancel_all()
            logger.info("orders_cancelled", count=cancelled)

        # Disconnect components
        if self._data_feed:
            await self._data_feed.disconnect()
        if self._broker:
            await self._broker.disconnect()
        if self._db:
            await self._db.close()
        if self._cache:
            await self._cache.close()

        logger.info("shutdown_complete")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="HFT Agent")
    parser.add_argument(
        "--mode", choices=["paper", "live"], default="paper",
        help="Trading mode (default: paper)",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to config YAML file",
    )
    parser.add_argument(
        "--broker", choices=["alpaca", "robinhood", "ibkr"], default=None,
        help="Override broker selection",
    )
    args = parser.parse_args()

    # Load settings
    settings = load_settings(args.config)

    # Apply CLI overrides
    if args.mode:
        settings.app.mode = args.mode
    if args.broker:
        settings.brokers.primary = args.broker

    # Load .env file if present
    from dotenv import load_dotenv
    load_dotenv()

    # Run the agent
    agent = HFTAgent(settings)

    # Handle SIGINT/SIGTERM gracefully
    loop = asyncio.new_event_loop()

    def shutdown_handler(sig, frame):
        agent._running = False

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        loop.run_until_complete(agent.start())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
