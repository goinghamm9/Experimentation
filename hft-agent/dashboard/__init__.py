"""HFT Agent Dashboard -- FastAPI backend with WebSocket real-time feed."""

from .app import (
    ConnectionManager,
    DashboardState,
    SimulationResult,
    TradeRecord,
    app,
    manager,
    push_update,
    state,
)

__all__ = [
    "ConnectionManager",
    "DashboardState",
    "SimulationResult",
    "TradeRecord",
    "app",
    "manager",
    "push_update",
    "state",
]
