from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="LedgerZA",
        description="Parse and summarise South African bank CSV exports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    p.add_argument(
        "-f", "--file",
        nargs="+",
        type=Path,
        metavar="PATH",
        required=True,
        help="CSV file(s) or a single folder.",
    )

    # Output
    out = p.add_argument_group("output")
    out.add_argument("--output", "-o", type=Path, help="Output JSON file")
    out.add_argument("--no-export", action="store_true")
    out.add_argument("--no-summary", action="store_true")
    out.add_argument("--hide-errors", action="store_true")

    # Folder
    folder = p.add_argument_group("folder")
    folder.add_argument("--recursive", "-r", action="store_true")

    # Cleaning
    clean = p.add_argument_group("cleaning")
    clean.add_argument("--dedup", action="store_true")

    # Filters
    filt = p.add_argument_group("filters")
    filt.add_argument("--from", dest="from_date")
    filt.add_argument("--to", dest="to_date")
    filt.add_argument("--min-amount", type=float)
    filt.add_argument("--max-amount", type=float)
    filt.add_argument("--keyword")
    filt.add_argument("--category")

    return p

# Input
def resolve_inputs(paths: list[Path], recursive: bool) -> list[Path]:
    """Expand files + folders into a flat list of CSV files."""
    from .detector import CSV_EXTENSIONS

    result: list[Path] = []

    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

        if p.is_file():
            result.append(p)
            continue

        # Folder
        pattern = "**/*" if recursive else "*"
        for f in sorted(p.glob(pattern)):
            if f.is_file() and f.suffix.lower() in CSV_EXTENSIONS:
                result.append(f)

    if not result:
        raise ValueError("No CSV files found.")

    return result


def parse_all(paths: list[Path]):
    from .detector import detect, UnknownFormatError
    from .categorizer import categorize

    all_txns = []
    all_errors = []
    all_meta = []

    for path in paths:
        try:
            parser = detect(path)
        except (FileNotFoundError, UnknownFormatError) as exc:
            all_errors.append({
                "row": 0,
                "reason": str(exc),
                "source": str(path),
            })
            continue

        result = parser.parse(path)

        # Categorize
        for txn in result.transactions:
            txn["category"] = categorize(txn["description"], txn.get("category"))

        all_txns.extend(result.transactions)
        all_errors.extend(result.errors)

        if result.meta:
            all_meta.append(result.meta)

    return all_txns, all_errors, all_meta

# Cleaning
def apply_cleaning(transactions: list[dict], args: argparse.Namespace):
    from .cleaner import (
        deduplicate, filter_by_date, filter_by_amount,
        filter_by_description, filter_by_category,
    )

    original = len(transactions)

    if args.dedup:
        transactions, removed = deduplicate(transactions)
        print(f"Duplicates removed: {removed}")

    if args.from_date or args.to_date:
        transactions = filter_by_date(transactions, args.from_date, args.to_date)

    if args.min_amount is not None or args.max_amount is not None:
        transactions = filter_by_amount(transactions, args.min_amount, args.max_amount)

    if args.keyword:
        transactions = filter_by_description(transactions, args.keyword)

    if args.category:
        transactions = filter_by_category(transactions, args.category)

    print(f"Transactions after cleaning: {len(transactions)} (filtered {original - len(transactions)})")

    return transactions


# Output
def export(transactions, errors, meta, output_path: Path):
    from .reporter import export_json

    try:
        export_json(transactions, output_path, errors, meta)
        print(f"JSON exported → {output_path}")
    except OSError as exc:
        print(f"Export failed: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        paths = resolve_inputs(args.file, args.recursive)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # 1. Parse
    transactions, errors, metas = parse_all(paths)

    # 2. Clean 
    transactions = apply_cleaning(transactions, args)

    # 3. Meta strategy (simple: last file wins)
    meta = metas[-1] if metas else {}

    # 4. Output
    if not args.no_summary:
        from .reporter import print_summary
        print_summary(transactions, errors, "merged", meta, not args.hide_errors)

    if not args.no_export:
        out = args.output or Path("output") / "merged.json"
        export(transactions, errors, meta, out)

    # Exit logic
    if errors and not transactions:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())