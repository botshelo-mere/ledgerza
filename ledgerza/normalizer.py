from __future__ import annotations
import csv
import io
from datetime import datetime

#  Date formats 
_DATE_FORMATS = (
    "%Y%m%d",      # 20260216 
    "%Y-%m-%d",    # 2026-02-16
    "%d/%m/%Y",    # 16/02/2026
    "%m/%d/%Y",    # 02/16/2026
    "%d-%m-%Y",    # 16-02-2026
    "%Y/%m/%d",    # 2026/02/16
    "%d %b %Y",    # 16 Feb 2026
    "%d %B %Y",    # 16 February 2026
)


def parse_date(raw: str) -> str | None:
    """
    Parse any recognised date string → ISO 8601 'YYYY-MM-DD'.
    Returns None on any failure.
    """
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


#  Amount parsing 
def parse_amount(raw: str) -> float | None:
    """ 
    Parse a monetary string into a signed float.
    Returns None on any parse failure.
    """
    if not raw or not raw.strip():
        return None

    s = raw.strip()

    # Bare '-' is a FNB debit/credit indicator, not an amount
    if s == "-":
        return None

    negative = False

    # Accounting notation: (R200.00) or (200.00)
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    # Strip currency prefix
    for prefix in ("ZAR", "R"):
        if s.upper().startswith(prefix):
            s = s[len(prefix):].strip()
            break

    # Leading minus after prefix strip
    if s.startswith("-"):
        negative = True
        s = s[1:]

    # Thousands / decimal normalisation
    comma_idx = s.rfind(",")
    dot_idx   = s.rfind(".")

    if comma_idx != -1 and dot_idx != -1:
        if comma_idx > dot_idx:          # European: 1.000,50
            s = s.replace(".", "").replace(",", ".")
        else:                             # US: 1,000.50
            s = s.replace(",", "")
    elif comma_idx != -1:
        after = s[comma_idx + 1:]
        if len(after) == 2 and after.isdigit():
            s = s.replace(",", ".")       # comma is decimal
        else:
            s = s.replace(",", "")        # comma is thousands
    # else: dot only — leave as-is

    s = s.replace(" ", "")               # strip space-thousands

    try:
        value = float(s)
        return -value if negative else value
    except ValueError:
        return None


#  Delimiter sniffing 

_CANDIDATE_DELIMITERS = (",", ";", "\t", "|")


def sniff_delimiter(sample: str) -> str:
    """Detect the delimiter used in a CSV sample string"""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_CANDIDATE_DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        pass

    # Manual fallback: count occurrences in first content line
    for line in sample.splitlines():
        if line.strip():
            counts = {d: line.count(d) for d in _CANDIDATE_DELIMITERS}
            best = max(counts, key=lambda d: counts[d])
            if counts[best] > 0:
                return best
            break

    return ","


def read_raw_lines(path_str: str, encodings: tuple[str, ...] = ("utf-8-sig", "latin-1")) -> tuple[list[str], str]:
    """
    Read a file trying each encoding in order.
    Returns (lines, encoding_used).
    Raises FileNotFoundError, ValueError (empty), UnicodeDecodeError (exhausted).
    """
    import os
    if not os.path.exists(path_str):
        raise FileNotFoundError(f"File not found: {path_str}")
    if os.path.getsize(path_str) == 0:
        raise ValueError(f"File is empty: {path_str}")

    last_exc: Exception = RuntimeError("no encodings tried")
    for enc in encodings:
        try:
            with open(path_str, encoding=enc, newline="") as fh:
                lines = fh.readlines()
            return lines, enc
        except UnicodeDecodeError as exc:
            last_exc = exc
            continue
    raise last_exc


def parse_csv_lines(lines: list[str], delimiter: str) -> list[dict[str, str]]:
    """
    Parse a list of raw line strings as CSV with the given delimiter.
    Returns list of row dicts with lowercased, stripped keys.
    Empty rows are skipped.
    """
    content = "".join(lines)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows: list[dict[str, str]] = []
    for row in reader:
        cleaned = {
            (k.strip().lower() if k else ""): (v.strip() if v else "")
            for k, v in row.items()
            if k is not None
        }
        if any(cleaned.values()):
            rows.append(cleaned)
    return rows
