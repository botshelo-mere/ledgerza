# LedgerZA - Usage Guide and Setup

## Folder structure

```
ledgerza/
├── ledgerza/
│   ├── __init__.py          public API
│   ├── cli.py               CLI — argparse entry point
│   ├── detector.py          format sniffing + folder scanning
│   ├── normalizer.py        parse_date, parse_amount, sniff_delimiter
│   ├── schema.py            make_transaction, make_error, make_statement_meta
│   ├── categorizer.py       keyword rule engine
│   ├── cleaner.py           dedup, filters, transformations
│   ├── reporter.py          terminal summary + JSON export
│   └── parsers/
│       ├── base.py          BaseParser ABC + ParseResult
│       ├── fnb.py           FNB — spec-accurate (July 2012 spec)
│       └── capitec.py       Capitec — Money In/Out column spec
├── tests/
│   ├── fixtures/
│   │   ├── fnb_statement.csv
│   │   ├── fnb_statement_tab.csv
│   │   ├── capitec_statement.csv
│   │   └── capitec_semicolon.csv
│   ├── test_normalizer.py
│   ├── test_parsers.py
│   ├── test_categorizer.py
│   ├── test_cleaner.py
│   └── test_reporter.py
├── README.md
├── ROADMAP.md
├── LICENSE.md
├── .gitignore
└── pyproject.toml
```

## Setup with uv
`uv` is a fast Python package manager - replaces pip + venv in one tool.

1. Install `uv` (if not already) or see [official installation guides](https://docs.astral.sh/uv/getting-started/installaton)
``` bash
pip install uv

# verify installation
uv --version
```

2. Clone and enter the project
``` bash
git clone https://github.com/botshelo-mere/ledgerza.git
cd ledgerza
```

3. Create virtual environment + install 
``` bash
uv sync     # creates .venv/ + installs and activates ledgerza 
```


## CLI Usage

Basic - auto-detect bank, print summary, export json.

``` bash
uv run ledgerza -f statement.csv
```

``` bash
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
JSON exported → output\statement.json
```


```bash
# Single file
ledgerza statement.csv

# Folder — auto-detect all CSVs
ledgerza exports/

# Folder — recursive
ledgerza exports/ --recursive

# Specify output path
ledgerza statement.csv --output results/feb.json

# Summary only — no JSON written
ledgerza statement.csv --no-export

# Suppress errors in terminal output
ledgerza statement.csv --hide-errors
```

### Filters

```bash
# Date range
ledgerza statement.csv --from 2026-01-01 --to 2026-01-31

# Amount range (negative = debits)
ledgerza statement.csv --min-amount -500 --max-amount 0

# Description keyword
ledgerza statement.csv --keyword woolworths

# Category
ledgerza statement.csv --category groceries
```

### Cleaning

```bash
# Remove duplicates (date + description + amount fingerprint)
ledgerza statement.csv --dedup

# Merge + dedup across files
ledgerza jan.csv feb.csv --merge --dedup
```
---