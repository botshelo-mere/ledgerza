from __future__ import annotations
from pathlib import Path

from .parsers.base import BaseParser
from .parsers.fnb import FNBParser
from .parsers.capitec import CapitecParser


# Registry of banks - order matters
_PARSERS: list[type[BaseParser]] = [FNBParser, CapitecParser,]
CSV_EXTENSIONS = {".csv", ".tsv"}

class UnknownFormatError(Exception):
    """Raised when no registered parser can claim a file."""
    pass


# Single file 
def detect(path: Path) -> BaseParser:
    """
    Detect the bank format for a single CSV file
    Raises:
        FileNotFoundError:  path does not exist.
        IsADirectoryError:  path is a directory (use detect_folder instead).
        UnknownFormatError: no parser recognises the format.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(
            f"'{path}' is a directory. Use detect_folder() to scan all CSVs in it."
        )

    for parser_cls in _PARSERS:
        if parser_cls.can_parse(path):
            return parser_cls()

    supported = [p.SOURCE for p in _PARSERS]
    raise UnknownFormatError(
        f"Could not detect bank format for: '{path.name}'\n"
        f"Supported formats: {supported}"
    )


#  Folder scanning 

class FolderScanResult:
    """Result of scanning a folder for parseable CSV files."""

    __slots__ = ("matched", "unmatched", "skipped")

    def __init__(self) -> None:
        self.matched:   list[tuple[Path, BaseParser]] = []   # (path, parser)
        self.unmatched: list[Path]                    = []   # no parser found
        self.skipped:   list[Path]                    = []   # non-CSV files

    def __repr__(self) -> str:
        return (
            f"FolderScanResult(matched={len(self.matched)}, "
            f"unmatched={len(self.unmatched)}, skipped={len(self.skipped)})"
        )


def detect_folder(folder: Path, recursive: bool = False) -> FolderScanResult:
    """
    Scan a folder for parseable CSV files.
    """
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    result   = FolderScanResult()
    pattern  = "**/*" if recursive else "*"
    all_files = sorted(folder.glob(pattern))

    for file_path in all_files:
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in CSV_EXTENSIONS:
            result.skipped.append(file_path)
            continue
        try:
            parser = detect(file_path)
            result.matched.append((file_path, parser))
        except UnknownFormatError:
            result.unmatched.append(file_path)

    return result
