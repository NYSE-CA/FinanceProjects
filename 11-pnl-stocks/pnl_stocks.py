#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass(frozen=True)
class StockCosts:
    commission_per_share: float = 0.00     # e.g., 0.005 if your broker charges per share
    slippage_per_share_rt: float = 0.02    # round-trip slippage (total)

def ask_float(prompt: str, default: float | None = None) -> float:
    while True:
        raw = input(f"{prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not raw and default is not None:
            return float(default)
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a number.")

def ask_int(prompt: str, default: int | None = None) -> int:
    while True:
        raw = input(f"{prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not raw and default is not None:
            return int(default)
        try:
            val = int(raw)
            if val <= 0:
                print("  Must be > 0.")
                continue
            return val
        except ValueError:
            print("  Please enter a whole number.")

def ask_side() -> str:
    while True:
        s = input("Side (long/short): ").strip().lower()
        if s in ("long", "short"):
            return s
        print("  Type 'long' or 'short'.")

def pnl_stocks(entry: float, exit: float, shares: int, side: str, costs: StockCosts) -> float:
    sign = 1 if side == "long" else -1
    gross = sign * (exit - entry) * shares
    costs_total = shares * (costs.commission_per_share + costs.slippage_per_share_rt)
    return round(gross - costs_total, 2)

def main():
    print("=== STOCKS/ETF P&L ===")
    entry = ask_float("Entry (buy) price")
    exit_ = ask_float("Exit (sell) price")
    side = ask_side()
    shares = ask_int("Number of shares", default=25)

    commission = ask_float("Commission per share", default=0.00)
    slippage_rt = ask_float("Round-trip slippage per share", default=0.02)

    costs = StockCosts(commission_per_share=commission, slippage_per_share_rt=slippage_rt)
    pnl = pnl_stocks(entry, exit_, shares, side, costs)

    print("\n--- RESULT ---")
    print(f"Side: {side.upper()}  Shares: {shares}")
    print(f"Entry: {entry:.4f}  Exit: {exit_:.4f}")
    print(f"Costs: commission/share=${commission:.4f}, slippage RT/share=${slippage_rt:.4f}")
    print(f"Net P&L: ${pnl:.2f}")

if __name__ == "__main__":
    main()

