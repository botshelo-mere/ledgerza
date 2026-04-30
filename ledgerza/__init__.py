"""ledgerZA - South African bank statement CSV parser and reporter."""

from .main import parse_and_summarize, summarize

__version__ = "0.1.0"
__all__ = ["parse_and_summarize", "summarize"]
