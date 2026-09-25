"""Daily price data: Yahoo Finance (no key), Alpaca (keys), or local CSV. Cached on disk."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .config import CACHE_DIR


@dataclass
class MarketData:
    close: pd.DataFrame  # adjusted closes, index=date, columns=symbols
    volume: pd.DataFrame
    source: str

    @property
    def returns(self) -> pd.DataFrame:
        return self.close.pct_change()

    def symbols(self) -> list[str]:
        return list(self.close.columns)


def load_prices(
    symbols: list[str],
    start: str,
    end: str | None = None,
    source: str = "auto",
    csv_path: str | None = None,
    use_cache: bool = True,
) -> MarketData:
    symbols = list(dict.fromkeys(s.upper() for s in symbols))
    end = end or (date.today() + timedelta(days=1)).isoformat()

    if source == "csv" or (source == "auto" and csv_path):
        if not csv_path:
            raise ValueError("csv source requires csv_path")
        return _load_csv(csv_path, symbols, start, end)

    key = hashlib.md5(f"{sorted(symbols)}|{start}|{end}|{source}".encode()).hexdigest()
    close_file, vol_file = CACHE_DIR / f"{key}_close.csv", CACHE_DIR / f"{key}_vol.csv"
    if use_cache and close_file.exists() and end < date.today().isoformat():
        return MarketData(
            pd.read_csv(close_file, index_col=0, parse_dates=True),
            pd.read_csv(vol_file, index_col=0, parse_dates=True),
            f"{source} (cached)",
        )

    errors: list[str] = []
    order = [source] if source != "auto" else (
        ["alpaca", "yahoo"] if os.environ.get("ALPACA_API_KEY") else ["yahoo"]
    )
    for src in order:
        try:
            md = _load_alpaca(symbols, start, end) if src == "alpaca" else _load_yahoo(symbols, start, end)
            if md.close.empty:
                raise RuntimeError("no rows returned")
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            md.close.to_csv(close_file)
            md.volume.to_csv(vol_file)
            return md
        except Exception as exc:  # try next source
            errors.append(f"{src}: {exc}")
    raise RuntimeError("Could not load prices. " + "; ".join(errors))


def _load_yahoo(symbols: list[str], start: str, end: str) -> MarketData:
    import yfinance as yf

    df = yf.download(symbols, start=start, end=end, auto_adjust=True, progress=False, group_by="column")
    if df.empty:
        return MarketData(pd.DataFrame(), pd.DataFrame(), "yahoo")
    if isinstance(df.columns, pd.MultiIndex):
        close, vol = df["Close"], df["Volume"]
    else:
        close = df[["Close"]].rename(columns={"Close": symbols[0]})
        vol = df[["Volume"]].rename(columns={"Volume": symbols[0]})
    close.index = pd.to_datetime(close.index).tz_localize(None)
    vol.index = close.index
    return MarketData(close.sort_index(), vol.sort_index(), "yahoo")


def _load_alpaca(symbols: list[str], start: str, end: str) -> MarketData:
    import requests

    headers = {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    }
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start,
        "end": end,
        "adjustment": "all",
        "limit": 10000,
        "feed": os.environ.get("ALPACA_DATA_FEED", "sip"),
    }
    rows: list[dict] = []
    while True:
        r = requests.get("https://data.alpaca.markets/v2/stocks/bars", headers=headers, params=params, timeout=30)
        r.raise_for_status()
        body = r.json()
        for sym, bars in (body.get("bars") or {}).items():
            rows += [{"symbol": sym, "date": b["t"][:10], "close": b["c"], "volume": b["v"]} for b in bars]
        token = body.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    if not rows:
        return MarketData(pd.DataFrame(), pd.DataFrame(), "alpaca")
    long = pd.DataFrame(rows)
    long["date"] = pd.to_datetime(long["date"])
    close = long.pivot(index="date", columns="symbol", values="close").sort_index()
    vol = long.pivot(index="date", columns="symbol", values="volume").sort_index()
    return MarketData(close, vol, "alpaca")


def _load_csv(path: str, symbols: list[str], start: str, end: str) -> MarketData:
    raw = pd.read_csv(path)
    cols = {c.lower(): c for c in raw.columns}
    sym_col = cols.get("symbol") or cols.get("stock_symbol") or cols.get("ticker")
    if sym_col:
        price_col = cols.get("adj_close") or cols.get("adj close") or cols.get("close")
        vol_col = cols.get("volume")
        raw["_date"] = pd.to_datetime(raw[cols["date"]])
        raw["_sym"] = raw[sym_col].str.upper()
        close = raw.pivot_table(index="_date", columns="_sym", values=price_col)
        volume = (
            raw.pivot_table(index="_date", columns="_sym", values=vol_col)
            if vol_col else pd.DataFrame(np.nan, index=close.index, columns=close.columns)
        )
    else:
        raw[cols["date"]] = pd.to_datetime(raw[cols["date"]])
        close = raw.set_index(cols["date"])
        volume = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    close.columns = [str(c).upper() for c in close.columns]
    volume.columns = [str(c).upper() for c in volume.columns]
    keep = [s for s in symbols if s in close.columns] or list(close.columns)
    mask = (close.index >= pd.Timestamp(start)) & (close.index < pd.Timestamp(end))
    return MarketData(close.loc[mask, keep].sort_index(), volume.loc[mask, keep].sort_index(), f"csv:{Path(path).name}")


def safe_asset_returns(md: MarketData, candidates: list[str], cash_rate_annual: float) -> pd.Series:
    """Daily return of the safe sleeve: first available T-bill ETF per day, else cash rate."""
    idx = md.close.index
    out = pd.Series(cash_rate_annual / 252.0, index=idx)
    for sym in reversed(candidates):
        if sym in md.close.columns:
            r = md.close[sym].pct_change()
            out = r.where(r.notna(), out)
    return out.fillna(cash_rate_annual / 252.0)
