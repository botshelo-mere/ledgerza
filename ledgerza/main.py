from datetime import datetime
import csv
from pathlib import Path
from collections import defaultdict

def read_csv(file_path: str) -> list[dict]:
    if not file_path:
        raise ValueError("File path not provided")
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"file not found: {file_path}")
    try:
        with open(path, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f, delimiter=','))
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV: {e}") from e


def clean_rows(rows: list[dict]) -> list[dict]:
    clean = []
    for row in rows:
        cleaned_row = {}
        for k, v in row.items():
            clean_k = k.strip().lower()
            clean_v = v.strip() if v is not None else ""
            cleaned_row[clean_k] = clean_v

        if 'posting date' in cleaned_row and cleaned_row['posting date']:
            cleaned_row['posting date'] = cleaned_row['posting date'].replace('/', '-')

        # Compute amount from money in / money out / fee
        money_in = cleaned_row.get('money in', '')
        money_out = cleaned_row.get('money out', '')
        fee = cleaned_row.get('fee', '')
        in_amt = safe_float(money_in) or 0.0
        out_amt = safe_float(money_out) or 0.0
        fee_amt = safe_float(fee) or 0.0
        computed_amt = in_amt + out_amt + fee_amt
        cleaned_row['balance'] = str(computed_amt)

        cleaned_row['description'] = cleaned_row.get(
            'description', cleaned_row.get('original description', '')
        ).strip()

        cat = cleaned_row.get('category', cleaned_row.get('parent category', '')).strip().lower()
        cleaned_row['category'] = cat if cat else 'uncategorised'

        clean.append(cleaned_row)
    return clean


def safe_float(value: str) -> float | None:
    try:
        clean = value.replace("R", "").replace(" ", "")
        if "," in clean and "." not in clean:
            clean = clean.replace(",", ".")
        return float(clean)
    except ValueError:
        return None


def validate_row(row: dict) -> tuple[bool, str]:
    required = ["posting date", "description", "balance"]
    for field in required:
        if field not in row or not row[field].strip():
            return False, f"Missing field: {field}"
        
    if safe_float(row["balance"]) is None:
        return False, f"Invalid amount: '{row['balance']}'"
    try:
        datetime.strptime(row["posting date"], "%Y-%m-%d")
    except ValueError:
        return False, f"Invalid date: {row['posting date']}"

    return True, "valid rows"


def validate_all(rows: list[dict]) -> tuple[list, list]:
    good, bad = [], []
    for i, row in enumerate(rows, 1):
        valid, reason = validate_row(row)
        if valid:
            good.append(row)
        else:
            bad.append({"row": i, "reason": reason, "data": row})
    return good, bad


def summarize(rows: list[dict], filename: str) -> None:
    if not rows:
        print("No valid transactions to summarize.")
        return

    txns = len(rows)
    earned = [safe_float(r["money in"]) or 0.0 for r in rows]
    spent = [safe_float(r["money out"]) or 0.0 for r in rows]

    total_earned = sum(a for a in earned if a > 0)
    total_spent = sum(a for a in spent if a < 0)
    net = total_earned + total_spent

    dates = [datetime.strptime(r["posting date"], "%Y-%m-%d") for r in rows if r.get("posting date")]
    date_range = f"{min(dates).strftime('%Y-%m-%d')} → {max(dates).strftime('%Y-%m-%d')}" if dates else "N/A"

    category_data = defaultdict(lambda: {'txns': 0, 'total': 0.0})
    for row in rows:
        cat = row.get('category', 'uncategorised')
        amt = safe_float(row['balance']) or 0.0
        category_data[cat]['txns'] += 1
        category_data[cat]['total'] += amt

    print(f"\n{'=' * 60}")
    print(f"ledgerZA REPORT — {filename}")
    print(f"Bank: Capitec")
    print(f"{'=' * 60}")
    print(f"Transactions : {txns}")
    print(f"Total earned : R {total_earned:.2f}")
    print(f"Total spent  : R {total_spent:.2f}")
    print(f"Net          : R {net:.2f}")
    print(f"Date range   : {date_range}")
    print()
    print("Category          Txns     Total")
    print("-" * 40)
    
    for cat in sorted(category_data.keys()):
        data = category_data[cat]
        total_str = f"R {data['total']:.2f}"
        print(f"{cat:<17} {data['txns']:>4} {total_str:>10}")
    print(f"{'=' * 60}")


def parse_and_summarize(filename: str) -> None:
    """Main library entry point."""
    raw_rows = read_csv(filename)
    rows = clean_rows(raw_rows)
    good, bad = validate_all(rows)

    if bad:
        print(f"{len(bad)} invalid rows")
        for error in bad:
            print(f"Row {error['row']}: {error['reason']}")

    if good:
        summarize(good, filename)
    else:
        print("No valid rows to summarize.")
