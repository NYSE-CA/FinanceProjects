from __future__ import annotations
import argparse, json, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .tz import convert as tz_convert, parse_dt
from .sessions import (
    CHI,
    market_status_cme_es,
    next_open_cme_es,
    market_status,
    next_open,
)
from .config_loader import load_market_config

PKG_DIR = os.path.dirname(__file__)

def tzutil_main():
    p = argparse.ArgumentParser(prog="tzutil", description="Timezone utilities")
    sp = p.add_subparsers(dest="cmd", required=True)

    p_convert = sp.add_parser("convert", help="Convert a timestamp between timezones")
    p_convert.add_argument("timestamp", help='e.g. "2025-09-23T06:30"')
    p_convert.add_argument("from_tz", help="e.g. America/Mazatlan")
    p_convert.add_argument("to_tz", help="e.g. UTC")
    p_convert.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    args = p.parse_args()
    if args.cmd == "convert":
        dt = tz_convert(args.timestamp, args.from_tz, args.to_tz)
        print(json.dumps({"timestamp_out": dt.isoformat()})) if args.json else print(dt.isoformat())

def cal_main():
    p = argparse.ArgumentParser(prog="tcal", description="Trading calendar utilities")
    sp = p.add_subparsers(dest="cmd", required=True)

    # NEW: --config (overrides --market); --market is now optional
    p_open = sp.add_parser("is-open", help="Is the market open now or at a given time?")
    p_open.add_argument("--market", choices=["cme_es"], help="Shortcut for built-in market configs")
    p_open.add_argument("--config", help="Path to a market YAML (overrides --market)")
    p_open.add_argument("--at", default="now", help='ISO timestamp or "now"')
    p_open.add_argument("--tz", default=os.environ.get("TCAL_TZ", "UTC"), help="Display timezone (e.g., America/Mazatlan)")
    p_open.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    p_next = sp.add_parser("next-open", help="Next open time for a market")
    p_next.add_argument("--market", choices=["cme_es"])
    p_next.add_argument("--config", help="Path to a market YAML (overrides --market)")
    p_next.add_argument("--from", dest="from_ts", default="now", help='ISO timestamp or "now"')
    p_next.add_argument("--tz", default=os.environ.get("TCAL_TZ", "UTC"), help="Display timezone")
    p_next.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    args = p.parse_args()

    def _load_cfg():
        # Use explicit config file if provided
        if getattr(args, "config", None):
            return load_market_config(args.config)
        # Or built-in shortcuts
        if getattr(args, "market", None) == "cme_es":
            return load_market_config(os.path.join(PKG_DIR, "config/markets/cme_es.yaml"))
        raise SystemExit("Provide --market or --config")

    if args.cmd == "is-open":
        ts = _coerce_now_or_parse(args.at)
        disp_tz = ZoneInfo(args.tz)
        cfg = _load_cfg()

        st = market_status(ts, cfg)
        out = {
            "market": cfg.market_id,
            "open": st["open"],
            "label": st["label"],
            "reason": st["reason"],
            "time": {
                "display_tz": args.tz,
                "display": ts.astimezone(disp_tz).isoformat(),
                "venue_tz": cfg.venue_tz.key,
                "venue": ts.astimezone(cfg.venue_tz).isoformat(),
                "utc": ts.astimezone(ZoneInfo("UTC")).isoformat(),
            },
        }
        if not st["open"]:
            nxt = next_open(ts, cfg)
            delta = nxt - ts
            out["next_open"] = {
                "display": nxt.astimezone(disp_tz).isoformat(),
                "venue": nxt.astimezone(cfg.venue_tz).isoformat(),
                "utc": nxt.astimezone(ZoneInfo("UTC")).isoformat(),
                "in": _fmt_timedelta(delta),
            }
        print(json.dumps(out, indent=2) if args.json else _pretty_status(out))

    elif args.cmd == "next-open":
        ts = _coerce_now_or_parse(args.from_ts)
        disp_tz = ZoneInfo(args.tz)
        cfg = _load_cfg()

        nxt = next_open(ts, cfg)
        out = {
            "market": cfg.market_id,
            "from": {
                "display_tz": args.tz,
                "display": ts.astimezone(disp_tz).isoformat(),
                "venue": ts.astimezone(cfg.venue_tz).isoformat(),
                "utc": ts.astimezone(ZoneInfo("UTC")).isoformat(),
            },
            "next_open": {
                "display": nxt.astimezone(disp_tz).isoformat(),
                "venue": nxt.astimezone(cfg.venue_tz).isoformat(),
                "utc": nxt.astimezone(ZoneInfo("UTC")).isoformat(),
                "in": _fmt_timedelta(nxt - ts),
            },
        }
        print(json.dumps(out, indent=2) if args.json else _pretty_next(out))

def _coerce_now_or_parse(s: str) -> datetime:
    if s.lower() == "now":
        return datetime.now(timezone.utc)
    return parse_dt(s, assume_tz="UTC")

def _fmt_timedelta(td) -> str:
    total = int(td.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    h, r = divmod(total, 3600)
    m, _ = divmod(r, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d}d")
    if h or d: parts.append(f"{h}h")
    parts.append(f"{m}m")
    return sign + " ".join(parts)

def _pretty_status(out: dict) -> str:
    hdr = f"{out['market'].upper()}  |  {'OPEN' if out['open'] else 'CLOSED'}"
    hdr += f" ({out['label']})" if out["open"] else f" ({out['reason']})"
    lines = [
        hdr,
        "-" * len(hdr),
        f"time @ {out['time']['display_tz']}: {out['time']['display']}",
        f"time @ venue ({out['time']['venue_tz']}): {out['time']['venue']}",
        f"time @ UTC: {out['time']['utc']}",
    ]
    if "next_open" in out:
        n = out["next_open"]
        lines += [
            "",
            f"next open in: {n['in']}",
            f"→ {out['time']['display_tz']}: {n['display']}",
            f"→ venue ({out['time']['venue_tz']}): {n['venue']}",
            f"→ UTC: {n['utc']}",
        ]
    return "\n".join(lines)

def _pretty_next(out: dict) -> str:
    lines = [
        f"{out['market'].upper()}  |  NEXT OPEN",
        "---------------------------",
        f"from @ {out['from']['display_tz']}: {out['from']['display']}",
        f"from @ venue: {out['from']['venue']}",
        f"from @ UTC: {out['from']['utc']}",
        "",
        f"next open in: {out['next_open']['in']}",
        f"→ {out['from']['display_tz']}: {out['next_open']['display']}",
        f"→ venue: {out['next_open']['venue']}",
        f"→ UTC: {out['next_open']['utc']}",
    ]
    return "\n".join(lines)

