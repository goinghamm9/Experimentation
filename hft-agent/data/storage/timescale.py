"""
TimescaleDB storage layer for tick data, bars, and order book snapshots.

TimescaleDB is chosen because:
- Native time-series hypertable compression (10-20x compression)
- Continuous aggregates for real-time OHLCV rollups
- Native SQL with time_bucket() for arbitrary interval aggregation
- Sub-millisecond query performance on time-range scans
- Built on PostgreSQL (mature, reliable, ACID compliant)
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import asyncpg
import numpy as np
from numpy.typing import NDArray

from utils.logging import get_logger
from utils.types import Bar, OrderBook, OrderBookLevel, Tick

logger = get_logger(__name__)

# Schema DDL for initialization
SCHEMA_DDL = """
-- Tick data hypertable
CREATE TABLE IF NOT EXISTS ticks (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    price       DOUBLE PRECISION NOT NULL,
    size        DOUBLE PRECISION NOT NULL,
    side        TEXT
);
SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks (symbol, time DESC);

-- OHLCV bars hypertable
CREATE TABLE IF NOT EXISTS bars (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION NOT NULL,
    vwap        DOUBLE PRECISION
);
SELECT create_hypertable('bars', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_bars_symbol_time ON bars (symbol, time DESC);

-- Order book snapshots
CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    bid_prices  DOUBLE PRECISION[] NOT NULL,
    bid_sizes   DOUBLE PRECISION[] NOT NULL,
    ask_prices  DOUBLE PRECISION[] NOT NULL,
    ask_sizes   DOUBLE PRECISION[] NOT NULL
);
SELECT create_hypertable('orderbook_snapshots', 'time', if_not_exists => TRUE);

-- Signals log
CREATE TABLE IF NOT EXISTS signals (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    signal_name TEXT NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    direction   TEXT,
    strength    DOUBLE PRECISION,
    metadata    JSONB
);
SELECT create_hypertable('signals', 'time', if_not_exists => TRUE);

-- Trades (executed orders)
CREATE TABLE IF NOT EXISTS trades (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,
    qty             DOUBLE PRECISION NOT NULL,
    price           DOUBLE PRECISION NOT NULL,
    order_id        TEXT,
    strategy        TEXT,
    signal_strength DOUBLE PRECISION,
    pnl             DOUBLE PRECISION
);
SELECT create_hypertable('trades', 'time', if_not_exists => TRUE);

-- Enable compression on older data
ALTER TABLE ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('ticks', INTERVAL '1 day', if_not_exists => TRUE);

ALTER TABLE bars SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('bars', INTERVAL '7 days', if_not_exists => TRUE);

-- Continuous aggregate for 1-minute bars from ticks
CREATE MATERIALIZED VIEW IF NOT EXISTS bars_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    first(price, time) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, time) AS close,
    sum(size) AS volume
FROM ticks
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('bars_1min',
    start_offset => INTERVAL '10 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);
"""


class TimescaleStore:
    """Async TimescaleDB storage for market data."""

    def __init__(self, dsn: str, pool_size: int = 10):
        self._dsn = dsn
        self._pool_size = pool_size
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create connection pool and initialize schema."""
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=2,
            max_size=self._pool_size,
        )
        logger.info("timescaledb_connected", dsn=self._dsn.split("@")[-1])

    async def initialize_schema(self) -> None:
        """Create tables and hypertables if they don't exist."""
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            # Execute each statement separately (some may fail if TimescaleDB
            # extension isn't available, which is fine for development)
            for statement in SCHEMA_DDL.split(";"):
                statement = statement.strip()
                if statement:
                    try:
                        await conn.execute(statement + ";")
                    except Exception as e:
                        logger.warning("schema_statement_failed", error=str(e)[:100])

        logger.info("schema_initialized")

    async def insert_tick(self, tick: Tick) -> None:
        """Insert a single tick."""
        if not self._pool:
            return
        await self._pool.execute(
            "INSERT INTO ticks (time, symbol, price, size, side) VALUES ($1, $2, $3, $4, $5)",
            tick.timestamp, tick.symbol, tick.price, tick.size,
            tick.side.value if tick.side else None,
        )

    async def insert_ticks_batch(self, ticks: list[Tick]) -> None:
        """Batch insert ticks for performance."""
        if not self._pool or not ticks:
            return
        records = [
            (t.timestamp, t.symbol, t.price, t.size, t.side.value if t.side else None)
            for t in ticks
        ]
        async with self._pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO ticks (time, symbol, price, size, side) VALUES ($1, $2, $3, $4, $5)",
                records,
            )

    async def insert_bar(self, bar: Bar) -> None:
        """Insert a single OHLCV bar."""
        if not self._pool:
            return
        await self._pool.execute(
            "INSERT INTO bars (time, symbol, open, high, low, close, volume, vwap) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            bar.timestamp, bar.symbol, bar.open, bar.high, bar.low,
            bar.close, bar.volume, bar.vwap,
        )

    async def insert_orderbook(self, ob: OrderBook) -> None:
        """Insert order book snapshot."""
        if not self._pool:
            return
        await self._pool.execute(
            "INSERT INTO orderbook_snapshots (time, symbol, bid_prices, bid_sizes, ask_prices, ask_sizes) "
            "VALUES ($1, $2, $3, $4, $5, $6)",
            ob.timestamp, ob.symbol,
            [l.price for l in ob.bids], [l.size for l in ob.bids],
            [l.price for l in ob.asks], [l.size for l in ob.asks],
        )

    async def get_recent_returns(
        self,
        symbol: str,
        n: int = 5000,
    ) -> NDArray[np.float64]:
        """Fetch recent log-returns from ticks for distribution fitting."""
        if not self._pool:
            return np.array([], dtype=np.float64)

        rows = await self._pool.fetch(
            "SELECT price FROM ticks WHERE symbol = $1 ORDER BY time DESC LIMIT $2",
            symbol, n + 1,
        )
        if len(rows) < 2:
            return np.array([], dtype=np.float64)

        prices = np.array([r["price"] for r in reversed(rows)], dtype=np.float64)
        returns = np.diff(np.log(prices))
        return returns

    async def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1 minute",
    ) -> list[Bar]:
        """Fetch bars for a time range."""
        if not self._pool:
            return []

        rows = await self._pool.fetch(
            "SELECT time, symbol, open, high, low, close, volume, vwap "
            "FROM bars WHERE symbol = $1 AND time >= $2 AND time <= $3 "
            "ORDER BY time",
            symbol, start, end,
        )
        return [
            Bar(
                symbol=r["symbol"], timestamp=r["time"],
                open=r["open"], high=r["high"], low=r["low"],
                close=r["close"], volume=r["volume"], vwap=r["vwap"],
            )
            for r in rows
        ]

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("timescaledb_disconnected")
