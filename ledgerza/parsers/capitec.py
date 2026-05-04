"""Capitec Bank CSV statement parser."""

from __future__ import annotations
from pathlib import Path

from .base import BaseParser, ParseResult
from ..normalizer import parse_date, parse_amount
from ..schema import make_transaction, make_error


# Required columns that must be present for this parser to claim the file
_REQUIRED_COLS = {"posting date", "money in", "money out"}

# All recognised column aliases (lowercased)
_COL_ALIASES: dict[str, str] = {
    "nr": "nr",
    "account": "account",
    "posting date": "posting_date",
    "transaction date": "transaction_date",
    "description": "description",
    "original description":"original_description",
    "parent category": "parent_category",
    "category": "category",
    "money in": "money_in",
    "money out": "money_out",
    "fee": "fee",
    "balance": "balance",
}


class CapitecParser(BaseParser):
    SOURCE = "capitec"

    @classmethod
    def can_parse(cls, path: Path) -> bool:
        """
        Capitec files: first line is a header containing
        'posting date', 'money in', 'money out' — all three required.
        """
        try:
            with path.open(encoding="utf-8-sig", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    lower = stripped.lower()
                    return all(col in lower for col in _REQUIRED_COLS)
        except OSError:
            return False
        return False

    def parse(self, path: Path) -> ParseResult:
        try:
            raw_lines, _ = self._load(path)
        except (FileNotFoundError, ValueError) as exc:
            return self._file_error(path, str(exc))

        delimiter    = self._sniff(raw_lines)
        rows         = self._csv_rows(raw_lines, delimiter)
        transactions = []
        errors       = []

        for i, row in enumerate(rows, start=2):  # row 1 is header
            # Normalise column names via alias map
            norm = self._normalise_cols(row)
            result = self._parse_row(norm, i)
            if "reason" in result:
                errors.append(result)
            else:
                transactions.append(result)

        return ParseResult(transactions, errors, {}, str(path))


    def _normalise_cols(self, row: dict[str, str]) -> dict[str, str]:
        """Remap raw column keys to canonical internal names."""
        return {
            _COL_ALIASES.get(k.strip().lower(), k.strip().lower()): v
            for k, v in row.items()
        }

    def _parse_row(self, row: dict[str, str], row_num: int) -> dict:
        # ── Required: at least one date 
        raw_date = row.get("posting_date") or row.get("transaction_date", "")
        if not raw_date:
            return make_error(
                row=row_num,
                reason="Missing 'Posting Date' and 'Transaction Date'",
                raw=row,
                source=self.SOURCE,
            )

        date = parse_date(raw_date)
        if date is None:
            return make_error(
                row=row_num,
                reason=f"Unparseable date: '{raw_date}'",
                raw=row,
                source=self.SOURCE,
            )

        # Amount from Money In / Money Out 
        money_in_raw  = row.get("money_in", "")
        money_out_raw = row.get("money_out", "")

        if not money_in_raw and not money_out_raw:
            return make_error(
                row=row_num,
                reason="Both 'Money In' and 'Money Out' are empty",
                raw=row,
                source=self.SOURCE,
            )

        amount: float
        if money_in_raw:
            val = parse_amount(money_in_raw)
            if val is None:
                return make_error(
                    row=row_num,
                    reason=f"Unparseable Money In: '{money_in_raw}'",
                    raw=row,
                    source=self.SOURCE,
                )
            amount = abs(val)   # always positive for inflows
        else:
            val = parse_amount(money_out_raw)
            if val is None:
                return make_error(
                    row=row_num,
                    reason=f"Unparseable Money Out: '{money_out_raw}'",
                    raw=row,
                    source=self.SOURCE,
                )
            amount = -abs(val)  # always negative for outflows

        # Fee 
        service_fee = parse_amount(row.get("fee", "")) or 0.0

        # Balance 
        balance = parse_amount(row.get("balance", ""))

        # Description — prefer 'description', fall back to 'original_description' 
        description = (
            row.get("description") or row.get("original_description") or "UNKNOWN"
        ).strip()

        # Category — Capitec supplies both parent and sub-category 
        category = (
            row.get("category") or row.get("parent_category") or "uncategorized"
        ).strip().lower()

        return make_transaction(
            date        = date,
            description = description,
            amount      = amount,
            service_fee = service_fee,
            balance     = balance,
            category    = category,
            source      = self.SOURCE,
        )
