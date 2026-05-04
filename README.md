## ledgerZA v0.1.0

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.md)
[![Development Status](https://img.shields.io/badge/status-alpha-red.svg)](https://github.com/botshelo-mere/ledgerza)

## Overview

Real bank CSVs are inconsistent. Different column names, date formats, sign conventions, preamble rows, and encoding.

Introducing `ledgerZA` - a Python toolkit for transforming South African bank statement CSVs into structured, categorized financial data and insights.

## What it does

`ledgerZA` abstracts all of the inconsistencies — you feed it a CSV, it gives you clean, structured transaction data.

``` bash
$ ledgerza --file capitec_feb.csv

============================================================
Transactions after cleaning: 62 (filtered 0)

════════════════════════════════════════════════════
  LedgerZA Report  -  statement.csv
  Bank: CAPITEC
════════════════════════════════════════════════════
  Transactions :     62
  Total in     : R  26569.74
  Total out    : R -23837.80
  Net          : R   2731.94
  Date range   : 2026-03-01  →  2026-04-21

  Category                Txns         Total
  ----------------------  -----  ------------
  groceries                 10  R  -7583.45
  uncategorised              1  R  -7450.00
  cash withdrawal            2  R  -2800.00
  digital payments           3  R  -1100.00
  restaurants                2  R  -1026.00
  takeaways                  2  R   -309.60
  children & dependants      2  R   -300.00
  alcohol                    2  R   -240.00
  clothing & shoes           1  R   -231.00
  public transport           4  R   -148.00
  personal care              1  R    -99.18
  cellphone                  3  R    -18.00
  interest                   1  R      2.09
  transfer                  17  R   1785.08
  cash deposit               2  R   3000.00
  other income               9  R  19250.00


  ⚠  2 row(s) skipped or failed:
    [capitec] Row 14: Both 'Money In' and 'Money Out' are empty
    [capitec] Row 15: Both 'Money In' and 'Money Out' are empty

════════════════════════════════════════════════════

```

> This alpha release introduces the core foundation for parsing, normalizing, and summarizing transaction data from real-world bank exports.

---

### Features

- Parse South African bank CSV statements from the terminal
- Normalize transaction fields — dates (6 format variants), amounts (Rand notation, comma decimals, thousands separators), descriptions
- Rule-based transaction categorization — data-driven, no hardcoded if/elif chains
- Financial summaries: income, expenses, net, per-category breakdowns
- JSON export of canonical transaction data
- Per-row error collection — bad rows never abort a full file parse
- Zero runtime dependencies — stdlib only

---

### Supported Banks


| Bank    | Parser accuracy | Delimiter support | Notes |
|---------|----------------|-------------------|-------|
| FNB     | Spec-accurate  | comma, tab, pipe, semicolon | Parses full header block (account number, opening/closing balance, debit/credit totals) |
| Capitec | Spec-accurate  | comma, semicolon, tab, pipe | Reads pre-supplied categories; Money In / Money Out columns |

> Support may vary depending on CSV format variations between account types and export settings.

---

## Installation

```bash
git clone https://github.com/botshelo-mere/ledgerza.git
cd ledgerza
```

Using `pip`
```bash
pip install -e ".[dev]"
```

Using `uv` (recommended).  
Install `uv` (if not already) or see [official installation guides](https://docs.astral.sh/uv/getting-started/installation/) 
```bash
pip install uv
uv sync
```

## Usage

```bash
# print summary
ledgerza --file statement.csv

# Specify file path
ledgerza -f finances/capitec_feb.json
```

For full user guide - see [usage.md](docs/usage.md) for details. 

---

## JSON output schema

```json
{
  "meta": {
    "account_number": "12345678901",
    "account_nickname": "My Cheque Account",
    "statement_date": "2026-02-16",
    "opening_balance": 1010.89,
    "closing_balance": 22.39,
    "total_debits": -988.50,
    "total_credits": 1000.04
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
  "errors": []
}
```

---

## License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

---

## Author 

**BOTSHELO MERE**  
Github: [botshelo-mere](https://github.com/botshelo-mere/)
