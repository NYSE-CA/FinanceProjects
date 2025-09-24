from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

ISO_HINT = (
    'Use ISO like "2025-09-23T06:30" or "2025-09-23 06:30". '
    'If input already has an offset (e.g. Z or -05:00), it will be respected.'
)

def parse_dt(ts: str, assume_tz: str | None = None) -> datetime:
    """
    Parse a timestamp string into an aware datetime.
    - If ts has no timezone info and assume_tz is provided, apply that tz.
    - If ts includes tzinfo (e.g. 2025-09-23T06:30-05:00 or Z), keep it.
    """
    s = ts.replace(" ", "T")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"Could not parse '{ts}'. {ISO_HINT}") from e
    if dt.tzinfo is None:
        if not assume_tz:
            raise ValueError(f"'{ts}' lacks timezone info. Provide --from-tz. {ISO_HINT}")
        return dt.replace(tzinfo=ZoneInfo(assume_tz))
    return dt

def convert(ts: str, from_tz: str, to_tz: str) -> datetime:
    """
    Convert from 'from_tz' to 'to_tz'. If ts already has tzinfo, 'from_tz' is ignored.
    """
    dt = parse_dt(ts, assume_tz=from_tz)
    return dt.astimezone(ZoneInfo(to_tz))

