#!/usr/bin/env python3
"""
Top-level menu runner:
- Choose Stocks or Futures
- After each run, return to this menu ("Back")
"""
from importlib import import_module

def ask_choice(prompt: str, options: dict[str, str], allow_quit: bool = True) -> str:
    keys = "/".join(options.keys()) + ("/q" if allow_quit and "q" not in options else "")
    while True:
        ans = input(f"{prompt} [{keys}]: ").strip().lower()
        if ans in options:
            return ans
        if allow_quit and ans in ("q", "quit", "exit"):
            return "q"
        print(f"  Please choose one of: {keys}")

def run_stocks():
    mod = import_module("ch11_pnl_stocks.pnl_stocks")
    mod.main()

def run_futures():
    mod = import_module("ch11_pnl_futures.pnl_futures")
    mod.main()

def main():
    print("=== P&L Runner ===")
    while True:
        choice = ask_choice(
            "Which market?",
            {"stocks": "Stocks/ETFs", "futures": "Futures (MES/Tradovate)"},
            allow_quit=True,
        )
        if choice == "q":
            print("Bye!")
            break

        if choice == "stocks":
            run_stocks()
        elif choice == "futures":
            run_futures()

        again = input("\nRun another calculation? [Y/n]: ").strip().lower()
        if again in ("n", "no"):
            print("Good Luck!")
            break

if __name__ == "__main__":
    main()
