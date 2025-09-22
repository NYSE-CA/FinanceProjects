from dataclasses import dataclass

@dataclass(frozen=True)
class SymbolConfig:
    symbol_root: str         # e.g. "MES" or "MCL"
    tick_size: float         # price increment (e.g., MES = 0.25, MCL = 0.01)
    dollars_per_tick: float  # tick value in USD (MES ≈ 1.25, MCL = 1.00)

DEFAULTS = {
    "MES": SymbolConfig(symbol_root="MES", tick_size=0.25, dollars_per_tick=1.25),
    "MCL": SymbolConfig(symbol_root="MCL", tick_size=0.01, dollars_per_tick=1.00),
}

DAY_RESET_HOUR_ET = 17  # CME typical session close; day P&L reset marker if you want to use it later

