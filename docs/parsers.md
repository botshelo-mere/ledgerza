# Parser Reference

## FNB (First National Bank)

**Source:** `ledgerza/parsers/fnb.py`  
**Spec:** File Specification: Statement Export — Statement Type: CSV (July 2012)  
**Identifier:** `"fnb"`

### File structure

FNB exports have two sections separated by a blank row:

**Section 1 — Statement header (key-value pairs):**

| Field              | Format     | Notes |
|--------------------|------------|-------|
| Recreated Statement | —         | Marker row — used for format detection |
| Date               | CCYYMMDD   | Statement creation date |
| Account Nickname   | text       | Account label |
| Account Number     | 11 digits  | Leading zeros included |
| Opening Balance    | numeric    | `"-"` suffix if debit position |
| Closing Balance    | numeric    | `"-"` suffix if debit position |
| Debits             | numeric    | Total debit value for period |
| Credits            | numeric    | Total credit value for period |
| Number of Debits   | integer    | Count of debit transactions |
| Number of Credits  | integer    | Count of credit transactions |

**Section 2 — Transactions (columnar CSV):**

| Column            | Format     | Notes |
|-------------------|------------|-------|
| Effective Date    | CCYYMMDD   | Date used for interface purposes |
| Description       | 42 chars   | Same as paper statement |
| Reference         | 30 chars   | Captured at transaction creation |
| Service Fee       | numeric    | Accrued fee for this transaction |
| Debit / Credit    | `CR` / `-` | Indicator: `CR` = credit, blank/`-` = debit |
| Amount            | numeric    | `"-"` prefix for debit entries |
| Balance           | numeric    | Calculated running balance |

### Detection signal

`can_parse()` checks:
1. First non-blank line contains `"Recreated Statement"`
2. Any line contains `"Effective Date"` (confirms transaction section)

### Delimiter support

Comma (`,`), tab (`\t`), semicolon (`;`), pipe (`|`) — auto-detected per file.

### Amount resolution

- `CR` in Debit/Credit column + positive amount → positive (credit)
- Blank/`-` in Debit/Credit column + negative amount → negative (debit)
- Amount already carries sign in most exports — DC indicator used to verify

---

## Capitec

**Source:** `ledgerza/parsers/capitec.py`  
**Identifier:** `"capitec"`

### Column spec

```
Nr, Account, Posting Date, Transaction Date, Description,
Original Description, Parent Category, Category,
Money In, Money Out, Fee, Balance
```

### Field mapping

| Column               | Maps to       | Notes |
|----------------------|---------------|-------|
| Posting Date         | `date`        | Primary date — falls back to Transaction Date |
| Transaction Date     | `date`        | Fallback if Posting Date missing |
| Description          | `description` | Preferred over Original Description |
| Original Description | `description` | Fallback |
| Category             | `category`    | Pre-supplied — trusted over rule engine |
| Parent Category      | `category`    | Fallback if Category missing |
| Money In             | `amount`      | Positive (credit/inflow) |
| Money Out            | `amount`      | Negative (debit/outflow) |
| Fee                  | `service_fee` | Separate fee field |
| Balance              | `balance`     | Running balance |

### Detection signal

`can_parse()` checks first non-blank line for all three:
- `"posting date"`
- `"money in"`
- `"money out"`

### Delimiter support

Comma (`,`), semicolon (`;`), tab (`\t`), pipe (`|`) — auto-detected per file.

### Category handling

Capitec exports include pre-supplied `Category` and `Parent Category` columns. These are trusted directly — the rule engine is bypassed for Capitec transactions with a valid category. This gives Capitec users their bank's own categorisation rather than ledgerza's approximation.

---

## Common parser behaviours

All parsers share these behaviours via `BaseParser`:

- **Encoding fallback**: tries `utf-8-sig` first, falls back to `latin-1`
- **Blank row filtering**: empty rows silently skipped
- **Key normalisation**: all column names lowercased and stripped before matching
- **Per-row error collection**: bad rows recorded in `ParseResult.errors`, never abort
- **File-level errors**: `FileNotFoundError`, `ValueError` (empty) → single error entry with `row=0`
