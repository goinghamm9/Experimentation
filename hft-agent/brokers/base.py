"""Abstract broker interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from utils.types import Order, OrderStatus, Position, PortfolioState


class Broker(ABC):
    """Abstract interface for broker connections.

    All broker implementations must provide these methods for
    the execution engine to interact with any supported platform.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Authenticate and connect to the broker."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the broker."""
        ...

    @abstractmethod
    async def get_account(self) -> PortfolioState:
        """Get current account/portfolio state."""
        ...

    @abstractmethod
    async def get_positions(self) -> dict[str, Position]:
        """Get all open positions."""
        ...

    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """Submit an order. Returns the order with updated status/ID."""
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order. Returns True if successful."""
        ...

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Check the status of an order."""
        ...

    @abstractmethod
    async def cancel_all_orders(self) -> int:
        """Cancel all open orders. Returns count of cancelled orders."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Broker name identifier."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether broker connection is active."""
        ...
