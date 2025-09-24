from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
from zoneinfo import ZoneInfo
from .config_loader import load_market_config, MarketConfig, Window

def _is_between(t_local: time, w: Window) -> bool:
    return (t_local >= w.start) and (t_local <= w.end)

def _weekday(dt_local: datetime) -> int:
    return dt_local.weekday()  # Mon=0..Sun=6

def market_status(ts: datetime, cfg: MarketConfig) -> dict:
    if ts.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")

    local = ts.astimezone(cfg.venue_tz)
    dow = _weekday(local)
    t = local.time()
    today = local.date()

    # Weekend rule: Fri >= friday_close, Sat all day, Sun < sunday_reopen
    if (dow == 4 and t >= cfg.friday_close) or (dow == 5) or (dow == 6 and t < cfg.sunday_reopen):
        return {"open": False, "label": "CLOSED", "reason": cfg.labels.get("closed_reason_weekend", "WEEKEND")}

    # Maintenance windows
    for m in cfg.maintenance:
        if dow in m.days and (t >= m.start and t < m.end):
            return {"open": False, "label": "CLOSED", "reason": cfg.labels.get("closed_reason_maintenance", "MAINTENANCE")}

    # Holidays full-day closure
    if today in cfg.holidays:
        return {"open": False, "label": "CLOSED", "reason": "HOLIDAY"}

    # Early close override (if defined): if label sets a special end for RTH
    ec = cfg.early_closes.get(today)
    if ec is not None:
        # If time is after special RTH end and before maintenance, consider CLOSED or POST by your preference
        if t > ec.rth_end:
            return {"open": False, "label": "CLOSED", "reason": ec.label}

    # Otherwise, use weekly windows
    for w in cfg.weekly.get(dow, []):
        if _is_between(t, w):
            return {"open": True, "label": w.label, "reason": None}

    # If no window matched on a trading day, treat as CLOSED
    return {"open": False, "label": "CLOSED", "reason": "OUTSIDE_SESSION"}

def next_open(ts: datetime, cfg: MarketConfig) -> datetime:
    """Walk forward minute by minute until an open is found. Efficient enough for our use-case."""
    step = timedelta(minutes=1)
    cur = ts
    # if closed now, start searching from now; if open, just return ts (back-compat)
    if market_status(ts, cfg)["open"]:
        return ts
    for _ in range(7*24*60):  # 1 week safety cap
        cur += step
        if market_status(cur, cfg)["open"]:
            return cur
    return cur  # fallback, should never hit

# Convenience for ES using packaged config path
CHI = ZoneInfo("America/Chicago")
def market_status_cme_es(ts: datetime) -> dict:
    cfg = load_market_config(__package__.replace("trading_calendar", "trading_calendar") + "/config/markets/cme_es.yaml")
    return market_status(ts, cfg)

def next_open_cme_es(ts: datetime) -> datetime:
    cfg = load_market_config(__package__.replace("trading_calendar", "trading_calendar") + "/config/markets/cme_es.yaml")
    return next_open(ts, cfg)

def is_open_cme_es(ts: datetime) -> bool:
    return market_status_cme_es(ts)["open"]

