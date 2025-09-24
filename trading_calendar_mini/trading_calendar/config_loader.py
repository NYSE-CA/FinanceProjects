from __future__ import annotations
from dataclasses import dataclass
from datetime import time, date
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo
import yaml

DOW_MAP = {"Mon":0,"Tue":1,"Wed":2,"Thu":3,"Fri":4,"Sat":5,"Sun":6}

@dataclass
class Window:
    start: time
    end: time
    label: str

@dataclass
class Maintenance:
    days: List[int]
    start: time
    end: time

@dataclass
class EarlyClose:
    rth_end: time
    label: str

@dataclass
class MarketConfig:
    market_id: str
    venue_tz: ZoneInfo
    weekly: Dict[int, List[Window]]    # weekday -> windows
    maintenance: List[Maintenance]
    friday_close: time                  # weekend close start on Fri
    sunday_reopen: time
    labels: Dict[str, str]
    holidays: List[date]
    early_closes: Dict[date, EarlyClose]

def _parse_time(s: str) -> time:
    # supports HH:MM or HH:MM:SS
    parts = [int(p) for p in s.split(":")]
    if len(parts) == 2:
        return time(parts[0], parts[1])
    if len(parts) == 3:
        return time(parts[0], parts[1], parts[2])
    raise ValueError(f"bad time '{s}'")

def load_market_config(path: str) -> MarketConfig:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    venue = ZoneInfo(raw["venue_tz"])
    weekly: Dict[int, List[Window]] = {i: [] for i in range(7)}
    for block in raw.get("weekly", []):
        days = block["days"]
        wins = block["windows"]
        for d in days:
            wd = DOW_MAP[d]
            for w in wins:
                weekly[wd].append(Window(
                    start=_parse_time(w["start"]),
                    end=_parse_time(w["end"]),
                    label=w["label"]
                ))

    maint: List[Maintenance] = []
    for m in raw.get("maintenance", []):
        maint.append(Maintenance(
            days=[DOW_MAP[d] for d in m["days"]],
            start=_parse_time(m["start"]),
            end=_parse_time(m["end"]),
        ))

    wc = raw.get("weekend_close", {})
    friday_close = _parse_time(wc.get("friday_close", "16:00"))
    sunday_reopen = _parse_time(wc.get("sunday_reopen", "17:00"))

    labels = raw.get("labels", {})
    hols = []
    for d in raw.get("holidays", []):
        y,m,dd = [int(x) for x in d.split("-")]
        hols.append(date(y,m,dd))

    early: Dict[date, EarlyClose] = {}
    for k, v in (raw.get("early_closes") or {}).items():
        y,m,dd = [int(x) for x in k.split("-")]
        early[date(y,m,dd)] = EarlyClose(
            rth_end=_parse_time(v["rth_end"]),
            label=v.get("label", "EARLY_CLOSE")
        )

    return MarketConfig(
        market_id=raw["market_id"],
        venue_tz=venue,
        weekly=weekly,
        maintenance=maint,
        friday_close=friday_close,
        sunday_reopen=sunday_reopen,
        labels=labels,
        holidays=hols,
        early_closes=early,
    )

