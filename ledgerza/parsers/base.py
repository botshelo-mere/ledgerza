from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..normalizer import read_raw_lines, sniff_delimiter, parse_csv_lines
from ..schema import make_error


class ParseResult:
    """Container for a completed parse operation."""

    __slots__ = ("transactions", "errors", "meta", "source_file")

    def __init__(
        self,
        transactions: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        meta: dict[str, Any] | None = None,
        source_file: str = "",
    ) -> None:
        self.transactions = transactions
        self.errors       = errors
        self.meta         = meta or {}
        self.source_file  = source_file

    def ok(self) -> bool:
        return len(self.transactions) > 0

    def __repr__(self) -> str:
        return (
            f"ParseResult(transactions={len(self.transactions)}, "
            f"errors={len(self.errors)}, source='{self.source_file}')"
        )


class BaseParser(ABC):
    """
    Bank parsers inherit from this.

    Subclasses implement:
        SOURCE         — str class attribute: parser identifier
        can_parse()    — sniff whether this parser claims a given file
        parse()        — parse the file, return ParseResult

    Helpers provided here:
        _load()        — read raw lines + sniff delimiter
        _csv_rows()    — parse lines into list[dict]
    """

    SOURCE: str = "unknown"

    @classmethod
    @abstractmethod
    def can_parse(cls, path: Path) -> bool:
        """
        Inspect the file and return True if this parser claims it.
        Must not raise — return False on any read failure.
        """
        ...

    @abstractmethod
    def parse(self, path: Path) -> ParseResult:
        """
        Parse the file. Collect errors per-row; never raise on bad data.
        Returns a ParseResult.
        """
        ...

    # Shared helpers 

    def _load(self, path: Path) -> tuple[list[str], str]:
        """
        Reads raw lines from file with encoding fallback.
        Raises FileNotFoundError or ValueError (empty) — callers convert to errors.
        """
        return read_raw_lines(str(path))

    def _sniff(self, lines: list[str]) -> str:
        sample = "".join(lines[:20])
        return sniff_delimiter(sample)

    def _csv_rows(self, lines: list[str], delimiter: str) -> list[dict[str, str]]:
        return parse_csv_lines(lines, delimiter)

    def _file_error(self, path: Path, reason: str) -> ParseResult:
        return ParseResult(
            transactions=[],
            errors=[make_error(row=0, reason=reason, source=self.SOURCE)],
            source_file=str(path),
        )
