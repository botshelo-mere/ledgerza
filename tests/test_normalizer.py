import pytest
from ledgerza.normalizer import parse_date, parse_amount, sniff_delimiter


#  parse_date 

class TestParseDate:
    @pytest.mark.parametrize("raw,expected", [
        ("20260216",     "2026-02-16"),  # FNB CCYYMMDD
        ("2026-02-16",   "2026-02-16"),  # ISO 8601
        ("16/02/2026",   "2026-02-16"),  # SA slash
        ("02/16/2026",   "2026-02-16"),  # US slash
        ("16-02-2026",   "2026-02-16"),  # dash DMY
        ("2026/02/16",   "2026-02-16"),  # slash YMD
        ("16 Feb 2026",  "2026-02-16"),  # verbose short
        ("16 February 2026", "2026-02-16"),  # verbose long
    ])
    def test_valid_formats(self, raw, expected):
        assert parse_date(raw) == expected

    @pytest.mark.parametrize("raw", [
        "", "   ", "not-a-date", "2026-13-01", "32/01/2026", None.__class__.__name__,
    ])
    def test_invalid_returns_none(self, raw):
        assert parse_date(raw) is None

    def test_whitespace_stripped(self):
        assert parse_date("  2026-02-16  ") == "2026-02-16"


#  parse_amount 

class TestParseAmount:
    @pytest.mark.parametrize("raw,expected", [
        ("R-50.00",      -50.0),
        ("R1000.00",    1000.0),
        ("R1000,00",    1000.0),    # comma decimal
        ("R-917,50",    -917.5),    # comma decimal negative
        ("(R200.00)",   -200.0),    # accounting notation
        ("R1.000,50",   1000.5),    # EU thousands
        ("R1,000.50",   1000.5),    # US thousands
        ("R1 000.00",   1000.0),    # space thousands
        ("R0.00",          0.0),
        ("R0.04",          0.04),
        ("ZAR-50.00",    -50.0),    # ZAR prefix
        ("-50.00",        -50.0),   # no prefix
        ("1000.00",      1000.0),   # plain numeric
        ("0.50",            0.5),
        ("12000.00",    12000.0),
    ])
    def test_valid_amounts(self, raw, expected):
        result = parse_amount(raw)
        assert result == pytest.approx(expected, rel=1e-6)

    @pytest.mark.parametrize("raw", [
        "", "   ", "garbage", "R", "ZAR", "-", "R-",
    ])
    def test_invalid_returns_none(self, raw):
        assert parse_amount(raw) is None

    def test_bare_dash_is_none(self):
        """FNB uses bare '-' as a debit indicator, not an amount."""
        assert parse_amount("-") is None

    def test_accounting_without_currency(self):
        assert parse_amount("(50.00)") == pytest.approx(-50.0)


#  sniff_delimiter 

class TestSniffDelimiter:
    def test_comma(self):
        assert sniff_delimiter("a,b,c\n1,2,3\n") == ","

    def test_semicolon(self):
        assert sniff_delimiter("a;b;c\n1;2;3\n") == ";"

    def test_tab(self):
        assert sniff_delimiter("a\tb\tc\n1\t2\t3\n") == "\t"

    def test_pipe(self):
        assert sniff_delimiter("a|b|c\n1|2|3\n") == "|"

    def test_empty_defaults_to_comma(self):
        result = sniff_delimiter("")
        assert result in (",", ";", "\t", "|")  # any reasonable default
