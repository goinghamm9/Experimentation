"""
Redis cache layer for real-time data.

Redis is used for:
- Order book cache (latest state, sub-ms reads)
- Signal cache (latest computed signals per symbol)
- Rate limiting (order submission throttling)
- Pub/sub for inter-component communication
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from utils.logging import get_logger
from utils.types import OrderBook, OrderBookLevel, Signal

logger = get_logger(__name__)


class RedisCache:
    """Async Redis cache for real-time HFT data."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self._host = host
        self._port = port
        self._db = db
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.Redis(
            host=self._host,
            port=self._port,
            db=self._db,
            decode_responses=True,
        )
        await self._client.ping()
        logger.info("redis_connected", host=self._host, port=self._port)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()

    # --- Order Book Cache ---

    async def set_orderbook(self, ob: OrderBook) -> None:
        """Cache the latest order book for a symbol."""
        if not self._client:
            return
        key = f"ob:{ob.symbol}"
        data = {
            "timestamp": ob.timestamp.isoformat(),
            "bids": [[l.price, l.size] for l in ob.bids],
            "asks": [[l.price, l.size] for l in ob.asks],
        }
        await self._client.set(key, json.dumps(data), ex=30)  # 30s TTL

    async def get_orderbook(self, symbol: str) -> OrderBook | None:
        """Get cached order book."""
        if not self._client:
            return None
        raw = await self._client.get(f"ob:{symbol}")
        if not raw:
            return None
        data = json.loads(raw)
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            bids=[OrderBookLevel(price=b[0], size=b[1]) for b in data["bids"]],
            asks=[OrderBookLevel(price=a[0], size=a[1]) for a in data["asks"]],
        )

    # --- Signal Cache ---

    async def set_signal(self, signal: Signal) -> None:
        """Cache the latest signal value."""
        if not self._client:
            return
        key = f"signal:{signal.symbol}:{signal.name}"
        data = {
            "timestamp": signal.timestamp.isoformat(),
            "value": signal.value,
            "direction": signal.direction.value if signal.direction else None,
            "strength": signal.strength,
            "metadata": signal.metadata,
        }
        await self._client.set(key, json.dumps(data), ex=60)

    async def get_signal(self, symbol: str, signal_name: str) -> Signal | None:
        """Get cached signal."""
        if not self._client:
            return None
        raw = await self._client.get(f"signal:{symbol}:{signal_name}")
        if not raw:
            return None
        data = json.loads(raw)
        from utils.types import Side
        return Signal(
            symbol=symbol,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            name=signal_name,
            value=data["value"],
            direction=Side(data["direction"]) if data["direction"] else None,
            strength=data["strength"],
            metadata=data.get("metadata", {}),
        )

    async def get_all_signals(self, symbol: str) -> list[Signal]:
        """Get all cached signals for a symbol."""
        if not self._client:
            return []
        keys = []
        async for key in self._client.scan_iter(f"signal:{symbol}:*"):
            keys.append(key)

        signals = []
        for key in keys:
            signal_name = key.split(":")[-1]
            signal = await self.get_signal(symbol, signal_name)
            if signal:
                signals.append(signal)
        return signals

    # --- Rate Limiting ---

    async def check_rate_limit(self, key: str, max_per_second: int) -> bool:
        """Check if an action is within rate limits. Returns True if allowed."""
        if not self._client:
            return True
        rate_key = f"rate:{key}"
        current = await self._client.incr(rate_key)
        if current == 1:
            await self._client.expire(rate_key, 1)
        return current <= max_per_second

    # --- Pub/Sub ---

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish a message to a channel."""
        if not self._client:
            return
        await self._client.publish(channel, json.dumps(message))

    def subscribe(self, *channels: str) -> redis.client.PubSub:
        """Subscribe to channels. Returns a PubSub object."""
        if not self._client:
            raise RuntimeError("Not connected")
        pubsub = self._client.pubsub()
        return pubsub

    # --- Portfolio State ---

    async def set_portfolio_value(self, equity: float, cash: float) -> None:
        """Cache current portfolio state for monitoring."""
        if not self._client:
            return
        await self._client.hset("portfolio", mapping={
            "equity": str(equity),
            "cash": str(cash),
            "updated": datetime.utcnow().isoformat(),
        })

    async def get_portfolio_value(self) -> dict[str, float] | None:
        """Get cached portfolio state."""
        if not self._client:
            return None
        data = await self._client.hgetall("portfolio")
        if not data:
            return None
        return {
            "equity": float(data.get("equity", 0)),
            "cash": float(data.get("cash", 0)),
        }
