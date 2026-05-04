""" LedgerZA Reporter
Two outputs:
  print_summary()  — structured terminal report
  export_json()    — canonical transactions + errors to JSON
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


#  Terminal report 

def print_summary(
    transactions: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    source_file: str = "",
    meta: dict[str, Any] | None = None,
    show_errors: bool = True,
) -> None:
    W = 52
    bar = "═" * W

    source_name = Path(source_file) if source_file else "unknown"
    source_label = transactions[0]["source"].upper() if transactions else "UNKNOWN"

    print(f"\n{bar}")
    print(f"  LedgerZA Report  -  {source_name}")
    print(f"  Bank: {source_label}")
    print(bar)

    #  Statement metadata (FNB only) 
    if meta:
        if meta.get("account_number"):
            print(f"  Account    : {meta['account_number']}")
        if meta.get("account_nickname"):
            print(f"  Nickname   : {meta['account_nickname']}")
        if meta.get("statement_date"):
            print(f"  Stmt Date  : {meta['statement_date']}")
        if meta.get("opening_balance") is not None:
            print(f"  Opening Bal: R{meta['opening_balance']:>10.2f}")
        if meta.get("closing_balance") is not None:
            print(f"  Closing Bal: R{meta['closing_balance']:>10.2f}")
        print()

    if not transactions:
        print("  No valid transactions parsed.")
        _print_errors(errors, show_errors)
        print(f"{bar}\n")
        return

    #  Totals 
    debits  = [t["amount"] for t in transactions if t["amount"] < 0]
    credits = [t["amount"] for t in transactions if t["amount"] >= 0]
    net     = sum(credits) + sum(debits)

    print(f"  Transactions : {len(transactions):>6}")
    print(f"  Total in     : R{sum(credits):>10.2f}")
    print(f"  Total out    : R{sum(debits):>10.2f}")
    print(f"  Net          : R{net:>10.2f}")
    print(f"  Date range   : {_date_range(transactions)}")
    print()

    #  Category breakdown 
    print(f"  {'Category':<22} {'Txns':>5}  {'Total':>12}")
    print(f"  {'-'*22}  {'-'*5}  {'-'*12}")
    by_cat = _group_by_category(transactions)
    for cat, (count, total) in sorted(by_cat.items(), key=lambda x: x[1][1]):
        print(f"  {cat:<22} {count:>5}  R{total:>10.2f}")

    #  Errors 
    _print_errors(errors, show_errors)

    print(f"\n{bar}\n")


def _print_errors(errors: list[dict], show: bool) -> None:
    if not errors or not show:
        return
    print(f"\n  {''*48}")
    print(f"  ⚠  {len(errors)} row(s) skipped or failed:")
    for e in errors:
        row_label = f"Row {e['row']}" if e.get("row") else "File"
        src       = f"[{e['source']}] " if e.get("source") else ""
        print(f"    {src}{row_label}: {e['reason']}")


def _date_range(transactions: list[dict]) -> str:
    dates = sorted(t["date"] for t in transactions if t.get("date"))
    return f"{dates[0]}  →  {dates[-1]}" if dates else "n/a"


def _group_by_category(transactions: list[dict]) -> dict[str, tuple[int, float]]:
    groups: dict[str, list[float]] = {}
    for t in transactions:
        groups.setdefault(t.get("category", "other"), []).append(t["amount"])
    return {cat: (len(amts), sum(amts)) for cat, amts in groups.items()}


#  JSON export 

def export_json(
    transactions: list[dict[str, Any]],
    output_path: Path,
    errors: list[dict[str, Any]] | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """ Write a structured JSON output file """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "meta":         meta or {},
        "transactions": transactions,
        "errors":       errors or [],
    }

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, default=_json_default)


def _json_default(obj: Any) -> Any:
    """Fallback serialiser for non-standard types (e.g. Path)."""
    return str(obj)
