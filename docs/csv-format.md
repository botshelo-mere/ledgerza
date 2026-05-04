# CSV Format Guide

## What ledgerZA expects

`ledgerZA` auto-detects the bank format and delimiter. You do not need to specify either. Simply point it at the file your bank exported.

---

## Supported formats

### FNB — Online Banking export

FNB's CSV export has two sections. The structure below is from the official FNB File Specification (July 2012).

**Header block (key-value rows):**
```
Recreated Statement,,,,,,
Date,20260216,,,,,
Account Nickname,My Cheque Account,,,,,
Account Number,12345678901,,,,,
Opening Balance,1010.89,,,,,
Closing Balance,22.39,,,,,
Debits,-988.50,,,,,
Credits,1000.04,,,,,
Number of Debits,7,,,,,
Number of Credits,2,,,,,
```

**Blank row separator**

**Transaction rows:**
```
Effective Date,Description,Reference,Service Fee,Debit / Credit,Amount,Balance
20260216,PAYMENT RECEIVED    ,REF001,,CR,1000.00,2010.89
20260216,BOLT PAYMENT        ,REF002,,-50.00,-50.00,1960.89
20260217,CARD PURCHASE       ,REF006,,-917.50,-917.50,1031.89
```

Key points:
- Dates are `CCYYMMDD` (no separators): `20260216`
- Credits use `CR` in the Debit/Credit column
- Debits have a `-` prefix on Amount; Debit/Credit column may be blank
- Service Fee is a separate column — may be empty for most rows
- Delimiter: comma by default, but tab is also handled

---

### Capitec — Transaction export

Capitec exports a flat CSV with a single header row. No preamble.

```
Nr,Account,Posting Date,Transaction Date,Description,Original Description,Parent Category,Category,Money In,Money Out,Fee,Balance
1,1234567890,2026-02-03,2026-02-03,PnP Stores,PNP STORES,Food & Drink,Groceries,,850.00,,4150.00
2,1234567890,2026-02-05,2026-02-05,Salary Deposit,EMPLOYER PAYROLL,Income,Salary,12000.00,,,16150.00
```

Key points:
- `Money In` = credit (positive) — column populated, `Money Out` empty
- `Money Out` = debit (negative) — column populated, `Money In` empty
- `Fee` is a separate column (maps to `service_fee`)
- `Category` and `Parent Category` are pre-supplied by Capitec — ledgerza trusts them
- Dates are `YYYY-MM-DD`
- Delimiter: comma or semicolon both supported

---

## Delimiter handling

ledgerza auto-detects the delimiter. The following are all supported:

| Delimiter | Symbol | Common in |
|-----------|--------|-----------|
| Comma     | `,`    | Most bank exports |
| Semicolon | `;`    | European locale exports |
| Tab       | `\t`   | Some FNB variants |
| Pipe      | `\|`   | Rare, but handled |

---

## Amount formats

All of the following are parsed correctly:

| Input        | Parsed as | Notes |
|--------------|-----------|-------|
| `R-50.00`    | `-50.0`   | R prefix + minus |
| `R1000.00`   | `1000.0`  | R prefix, no sign |
| `R1000,00`   | `1000.0`  | Comma decimal (quoted in CSV) |
| `R-917,50`   | `-917.5`  | Comma decimal + minus |
| `(R200.00)`  | `-200.0`  | Accounting notation |
| `R1.000,50`  | `1000.5`  | European thousands + decimal |
| `R1,000.50`  | `1000.5`  | US thousands + decimal |
| `R1 000.00`  | `1000.0`  | Space thousands |
| `ZAR-50.00`  | `-50.0`   | ZAR prefix |
| `-50.00`     | `-50.0`   | No prefix |
| `1000.00`    | `1000.0`  | Plain numeric |

---

## The comma-decimal problem

If your bank uses a comma as the decimal separator and a comma as the CSV delimiter, amounts like `R1000,00` become two tokens: `R1000` and `00`. This is **ambiguous CSV** — ledgerza cannot fix it yet .

**The fix:** your bank should quote amount fields: `"R1000,00"`. Python's CSV parser handles this correctly. If your export does not quote amount fields, switch your export settings to use a period decimal separator.

**NOTE** A feature that solves this problem will be implemented in future versions of `LedgerZA`
---

## Date formats

All of the following are recognised:

| Format       | Example         |
|--------------|-----------------|
| `CCYYMMDD`   | `20260216`      |
| `YYYY-MM-DD` | `2026-02-16`    |
| `DD/MM/YYYY` | `16/02/2026`    |
| `MM/DD/YYYY` | `02/16/2026`    |
| `DD-MM-YYYY` | `16-02-2026`    |
| `YYYY/MM/DD` | `2026/02/16`    |
| `DD Mon YYYY`| `16 Feb 2026`   |
| `DD Month YYYY`| `16 February 2026` |

All output dates are normalised to `YYYY-MM-DD` (ISO 8601).
