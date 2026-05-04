from __future__ import annotations
from typing import Any


#  Canonical transaction 

TRANSACTION_FIELDS = (
    "date",          # str  — ISO 8601 'YYYY-MM-DD'
    "description",   # str  — uppercased, stripped
    "reference",     # str  — reference number / memo (may be empty)
    "amount",        # float — negative = debit, positive = credit
    "service_fee",   # float — accrued service fee (0.0 if absent)
    "balance",       # float | None — running balance (None if not in export)
    "category",      # str  — assigned by categorizer
    "source",        # str  — parser identifier e.g. 'fnb', 'capitec'
)


def make_transaction(
    *,
    date: str,
    description: str,
    amount: float,
    source: str,
    reference: str = "",
    service_fee: float = 0.0,
    balance: float | None = None,
    category: str = "uncategorized",
) -> dict[str, Any]:
    """
    Factory for canonical transaction dicts.
    Named-only arguments enforce explicit construction at every call site.
    """
    return {
        "date":        date,
        "description": description.upper().strip(),
        "reference":   reference.strip(),
        "amount":      float(amount),
        "service_fee": float(service_fee),
        "balance":     balance,
        "category":    category.strip().lower(),
        "source":      source,
    }


#  Parse error 

def make_error(
    *,
    row: int,
    reason: str,
    raw: dict | None = None,
    source: str = "",
) -> dict[str, Any]:
    """
    Factory for parse error dicts.
    Errors are collected per-row; a bad row never aborts a file.
    """
    return {
        "row":    row,
        "reason": reason,
        "raw":    raw or {},
        "source": source,
    }


#  Statement metadata (FNB header block) 

def make_statement_meta(
    *,
    account_number: str = "",
    account_nickname: str = "",
    statement_date: str = "",
    opening_balance: float | None = None,
    closing_balance: float | None = None,
    total_debits: float | None = None,
    total_credits: float | None = None,
    num_debits: int | None = None,
    num_credits: int | None = None,
) -> dict[str, Any]:
    return {
        "account_number":   account_number,
        "account_nickname": account_nickname,
        "statement_date":   statement_date,
        "opening_balance":  opening_balance,
        "closing_balance":  closing_balance,
        "total_debits":     total_debits,
        "total_credits":    total_credits,
        "num_debits":       num_debits,
        "num_credits":      num_credits,
    }
