# CLI Reference

## Synopsis

```
ledgerza --file [PATH ...] [options]
```

`PATH` can be:
- A single CSV file
- Multiple CSV files (use `--merge` to combine them)
- A single folder (scans all `.csv` / `.tsv` files inside it)

---

## Arguments

### Positional

| Argument | Description |
|----------|-------------|
| `PATH`   | One or more CSV files, or a single directory |

---

## Options

### Output

| Flag | Default | Description |
|------|---------|-------------|
| `--output FILE` / `-o FILE` | `output/<input>.json` | JSON output path |
| `--no-export` | off | Print summary only — skip JSON export |
| `--no-summary` | off | Export JSON only — skip terminal output |
| `--hide-errors` | off | Suppress per-row error detail in summary |

### Folder mode

| Flag | Default | Description |
|------|---------|-------------|
| `--recursive` / `-r` | off | Recurse into sub-directories when a folder is given |

### Cleaning

| Flag | Default | Description |
|------|---------|-------------|
| `--dedup` | off | Remove duplicate transactions (fingerprint: date + description + amount) |

### Filters

| Flag | Example | Description |
|------|---------|-------------|
| `--from YYYY-MM-DD` | `--from 2026-01-01` | Include transactions on or after this date |
| `--to YYYY-MM-DD` | `--to 2026-01-31` | Include transactions on or before this date |
| `--min-amount AMOUNT` | `--min-amount -500` | Include transactions with amount >= AMOUNT |
| `--max-amount AMOUNT` | `--max-amount 0` | Include transactions with amount <= AMOUNT |
| `--keyword TEXT` | `--keyword woolworths` | Include only transactions whose description contains TEXT |
| `--category CAT` | `--category groceries` | Include only transactions matching this category |

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Success — at least one transaction parsed |
| `1`  | Error — file not found, unknown format, or all rows failed |

---

## Examples

### Basic parse

```bash
ledgerza -f statement.csv
```

Detects bank format, prints terminal summary, exports `output/statement.json`.

---

### Folder scan

```bash
ledgerza exports/
```

Scans `exports/` for all `.csv` and `.tsv` files, prints a summary per file.

```bash
ledgerza exports/ --recursive
```

Same, but recurses into sub-directories.

---

### Date range filter

```bash
ledgerza -f statement.csv --from 2026-01-01 --to 2026-01-31
```

Only transactions within January 2026 appear in summary and export.

---

### Show only debits over R500

```bash
ledgerza -f statement.csv --max-amount -500
```

Amounts are signed: negative = debit. `--max-amount -500` keeps transactions where `amount <= -500`, i.e. debits of R500 or more.

---

### Keyword search

```bash
ledgerza --file statement.csv --keyword woolworths
```

Case-insensitive. Matches any description containing "woolworths".

---

### Category filter

```bash
ledgerza -f statement.csv --category groceries
```

Outputs only transactions in the `groceries` category.

---

### Export only — no terminal output

```bash
ledgerza -f statement.csv --no-summary --output results/feb.json
```

---

### Summary only — no file written

```bash
ledgerza --file statement.csv --no-export
```

---

### Suppress error detail

```bash
ledgerza --file statement.csv --hide-errors
```

Summary still shows error count, but individual row errors are not printed.

---

## JSON output format

```json
{
  "meta": {
    "account_number": "12345678901",
    "account_nickname": "My Cheque Account",
    "statement_date": "2026-02-16",
    "opening_balance": 1010.89,
    "closing_balance": 22.39,
    "total_debits": -988.50,
    "total_credits": 1000.04,
    "num_debits": 7,
    "num_credits": 2
  },
  "transactions": [
    {
      "date": "2026-02-16",
      "description": "PAYMENT RECEIVED",
      "reference": "REF001",
      "amount": 1000.0,
      "service_fee": 0.0,
      "balance": 2010.89,
      "category": "income",
      "source": "fnb"
    }
  ],
  "errors": [
    {
      "row": 5,
      "reason": "Unparseable date: '32/13/2026'",
      "raw": { "effective date": "32/13/2026", "description": "...", "amount": "..." },
      "source": "fnb"
    }
  ]
}
```

`meta` is populated for FNB statements (which include a header block). For Capitec, `meta` will be an empty object `{}`.
