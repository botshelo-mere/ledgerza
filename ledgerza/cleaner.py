from __future__ import annotations
from typing import Any


# Deduplication 

def deduplicate(
    transactions: list[dict[str, Any]],
    keys: tuple[str, ...] = ("date", "description", "amount"),
) -> tuple[list[dict[str, Any]], int]:
    """
    Remove exact duplicates by hashing a subset of fields.
    First occurrence wins.

    Returns (deduplicated_list, count_removed).
    """
    seen: set[tuple] = set()
    result: list[dict[str, Any]] = []
    removed = 0

    for txn in transactions:
        fingerprint = tuple(txn.get(k) for k in keys)
        if fingerprint in seen:
            removed += 1
        else:
            seen.add(fingerprint)
            result.append(txn)

    return result, removed


# Missing value handling 

def fill_missing(
    transactions: list[dict[str, Any]],
    field: str,
    default: Any,
) -> list[dict[str, Any]]:
    """
    Replace None / empty-string values in `field` with `default`.
    Returns a new list with copies of affected rows.
    """
    result = []
    for txn in transactions:
        val = txn.get(field)
        if val is None or val == "":
            txn = {**txn, field: default}
        result.append(txn)
    return result


def drop_if_missing(
    transactions: list[dict[str, Any]],
    field: str,
) -> tuple[list[dict[str, Any]], int]:
    """
    Drop rows where `field` is None or empty.
    Returns (kept, count_dropped).
    """
    kept    = [t for t in transactions if t.get(field) not in (None, "")]
    dropped = len(transactions) - len(kept)
    return kept, dropped


# Column standardisation 

def standardize_descriptions(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Uppercase + strip all description fields.
    Already done at parse time, but useful after a merge from external sources.
    """
    return [{**t, "description": t["description"].upper().strip()} for t in transactions]


def standardize_dates(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Re-run date parsing on the 'date' field to guarantee ISO 8601 format.
    Useful after merging files from parsers with different date outputs.
    """
    from .normalizer import parse_date
    result = []
    for txn in transactions:
        date = parse_date(txn.get("date", ""))
        result.append({**txn, "date": date or txn.get("date", "")})
    return result


#  Filters 

def filter_by_date(
    transactions: list[dict[str, Any]],
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    Keep transactions within [from_date, to_date] (inclusive, ISO 8601 strings).
    None means no bound on that side.
    """
    result = []
    for txn in transactions:
        d = txn.get("date", "")
        if from_date and d < from_date:
            continue
        if to_date and d > to_date:
            continue
        result.append(txn)
    return result


def filter_by_amount(
    transactions: list[dict[str, Any]],
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> list[dict[str, Any]]:
    """
    Keep transactions where amount falls within [min_amount, max_amount].
    Comparisons are on the raw signed float (negative = debit).
    """
    result = []
    for txn in transactions:
        amt = txn.get("amount", 0.0)
        if min_amount is not None and amt < min_amount:
            continue
        if max_amount is not None and amt > max_amount:
            continue
        result.append(txn)
    return result


def filter_by_description(
    transactions: list[dict[str, Any]],
    keyword: str,
    case_sensitive: bool = False,
) -> list[dict[str, Any]]:
    """
    Keep transactions whose description contains `keyword`.
    """
    kw = keyword if case_sensitive else keyword.upper()
    return [
        t for t in transactions
        if kw in (t.get("description", "") if case_sensitive else t.get("description", "").upper())
    ]


def filter_by_category(
    transactions: list[dict[str, Any]],
    category: str,
) -> list[dict[str, Any]]:
    """Keep transactions matching a specific category (case-insensitive)."""
    cat = category.strip().lower()
    return [t for t in transactions if t.get("category", "").lower() == cat]


#  Transformations 

def add_month_field(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add a 'month' field ('YYYY-MM') derived from 'date'.
    Useful for grouping / pivot analysis.
    """
    result = []
    for txn in transactions:
        date = txn.get("date", "")
        month = date[:7] if len(date) >= 7 else ""
        result.append({**txn, "month": month})
    return result


def add_abs_amount_field(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add an 'abs_amount' field — unsigned magnitude of the transaction.
    Useful for sorting by size regardless of direction.
    """
    return [{**t, "abs_amount": abs(t.get("amount", 0.0))} for t in transactions]


def split_debits_credits(
    transactions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split transactions into (debits, credits) lists.
    Debits: amount < 0. Credits: amount >= 0.
    """
    debits  = [t for t in transactions if t.get("amount", 0.0) < 0]
    credits = [t for t in transactions if t.get("amount", 0.0) >= 0]
    return debits, credits


#  Merge 

def merge(
    *transaction_lists: list[dict[str, Any]],
    dedup: bool = True,
    sort_by_date: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    """
    Merge multiple transaction lists into one.

    Args:
        *transaction_lists: Any number of canonical transaction lists.
        dedup:              Remove duplicates after merging (default True).
        sort_by_date:       Sort merged result by date ascending (default True).

    Returns:
        (merged_list, duplicates_removed)
    """
    combined: list[dict[str, Any]] = []
    for lst in transaction_lists:
        combined.extend(lst)

    removed = 0
    if dedup:
        combined, removed = deduplicate(combined)

    if sort_by_date:
        combined.sort(key=lambda t: t.get("date", ""))

    return combined, removed
