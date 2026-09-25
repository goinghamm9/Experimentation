from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import yfinance as yf

from utils.logging import get_logger
from utils.types import Bar, Side, Tick

logger = get_logger(__name__)

CACHE_DIR = Path(__file__).parent.parent / ".cache" / "market_data"


def _cache_key(symbols: list[str], start: str, end: str, interval: str) -> str:
    raw = f"{sorted(symbols)}_{start}_{end}_{interval}"
    return hashlib.md5(raw.encode()).hexdigest()


def _read_cache(key: str) -> dict[str, Any] | None:
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        logger.info("cache_hit", key=key)
        return data
    except Exception:
        return None


def _write_cache(key: str, data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    try:
        with open(path, "w") as f:
            json.dump(data, f)
        logger.info("cache_written", key=key)
    except Exception as exc:
        logger.warning("cache_write_failed", error=str(exc))


def load_historical_bars(
    symbols: list[str],
    start: str,
    end: str,
    interval: str = "1d",
) -> dict[str, list[Bar]]:
    """Download historical bars from Yahoo Finance.

    Args:
        symbols: Ticker symbols (e.g. ["SPY", "AAPL"]).
        start: Start date as "YYYY-MM-DD".
        end: End date as "YYYY-MM-DD".
        interval: Bar interval -- "1m", "2m", "5m", "15m", "30m", "60m", "90m",
                  "1h", "1d", "5d", "1wk", "1mo", "3mo".
    """
    key = _cache_key(symbols, start, end, interval)
    cached = _read_cache(key)
    if cached is not None:
        return _deserialize_bars(cached)

    logger.info("downloading_data", symbols=symbols, start=start, end=end, interval=interval)

    result: dict[str, list[Bar]] = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval)
            if df.empty:
                logger.warning("no_data", symbol=symbol)
                result[symbol] = []
                continue

            bars: list[Bar] = []
            for idx, row in df.iterrows():
                ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else datetime.fromisoformat(str(idx))
                vol = float(row.get("Volume", 0))
                o, h, l, c = float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"])
                vwap = (o + h + l + c) / 4 if vol > 0 else c
                bars.append(Bar(
                    symbol=symbol,
                    timestamp=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=vol,
                    vwap=vwap,
                ))
            result[symbol] = bars
            logger.info("downloaded", symbol=symbol, bars=len(bars))
        except Exception as exc:
            logger.error("download_failed", symbol=symbol, error=str(exc))
            result[symbol] = []

    _write_cache(key, _serialize_bars(result))
    return result


def generate_synthetic_ticks(bars: list[Bar], ticks_per_bar: int = 20) -> list[Tick]:
    """Interpolate synthetic ticks from bars for realistic simulation.

    Uses a random walk within each bar's OHLC range with volume distribution
    that mimics the U-shaped intraday volume pattern.
    """
    if not bars:
        return []

    ticks: list[Tick] = []
    for bar in bars:
        if bar.volume <= 0:
            continue

        bar_duration = timedelta(minutes=1)
        if len(bars) > 1:
            idx = bars.index(bar)
            if idx < len(bars) - 1:
                bar_duration = bars[idx + 1].timestamp - bar.timestamp

        tick_interval = bar_duration / max(ticks_per_bar, 1)
        total_volume = bar.volume
        prices = _interpolate_ohlc(bar.open, bar.high, bar.low, bar.close, ticks_per_bar)
        volumes = _distribute_volume(total_volume, ticks_per_bar)

        for i in range(ticks_per_bar):
            ts = bar.timestamp + tick_interval * i
            price = prices[i]
            size = volumes[i]
            side = Side.BUY if i > 0 and prices[i] >= prices[i - 1] else Side.SELL
            ticks.append(Tick(
                symbol=bar.symbol,
                timestamp=ts,
                price=price,
                size=size,
                side=side,
            ))

    return ticks


def _interpolate_ohlc(o: float, h: float, l: float, c: float, n: int) -> list[float]:
    if n <= 1:
        return [c]

    prices = [o]
    current = o
    peak_idx = random.randint(1, max(n // 3, 1))
    trough_idx = random.randint(peak_idx + 1, max(2 * n // 3, peak_idx + 1))

    for i in range(1, n):
        if i == peak_idx:
            current = h
        elif i == trough_idx:
            current = l
        elif i == n - 1:
            current = c
        else:
            target = c if i > trough_idx else (h if i < peak_idx else l)
            noise = random.gauss(0, (h - l) * 0.05) if h > l else 0
            alpha = i / n
            current = current * (1 - alpha * 0.3) + target * alpha * 0.3 + noise
            current = max(l, min(h, current))
        prices.append(round(current, 4))

    return prices


def _distribute_volume(total: float, n: int) -> list[float]:
    if n <= 0:
        return []
    weights = np.array([1.5 if i < n * 0.1 or i > n * 0.9 else 0.7 + random.random() * 0.6 for i in range(n)])
    weights /= weights.sum()
    volumes = (weights * total).tolist()
    return [max(1.0, v) for v in volumes]


def _serialize_bars(data: dict[str, list[Bar]]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for symbol, bars in data.items():
        result[symbol] = [
            {
                "symbol": b.symbol,
                "timestamp": b.timestamp.isoformat(),
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
                "vwap": b.vwap,
            }
            for b in bars
        ]
    return result


def _deserialize_bars(data: dict[str, list[dict]]) -> dict[str, list[Bar]]:
    result: dict[str, list[Bar]] = {}
    for symbol, items in data.items():
        result[symbol] = [
            Bar(
                symbol=item["symbol"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                open=item["open"],
                high=item["high"],
                low=item["low"],
                close=item["close"],
                volume=item["volume"],
                vwap=item.get("vwap"),
            )
            for item in items
        ]
    return result
