# ledgerza — Architecture

## Overview

ledgerza is built around a single design principle: **every component does one thing and returns a typed result**. Parsers produce transactions. Cleaners filter and transform them. The reporter renders them. Nothing crosses those boundaries.

---

## Module map

```
ledgerza/
├── __init__.py        Public API surface: detect(), parse_file()
├── cli.py             Argument parsing + orchestration only — no logic
├── detector.py        Format sniffing + folder scanning
├── normalizer.py      parse_date(), parse_amount(), sniff_delimiter()
├── schema.py          make_transaction(), make_error(), make_statement_meta()
├── categorizer.py     Keyword rule engine
├── cleaner.py         Pure functions: filter, dedup, transform
├── reporter.py        print_summary(), export_json()
└── parsers/
    ├── base.py        BaseParser ABC + ParseResult container
    ├── fnb.py         FNB parser (spec: July 2012)
    └── capitec.py     Capitec parser
```

---

## Data flow

```
CSV file on disk
      │
      ▼
 detector.py          sniff_delimiter() → can_parse() → pick parser
      │
      ▼
 parsers/fnb.py        read raw lines → split header/transactions → parse rows
 parsers/capitec.py    read raw lines → normalise col names → parse rows
      │
      ▼
 ParseResult           { transactions: [...], errors: [...], meta: {...} }
      │
      ├──► categorizer.py    assign/override category per transaction
      │
      ├──► cleaner.py        dedup, filter, transform (optional)
      │
      └──► reporter.py       terminal summary  +  JSON file
```

---

## Canonical transaction schema

Every parser produces this. No exceptions.

```python
{
    "date":        "2026-02-16",   # ISO 8601 — always
    "description": "PAYMENT RECEIVED",  # uppercased, stripped
    "reference":   "REF001",       # 30-char reference (may be empty)
    "amount":      1000.0,         # float — negative = debit, positive = credit
    "service_fee": 0.0,            # accrued fee (FNB spec field)
    "balance":     2010.89,        # running balance (None if not in export)
    "category":    "income",       # lowercase string
    "source":      "fnb",          # parser identifier
}
```

---

## Error schema

Per-row errors are collected without aborting the parse.

```python
{
    "row":    4,                   # 1-based row number in transaction section
    "reason": "Unparseable date: '32/13/2026'",
    "raw":    { ... },             # the raw row dict that caused the failure
    "source": "fnb",
}
```

---

## Statement metadata schema (FNB only)

Parsed from the header block above the transaction section.

```python
{
    "account_number":   "12345678901",
    "account_nickname": "My Cheque Account",
    "statement_date":   "2026-02-16",
    "opening_balance":  1010.89,
    "closing_balance":  22.39,
    "total_debits":     -988.50,
    "total_credits":    1000.04,
    "num_debits":       7,
    "num_credits":      2,
}
```

---

## Adding a new bank

1. Create `ledgerza/parsers/yourbank.py`:
   - Subclass `BaseParser`
   - Set `SOURCE = "yourbank"`
   - Implement `can_parse(path: Path) -> bool` — must not raise
   - Implement `parse(path: Path) -> ParseResult`
   - Use `self._load()`, `self._sniff()`, `self._csv_rows()` from base
   - Return `make_transaction(...)` for successes, `make_error(...)` for failures

2. Register in `detector.py` — add to `_PARSERS` list

3. Add fixture CSV to `tests/fixtures/`

4. Write tests in `tests/test_parsers.py`

Nothing else changes.

---

## Delimiter handling

`sniff_delimiter()` in `normalizer.py`:
1. Tries `csv.Sniffer` on the first 20 lines of the file
2. Falls back to counting candidates (`,` `;` `\t` `|`) in the first content line
3. Defaults to `,` if nothing conclusive

Parsers never hardcode delimiters. `_sniff()` is called on every file.

---

## Error handling philosophy

- **File-level errors** (missing, empty, unreadable): returned as a single error entry in `ParseResult.errors`, with `row=0`
- **Row-level errors** (bad date, missing amount, unparseable value): collected per row, never abort the parse
- **No silent failures**: every skipped row has a reason recorded
- **Callers decide severity**: the CLI reports errors; the library returns them — consumers choose what to do
