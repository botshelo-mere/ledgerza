"""FNB (First National Bank) CSV statement parser."""

from __future__ import annotations
from pathlib import Path

from .base import BaseParser, ParseResult
from ..normalizer import parse_date, parse_amount, sniff_delimiter
from ..schema import make_transaction, make_error, make_statement_meta


# Header keys 
_HEADER_KEYS = {
    "recreated statement",
    "date",
    "account nickname",
    "account number",
    "opening balance",
    "closing balance",
    "debits",
    "credits",
    "number of debits",
    "number of credits",
}

# Required transaction columns (lowercased)
_TXN_COLS = {"effective date", "description", "amount"}


class FNBParser(BaseParser):
    SOURCE = "fnb"

    @classmethod
    def can_parse(cls, path: Path) -> bool:
        try:
            with path.open(encoding="utf-8-sig", errors="replace") as fh:
                lines = [l for l in fh.readlines() if l.strip()]
            if not lines:
                return False
            first = lines[0].lower()
            has_header = "recreated statement" in first
            has_txn_col = any("effective date" in l.lower() for l in lines)
            return has_header and has_txn_col
        except OSError:
            return False

    def parse(self, path: Path) -> ParseResult:
        try:
            raw_lines, _ = self._load(path)
        except (FileNotFoundError, ValueError) as exc:
            return self._file_error(path, str(exc))

        delimiter = self._sniff(raw_lines)
        meta, txn_lines, header_errors = self._split_sections(raw_lines, delimiter)

        if not txn_lines:
            err = make_error(row=0, reason="No transaction section found", source=self.SOURCE)
            return ParseResult([], [err] + header_errors, meta, str(path))

        transactions, parse_errors = self._parse_transactions(txn_lines, delimiter)
        all_errors = header_errors + parse_errors

        return ParseResult(transactions, all_errors, meta, str(path))

    # Private

    def _split_sections(
        self, lines: list[str], delimiter: str
    ) -> tuple[dict, list[str], list[dict]]:
        """
        Walk raw lines:
          - Collect key=value header rows until the blank separator
          - Collect everything from the 'Effective Date' header row onward as txn_lines
        Returns (meta_dict, txn_lines, header_errors).
        """
        import csv, io

        meta_raw: dict[str, str] = {}
        txn_start_idx: int | None = None
        errors: list[dict] = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            lower = stripped.lower()

            # Detect the transaction header row
            if "effective date" in lower:
                txn_start_idx = i
                break

            # Parse header key-value pairs
            parts = list(csv.reader(io.StringIO(stripped), delimiter=delimiter))[0]
            if parts:
                key = parts[0].strip().lower()
                val = parts[1].strip() if len(parts) > 1 else ""
                meta_raw[key] = val

        meta = self._build_meta(meta_raw, errors)
        txn_lines = lines[txn_start_idx:] if txn_start_idx is not None else []
        return meta, txn_lines, errors

    def _build_meta(self, raw: dict[str, str], errors: list[dict]) -> dict:
        stmt_date = parse_date(raw.get("date", "")) or raw.get("date", "")
        opening   = parse_amount(raw.get("opening balance", ""))
        closing   = parse_amount(raw.get("closing balance", ""))
        debits    = parse_amount(raw.get("debits", ""))
        credits   = parse_amount(raw.get("credits", ""))

        num_debits = num_credits = None
        try:
            num_debits = int(raw.get("number of debits", ""))
        except ValueError:
            pass
        try:
            num_credits = int(raw.get("number of credits", ""))
        except ValueError:
            pass

        return make_statement_meta(
            account_number   = raw.get("account number", ""),
            account_nickname = raw.get("account nickname", ""),
            statement_date   = stmt_date,
            opening_balance  = opening,
            closing_balance  = closing,
            total_debits     = debits,
            total_credits    = credits,
            num_debits       = num_debits,
            num_credits      = num_credits,
        )

    def _parse_transactions(
        self, txn_lines: list[str], delimiter: str
    ) -> tuple[list[dict], list[dict]]:
        rows    = self._csv_rows(txn_lines, delimiter)
        results = []
        errors  = []

        for i, row in enumerate(rows, start=1):
            r = self._parse_row(row, i)
            if "reason" in r:
                errors.append(r)
            else:
                results.append(r)

        return results, errors

    def _parse_row(self, row: dict[str, str], row_num: int) -> dict:
        # Required fields 
        if not row.get("effective date"):
            return make_error(row=row_num, reason="Missing 'Effective Date'", raw=row, source=self.SOURCE)
        if not row.get("amount") and not row.get("debit / credit"):
            return make_error(row=row_num, reason="Missing both 'Amount' and 'Debit / Credit'", raw=row, source=self.SOURCE)

        # Date 
        date = parse_date(row["effective date"])
        if date is None:
            return make_error(
                row=row_num,
                reason=f"Unparseable date: '{row['effective date']}'",
                raw=row,
                source=self.SOURCE,
            )

        # Amount 
        # FNB uses 'Debit / Credit' as a sign indicator ('CR' = credit, '-' or blank = debit)
        # and 'Amount' as the magnitude. Amount may already carry a '-' sign.
        raw_amount   = row.get("amount", "")
        dc_indicator = row.get("debit / credit", "").strip().upper()
        service_raw  = row.get("service fee", "")

        amount = parse_amount(raw_amount)
        if amount is None:
            return make_error(
                row=row_num,
                reason=f"Unparseable amount: '{raw_amount}'",
                raw=row,
                source=self.SOURCE,
            )

        # Apply credit indicator: if 'CR' and amount is negative, flip to positive
        if dc_indicator == "CR" and amount < 0:
            amount = abs(amount)
        # If no CR indicator and amount is positive, treat as debit (make negative)
        elif dc_indicator not in ("CR", "") and amount > 0:
            amount = -amount

        # Service fee
        service_fee = parse_amount(service_raw) or 0.0

        # Balance
        balance = parse_amount(row.get("balance", ""))

        # Description / Reference
        description = row.get("description", "").strip() or "UNKNOWN"
        reference   = row.get("reference", "").strip()

        return make_transaction(
            date        = date,
            description = description,
            reference   = reference,
            amount      = amount,
            service_fee = service_fee,
            balance     = balance,
            source      = self.SOURCE,
        )
