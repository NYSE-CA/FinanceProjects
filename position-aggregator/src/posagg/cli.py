from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from .models import Fill
from .engine import PositionEngine
from .marks import StaticMarkProvider

def parse_fill(row: dict) -> Fill:
    # CSV columns: ts,symbol,side,qty,price,fees,account,exec_id,note
    return Fill(
        ts=row.get("ts",""),
        symbol=row["symbol"].strip(),
        side=row["side"].strip().upper(),
        qty=int(row["qty"]),
        price=float(row["price"]),
        fees=float(row.get("fees",0) or 0),
        account=row.get("account","default"),
        exec_id=row.get("exec_id") or None,
        note=row.get("note",""),
    )

def cmd_load_csv(args) -> None:
    engine = PositionEngine(mark_provider=StaticMarkProvider())
    with open(args.path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            engine.apply_fill(parse_fill(row))
    _print_blotter(engine)

def cmd_add_fill(args) -> None:
    engine = PositionEngine(mark_provider=StaticMarkProvider())
    # allow a single manual fill for quick testing
    fill = Fill(
        ts=args.ts,
        symbol=args.symbol,
        side=args.side.upper(),
        qty=args.qty,
        price=args.price,
        fees=args.fees,
        account="default",
        exec_id=args.exec_id,
    )
    engine.apply_fill(fill)
    _print_blotter(engine)

def _print_blotter(engine: PositionEngine) -> None:
    lines = engine.all_blotter()
    if not lines:
        print("No positions.")
        return
    print("SYMBOL  NET  AVG_PRICE   MARK      UPL       RPL       FEES     NLV_DELTA")
    for bl in lines:
        mark_str = f"{bl.mark:.2f}" if bl.mark is not None else "--"
        print(f"{bl.symbol:<6} {bl.net_qty:>4}  {bl.avg_price:>9.2f}  {mark_str:>7}  "
              f"{bl.upl:>8.2f}  {bl.rpl:>8.2f}  {bl.fees:>8.2f}  {bl.nlv_delta:>10.2f}")

def main():
    p = argparse.ArgumentParser(prog="posagg", description="Position Aggregator")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_csv = sub.add_parser("load-csv", help="Load fills from CSV and show blotter")
    p_csv.add_argument("path", type=Path)
    p_csv.set_defaults(func=cmd_load_csv)

    p_add = sub.add_parser("add-fill", help="Add a single fill and show blotter")
    p_add.add_argument("--ts", default="", help="timestamp")
    p_add.add_argument("--symbol", required=True)
    p_add.add_argument("--side", required=True, choices=["BUY","SELL"])
    p_add.add_argument("--qty", required=True, type=int)
    p_add.add_argument("--price", required=True, type=float)
    p_add.add_argument("--fees", type=float, default=0.0)
    p_add.add_argument("--exec-id", dest="exec_id", default=None)
    p_add.set_defaults(func=cmd_add_fill)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

