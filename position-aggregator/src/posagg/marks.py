from __future__ import annotations
from typing import Optional, Dict

class MarkProvider:
    """Interface for real-time or polled marks."""
    def get_mark(self, symbol: str) -> Optional[float]:
        raise NotImplementedError

class StaticMarkProvider(MarkProvider):
    """Simple placeholder: set marks manually or by polling a delayed source."""
    def __init__(self, initial: Optional[Dict[str, float]] = None):
        self._marks: Dict[str, float] = dict(initial or {})

    def set_mark(self, symbol: str, price: float) -> None:
        self._marks[symbol] = price

    def get_mark(self, symbol: str) -> Optional[float]:
        return self._marks.get(symbol)

