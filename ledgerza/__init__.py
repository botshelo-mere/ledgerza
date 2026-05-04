"""LedgerZA — South African bank CSV parser"""

from .detector import detect, detect_folder, UnknownFormatError
from .schema import make_transaction
from .parsers.base import ParseResult

def parse_file(path: str) -> "ParseResult":
    from pathlib import Path
    from .categorizer import categorize
    parser = detect(Path(path))
    result = parser.parse(Path(path))
    for txn in result.transactions:
        txn["category"] = categorize(txn["description"], txn.get("category"))
    return result

__all__ = ["detect", "detect_folder", "parse_file", "make_transaction",
           "ParseResult", "UnknownFormatError"]
__version__ = "0.1.0"
