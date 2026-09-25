"""Robinhood Agentic Trading broker via MCP (Model Context Protocol).

Connects to Robinhood's MCP server at https://agent.robinhood.com/mcp/trading
to execute trades in a dedicated Agentic account.

Key differences from robin_stocks integration:
- OAuth 2.0 auth (no password/MFA stored)
- Trades in ring-fenced Agentic account only
- Cash-only (no margin borrowing)
- MCP tool-based: place_equity_order, get_portfolio, get_equity_positions, etc.
- Stateless per-run: credentials injected at session start
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any

import aiohttp

from utils.logging import get_logger
from utils.types import (
    Order,
    OrderStatus,
    OrderType,
    Position,
    PortfolioState,
    Side,
)

from .base import Broker

logger = get_logger(__name__)

_RH_MCP_STATUS_MAP = {
    "queued": OrderStatus.PENDING,
    "unconfirmed": OrderStatus.PENDING,
    "confirmed": OrderStatus.SUBMITTED,
    "partially_filled": OrderStatus.PARTIALLY_FILLED,
    "filled": OrderStatus.FILLED,
    "cancelled": OrderStatus.CANCELLED,
    "rejected": OrderStatus.REJECTED,
    "failed": OrderStatus.REJECTED,
}

MCP_SERVER_URL = "https://agent.robinhood.com/mcp/trading"


class RobinhoodMCPBroker(Broker):
    """Robinhood broker via Agentic Trading MCP server."""

    def __init__(
        self,
        mcp_server_url: str | None = None,
        oauth_token: str | None = None,
        max_retries: int = 3,
        request_timeout: float = 30.0,
    ):
        self._server_url = mcp_server_url or os.environ.get(
            "ROBINHOOD_MCP_URL", MCP_SERVER_URL
        )
        self._oauth_token = oauth_token or os.environ.get("ROBINHOOD_OAUTH_TOKEN", "")
        self._max_retries = max_retries
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)
        self._session: aiohttp.ClientSession | None = None
        self._connected = False
        self._account_id: str | None = None

    @property
    def name(self) -> str:
        return "robinhood_mcp"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        if not self._oauth_token:
            raise RuntimeError(
                "ROBINHOOD_OAUTH_TOKEN not set. Complete OAuth consent in the "
                "Robinhood app (Agentic Trading > Connect your agent) first."
            )

        self._session = aiohttp.ClientSession(
            timeout=self._timeout,
            headers={
                "Authorization": f"Bearer {self._oauth_token}",
                "Content-Type": "application/json",
            },
        )

        portfolio = await self._call_tool("get_portfolio", {})
        if portfolio is None:
            await self._session.close()
            raise RuntimeError("Failed to authenticate with Robinhood MCP server")

        self._account_id = portfolio.get("account_id")
        self._connected = True
        logger.info(
            "robinhood_mcp_connected",
            account_id=self._account_id,
            buying_power=portfolio.get("buying_power"),
        )

    async def disconnect(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False
        self._account_id = None
        logger.info("robinhood_mcp_disconnected")

    async def get_account(self) -> PortfolioState:
        portfolio = await self._call_tool("get_portfolio", {})
        if portfolio is None:
            raise RuntimeError("Failed to get portfolio from MCP")

        positions = await self.get_positions()

        equity = float(portfolio.get("equity", 0))
        cash = float(portfolio.get("buying_power", 0))

        return PortfolioState(
            cash=cash,
            positions=positions,
            total_equity=equity,
            peak_equity=equity,
        )

    async def get_positions(self) -> dict[str, Position]:
        result = await self._call_tool("get_equity_positions", {})
        if result is None:
            return {}

        positions_list = result if isinstance(result, list) else result.get("positions", [])
        positions: dict[str, Position] = {}

        for pos in positions_list:
            qty = float(pos.get("quantity", 0))
            if qty == 0:
                continue

            symbol = pos.get("symbol", "UNKNOWN")
            avg_price = float(pos.get("average_buy_price", 0))
            current_price = float(pos.get("current_price", avg_price))
            unrealized = float(pos.get("unrealized_pnl", (current_price - avg_price) * qty))

            positions[symbol] = Position(
                symbol=symbol,
                qty=qty,
                avg_entry_price=avg_price,
                current_price=current_price,
                unrealized_pnl=unrealized,
            )

        return positions

    async def submit_order(self, order: Order) -> Order:
        params: dict[str, Any] = {
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.qty,
            "type": order.order_type.value,
        }

        if order.order_type == OrderType.LIMIT:
            if order.limit_price is None:
                raise ValueError("Limit price required for limit orders")
            params["limit_price"] = order.limit_price

        result = await self._call_tool("place_equity_order", params)

        if result and result.get("id"):
            order.order_id = result["id"]
            state = result.get("state", "")
            order.status = _RH_MCP_STATUS_MAP.get(state, OrderStatus.PENDING)
            order.timestamp = datetime.now(timezone.utc)

            if result.get("average_price"):
                order.filled_price = float(result["average_price"])
            if result.get("filled_quantity"):
                order.filled_qty = float(result["filled_quantity"])

            logger.info(
                "robinhood_mcp_order_submitted",
                symbol=order.symbol,
                side=order.side.value,
                qty=order.qty,
                order_id=order.order_id,
                status=order.status.value,
            )
        else:
            order.status = OrderStatus.REJECTED
            reject_reason = result.get("detail", "unknown") if result else "no response"
            logger.warning(
                "robinhood_mcp_order_rejected",
                symbol=order.symbol,
                reason=reject_reason,
            )

        return order

    async def cancel_order(self, order_id: str) -> bool:
        result = await self._call_tool("cancel_equity_order", {"order_id": order_id})
        if result is not None:
            logger.info("robinhood_mcp_order_cancelled", order_id=order_id)
            return True
        logger.warning("robinhood_mcp_cancel_failed", order_id=order_id)
        return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        result = await self._call_tool(
            "get_order_history", {"order_id": order_id}
        )
        if result is None:
            return OrderStatus.REJECTED
        state = result.get("state", "failed")
        return _RH_MCP_STATUS_MAP.get(state, OrderStatus.REJECTED)

    async def cancel_all_orders(self) -> int:
        result = await self._call_tool("cancel_all_equity_orders", {})
        count = result.get("cancelled_count", 0) if result else 0
        logger.info("robinhood_mcp_all_cancelled", count=count)
        return count

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get a live equity quote via MCP."""
        return await self._call_tool("get_equity_quotes", {"symbols": [symbol]})

    async def get_quotes(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Get live quotes for multiple symbols."""
        result = await self._call_tool("get_equity_quotes", {"symbols": symbols})
        if result is None:
            return []
        return result if isinstance(result, list) else result.get("quotes", [])

    async def search_symbol(self, query: str) -> list[dict[str, Any]]:
        """Search for symbols via MCP."""
        result = await self._call_tool("search_symbols", {"query": query})
        if result is None:
            return []
        return result if isinstance(result, list) else result.get("results", [])

    async def _call_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Call an MCP tool on the Robinhood server with retry logic."""
        if not self._session:
            raise RuntimeError("Not connected to Robinhood MCP")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params,
            },
            "id": f"{tool_name}_{id(params)}",
        }

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                async with self._session.post(
                    self._server_url, json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data:
                            content = data["result"].get("content", [])
                            for block in content:
                                if block.get("type") == "text":
                                    try:
                                        return json.loads(block["text"])
                                    except (json.JSONDecodeError, KeyError):
                                        return {"raw": block.get("text")}
                            return data["result"]
                        elif "error" in data:
                            logger.warning(
                                "mcp_tool_error",
                                tool=tool_name,
                                error=data["error"],
                            )
                            return None
                    elif resp.status == 429:
                        wait = float(resp.headers.get("Retry-After", 2 * (attempt + 1)))
                        logger.warning(
                            "mcp_rate_limited", tool=tool_name, retry_after=wait
                        )
                        await asyncio.sleep(wait)
                        continue
                    else:
                        body = await resp.text()
                        logger.warning(
                            "mcp_http_error",
                            tool=tool_name,
                            status=resp.status,
                            body=body[:200],
                        )

            except asyncio.TimeoutError:
                last_error = TimeoutError(f"MCP call {tool_name} timed out")
                logger.warning("mcp_timeout", tool=tool_name, attempt=attempt + 1)
            except aiohttp.ClientError as e:
                last_error = e
                logger.warning(
                    "mcp_client_error",
                    tool=tool_name,
                    error=str(e),
                    attempt=attempt + 1,
                )

            if attempt < self._max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))

        if last_error:
            logger.error(
                "mcp_call_failed",
                tool=tool_name,
                error=str(last_error),
            )
        return None
