from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class Fill:
    ts: str            # ISO string or "YYYY-MM-DD HH:MM:SS"
    symbol: str        # e.g., "MESZ5" or "MCLX5"
    side: str          # "BUY" or "SELL"
    qty: int
    price: float
    fees: float = 0.0
    account: str = "default"
    exec_id: Optional[str] = None
    note: str = ""

@dataclass
class Position:
    symbol: str
    net_qty: int = 0                  # signed (+ long, - short)
    avg_price: float = 0.0            # WAC for the open side
    realized_pnl: float = 0.0
    fees_cum: float = 0.0

    def reset_day(self) -> None:
        # Day-P&L rolling could be tracked separately later; base ledger persists.
        pass

@dataclass
class BlotterLine:
    symbol: str
    net_qty: int
    avg_price: float
    mark: Optional[float]
    upl: float
    rpl: float
    fees: float
    nlv_delta: float                   # rpl + upl - fees

