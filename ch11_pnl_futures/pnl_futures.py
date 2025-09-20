#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass(frozen=True)
class FuturesFees:
    # Per SIDE fees (MES on Tradovate, approximate defaults)
    exchange_per_side: float = 0.35   # CME exec/exchange (retail, non-member)
    clearing_per_side: float = 0.19   # Tradovate clearing
    nfa_per_side: float = 0.02        # NFA assessment
    commission_per_side: float = 0.39 # Tradovate "Free" plan commission on micros

@dataclass(frozen=True)
class ContractSpec:
    tick_size: float = 0.25         # MES tick
    dollars_per_tick: float = 1.25  # MES $/tick
    contracts: int = 1

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

def ask_yes_no(prompt: str, default_yes: bool | None = None) -> bool:
    suffix = ""
    if default_yes is True: suffix = " [Y/n]"
    elif default_yes is False: suffix = " [y/N]"
    while True:
        raw = input(f"{prompt}{suffix}: ").strip().lower()
        if not raw and default_yes is not None:
            return default_yes
        if raw in ("y", "yes"): return True
        if raw in ("n", "no"):  return False
        print("  Please answer y/n.")

def per_side_total(fees: FuturesFees) -> float:
    return fees.exchange_per_side + fees.clearing_per_side + fees.nfa_per_side + fees.commission_per_side

def round_trip_fees(fees: FuturesFees, contracts: int) -> float:
    return 2 * per_side_total(fees) * contracts

def pnl_futures(entry: float, exit: float, side: str, spec: ContractSpec, fees: FuturesFees, slippage_ticks_rt: float) -> float:
    sign = 1 if side == "long" else -1
    ticks_per_point = 1.0 / spec.tick_size
    gross = sign * (exit - entry) * ticks_per_point * spec.dollars_per_tick * spec.contracts
    costs = round_trip_fees(fees, spec.contracts) + (slippage_ticks_rt * spec.dollars_per_tick * spec.contracts)
    return round(gross - costs, 2)

def net_per_contract(entry: float, exit: float, side: str, spec: ContractSpec, fees: FuturesFees, slippage_ticks_rt: float) -> float:
    sign = 1 if side == "long" else -1
    ticks_per_point = 1.0 / spec.tick_size
    gross = sign * (exit - entry) * ticks_per_point * spec.dollars_per_tick
    rt_fees_one = round_trip_fees(fees, 1)
    slip_usd_one = slippage_ticks_rt * spec.dollars_per_tick
    return round(gross - rt_fees_one - slip_usd_one, 2)

def main():
    print("=== FUTURES P&L (MES / Tradovate) ===")
    entry = ask_float("Entry price")
    exit_ = ask_float("Exit price")
    side = ask_side()
    contracts = ask_int("Number of contracts", default=1)

    has_no_commission = ask_yes_no('Do you have the "No Commission Membership"?', default_yes=False)

    spec = ContractSpec(contracts=contracts)
    if has_no_commission:
        fees = FuturesFees(commission_per_side=0.00)
        plan_label = "No Commission Membership"
    else:
        fees = FuturesFees()
        plan_label = "Free plan (commissioned)"

    slippage_ticks_rt = ask_float("Round-trip slippage (ticks)", default=1.0)

    total = pnl_futures(entry, exit_, side, spec, fees, slippage_ticks_rt)
    per_ct = net_per_contract(entry, exit_, side, spec, fees, slippage_ticks_rt)
    rt_fees = round(round_trip_fees(fees, contracts), 2)
    slip_usd = slippage_ticks_rt * spec.dollars_per_tick * contracts

    print("\n--- RESULT (FUTURES) ---")
    print(f"Contract: MES   Side: {side.upper()}  Contracts: {contracts}")
    print(f"Entry: {entry:.2f}  Exit: {exit_:.2f}  Tick: {spec.tick_size}  $/tick: {spec.dollars_per_tick}")
    print(f"Plan: {plan_label}")
    print(f"Fees RT (exch+clr+nfa+comm): ${rt_fees:.2f}")
    print(f"Slippage RT: {slippage_ticks_rt} ticks (= ${slip_usd:.2f})")
    print(f"P&L per contract: ${per_ct:.2f}")
    print(f"P&L total:        ${total:.2f}")

if __name__ == "__main__":
    main()

