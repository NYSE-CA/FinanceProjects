from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from .models import Fill, Position, BlotterLine
from .config import DEFAULTS
from .marks import MarkProvider

def symbol_root(sym: str) -> str:
    # "MESZ5" -> "MES"; "MCLX5" -> "MCL"
    for root in DEFAULTS.keys():
        if sym.startswith(root):
            return root
    return sym  # fallback

@dataclass
class PositionEngine:
    mark_provider: Optional[MarkProvider] = None
    positions: Dict[str, Position] = field(default_factory=dict)
    seen_exec_ids: set[str] = field(default_factory=set)

    def _get_pos(self, symbol: str) -> Position:
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def _tickmath(self, symbol: str) -> Tuple[float, float]:
        root = symbol_root(symbol)
        cfg = DEFAULTS[root]
        return (cfg.tick_size, cfg.dollars_per_tick)

    def apply_fill(self, fill: Fill) -> None:
        # idempotency
        if fill.exec_id and fill.exec_id in self.seen_exec_ids:
            return
        if fill.exec_id:
            self.seen_exec_ids.add(fill.exec_id)

        pos = self._get_pos(fill.symbol)
        tick_size, dollars_per_tick = self._tickmath(fill.symbol)

        signed_fill_qty = fill.qty if fill.side.upper() == "BUY" else -fill.qty

        # Case 1: adding in same direction or starting from flat
        if pos.net_qty == 0 or (pos.net_qty > 0 and signed_fill_qty > 0) or (pos.net_qty < 0 and signed_fill_qty < 0):
            # Weighted Average Cost update
            new_qty = pos.net_qty + signed_fill_qty
            if pos.net_qty == 0:
                pos.avg_price = fill.price
            else:
                # Blend only if moving further in same direction
                total_qty_before = abs(pos.net_qty)
                total_qty_after  = abs(new_qty)
                pos.avg_price = (pos.avg_price * total_qty_before + fill.price * abs(signed_fill_qty)) / total_qty_after
            pos.net_qty = new_qty

        else:
            # Case 2: reducing or flipping through zero
            if (pos.net_qty > 0 and signed_fill_qty < 0) or (pos.net_qty < 0 and signed_fill_qty > 0):
                close_qty = min(abs(pos.net_qty), abs(signed_fill_qty))
                # Realize P&L on the closing portion against current avg
                # Sign-correct P&L:
                # Long reduced by SELL: pnl = (exit - avg) * contracts * ticks_per_point * $/tick (abstract to price delta * $/tick / tick_size)
                price_delta = (fill.price - pos.avg_price)
                direction = 1 if pos.net_qty > 0 else -1  # +1 long, -1 short
                realized_per_contract = direction * price_delta / tick_size * dollars_per_tick
                pos.realized_pnl += realized_per_contract * close_qty

                # Update remaining quantity
                remaining = pos.net_qty + signed_fill_qty  # signed
                if remaining == 0:
                    pos.net_qty = 0
                    pos.avg_price = 0.0
                else:
                    # Flip happened: leftover in new direction; average becomes the fill price for the overfill part
                    pos.net_qty = remaining
                    pos.avg_price = fill.price

        # Fees always accrue to realized side
        pos.fees_cum += fill.fees

    def mark_for(self, symbol: str) -> Optional[float]:
        if not self.mark_provider:
            return None
        return self.mark_provider.get_mark(symbol)

    def upl(self, symbol: str) -> float:
        pos = self._get_pos(symbol)
        if pos.net_qty == 0:
            return 0.0
        mark = self.mark_for(symbol)
        if mark is None:
            return 0.0
        tick_size, dollars_per_tick = self._tickmath(symbol)
        direction = 1 if pos.net_qty > 0 else -1
        price_delta = (mark - pos.avg_price)
        per_contract = direction * price_delta / tick_size * dollars_per_tick
        return per_contract * abs(pos.net_qty)

    def blotter_line(self, symbol: str) -> BlotterLine:
        pos = self._get_pos(symbol)
        mark = self.mark_for(symbol)
        upl_val = self.upl(symbol)
        nlv_delta = pos.realized_pnl + upl_val - pos.fees_cum
        return BlotterLine(
            symbol=symbol,
            net_qty=pos.net_qty,
            avg_price=pos.avg_price,
            mark=mark,
            upl=upl_val,
            rpl=pos.realized_pnl,
            fees=pos.fees_cum,
            nlv_delta=nlv_delta,
        )

    def all_blotter(self) -> list[BlotterLine]:
        return [self.blotter_line(sym) for sym in sorted(self.positions.keys())]

