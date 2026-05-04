"""
Integration tests for FNB and Capitec parsers.
Tests assert on behaviour (schema, values, error handling), not implementation.
"""

import pytest
from pathlib import Path
from ledgerza.parsers.fnb import FNBParser
from ledgerza.parsers.capitec import CapitecParser
from ledgerza.detector import detect, UnknownFormatError

FIXTURES = Path(__file__).parent / "fixtures"
FNB_CSV      = FIXTURES / "fnb_statement.csv"
FNB_TAB      = FIXTURES / "fnb_statement_tab.csv"
CAP_CSV      = FIXTURES / "capitec_statement.csv"
CAP_SEMI     = FIXTURES / "capitec_semicolon.csv"

REQUIRED_KEYS = {"date", "description", "reference", "amount",
                 "service_fee", "balance", "category", "source"}


#  Detector 

class TestDetector:
    def test_detects_fnb_comma(self):
        assert detect(FNB_CSV).SOURCE == "fnb"

    def test_detects_fnb_tab(self):
        assert detect(FNB_TAB).SOURCE == "fnb"

    def test_detects_capitec_comma(self):
        assert detect(CAP_CSV).SOURCE == "capitec"

    def test_detects_capitec_semicolon(self):
        assert detect(CAP_SEMI).SOURCE == "capitec"

    def test_unknown_format_raises(self, tmp_path):
        f = tmp_path / "weird.csv"
        f.write_text("foo,bar\n1,2\n")
        with pytest.raises(UnknownFormatError):
            detect(f)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            detect(tmp_path / "ghost.csv")

    def test_directory_raises(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            detect(tmp_path)


#  FNB parser — comma 

class TestFNBParserComma:
    @pytest.fixture
    def result(self):
        return FNBParser().parse(FNB_CSV)

    def test_no_errors(self, result):
        assert result.errors == [], f"Unexpected errors: {result.errors}"

    def test_transaction_count(self, result):
        assert len(result.transactions) == 9

    def test_schema_complete(self, result):
        for txn in result.transactions:
            assert REQUIRED_KEYS.issubset(txn.keys()), f"Missing keys: {txn}"

    def test_source_is_fnb(self, result):
        assert all(t["source"] == "fnb" for t in result.transactions)

    def test_dates_are_iso(self, result):
        import re
        iso = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for txn in result.transactions:
            assert iso.match(txn["date"]), f"Bad date: {txn['date']}"

    def test_amounts_are_float(self, result):
        for txn in result.transactions:
            assert isinstance(txn["amount"], float)

    def test_descriptions_are_upper(self, result):
        for txn in result.transactions:
            assert txn["description"] == txn["description"].upper()

    def test_credit_is_positive(self, result):
        payment = next(t for t in result.transactions if "PAYMENT RECEIVED" in t["description"])
        assert payment["amount"] > 0

    def test_debit_is_negative(self, result):
        bolt = next(t for t in result.transactions if "BOLT" in t["description"])
        assert bolt["amount"] < 0

    def test_interest_is_positive(self, result):
        interest = next(t for t in result.transactions if "INTEREST" in t["description"])
        assert interest["amount"] > 0

    def test_service_fee_parsed(self, result):
        # Some rows have a service fee
        fees = [t for t in result.transactions if t["service_fee"] != 0.0]
        assert len(fees) >= 1

    def test_balance_parsed(self, result):
        for txn in result.transactions:
            assert txn["balance"] is not None

    def test_meta_account_number(self, result):
        assert result.meta.get("account_number") == "12345678901"

    def test_meta_opening_balance(self, result):
        assert result.meta.get("opening_balance") == pytest.approx(1010.89)

    def test_meta_statement_date(self, result):
        assert result.meta.get("statement_date") == "2026-02-16"


#  FNB parser — tab delimiter 

class TestFNBParserTab:
    @pytest.fixture
    def result(self):
        return FNBParser().parse(FNB_TAB)

    def test_no_errors(self, result):
        assert result.errors == []

    def test_transaction_count(self, result):
        assert len(result.transactions) == 4

    def test_source_is_fnb(self, result):
        assert all(t["source"] == "fnb" for t in result.transactions)

    def test_credit_positive(self, result):
        income = next(t for t in result.transactions if "PAYMENT RECEIVED" in t["description"])
        assert income["amount"] > 0


#  Capitec parser — comma 

class TestCapitecParserComma:
    @pytest.fixture
    def result(self):
        return CapitecParser().parse(CAP_CSV)

    def test_transaction_count(self, result):
        assert len(result.transactions) == 8

    def test_schema_complete(self, result):
        for txn in result.transactions:
            assert REQUIRED_KEYS.issubset(txn.keys())

    def test_source_is_capitec(self, result):
        assert all(t["source"] == "capitec" for t in result.transactions)

    def test_money_in_is_positive(self, result):
        salary = next(t for t in result.transactions if "SALARY" in t["description"].upper())
        assert salary["amount"] > 0

    def test_money_out_is_negative(self, result):
        pnp = next(t for t in result.transactions if "PNP" in t["description"].upper()
                   or "STORES" in t["description"].upper())
        assert pnp["amount"] < 0

    def test_category_from_export(self, result):
        salary = next(t for t in result.transactions if "SALARY" in t["description"].upper())
        assert salary["category"] == "salary"

    def test_fee_field_parsed(self, result):
        fee_row = next(t for t in result.transactions if "SERVICE FEE" in t["description"].upper())
        assert fee_row["service_fee"] == pytest.approx(0.50)

    def test_balance_parsed(self, result):
        for txn in result.transactions:
            assert txn["balance"] is not None

    def test_dates_iso(self, result):
        import re
        iso = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for txn in result.transactions:
            assert iso.match(txn["date"])


#  Capitec parser — semicolon 

class TestCapitecParserSemicolon:
    @pytest.fixture
    def result(self):
        return CapitecParser().parse(CAP_SEMI)

    def test_transaction_count(self, result):
        assert len(result.transactions) == 3

    def test_no_errors(self, result):
        assert result.errors == []

    def test_money_out_negative(self, result):
        pnp = next(t for t in result.transactions if "PNP" in t["description"].upper()
                   or "STORES" in t["description"].upper())
        assert pnp["amount"] < 0


#  Edge cases 

class TestEdgeCases:
    def test_empty_file_not_claimed(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("")
        assert FNBParser.can_parse(f) is False
        assert CapitecParser.can_parse(f) is False

    def test_empty_file_parse_returns_error(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("")
        for Parser in (FNBParser, CapitecParser):
            r = Parser().parse(f)
            assert r.transactions == []
            assert len(r.errors) >= 1

    '''def test_fnb_missing_amount_row(self, tmp_path):
        f = tmp_path / "bad_amount.csv"
        content = (
            "Recreated Statement,,,,,,\n"
            "Date,20260216,,,,\n"
            "Account Number,12345,,,,\n"
            "\n"
            "Effective Date,Description,Reference,Service Fee,Debit / Credit,Amount,Balance\n"
            "20260216,TEST TXN,REF001,,CR,,1000.00\n"
        )
        f.write_text(content)
        r = FNBParser().parse(f)
        assert r.transactions == []
        assert len(r.errors) == 1
        assert "Amount" in r.errors[0]["reason"]'''
        
    def test_fnb_bad_date_row(self, tmp_path):
        f = tmp_path / "bad_date.csv"
        content = (
            "Recreated Statement,,,,,,\n"
            "Date,20260216,,,,\n"
            "Account Number,12345,,,,\n"
            "\n"
            "Effective Date,Description,Reference,Service Fee,Debit / Credit,Amount,Balance\n"
            "not-a-date,TEST TXN,REF001,,CR,100.00,1000.00\n"
        )
        f.write_text(content)
        r = FNBParser().parse(f)
        assert r.transactions == []
        assert len(r.errors) == 1
        assert "date" in r.errors[0]["reason"].lower()

    def test_mixed_good_and_bad_rows(self, tmp_path):
        f = tmp_path / "mixed.csv"
        content = (
            "Recreated Statement,,,,,,\n"
            "Date,20260216,,,,\n"
            "Account Number,12345,,,,\n"
            "\n"
            "Effective Date,Description,Reference,Service Fee,Debit / Credit,Amount,Balance\n"
            "20260216,GOOD ONE,REF001,,CR,100.00,1000.00\n"
            "bad-date,BAD ONE,REF002,,CR,50.00,950.00\n"
            "20260217,GOOD TWO,REF003,,-50.00,-50.00,900.00\n"
        )
        f.write_text(content)
        r = FNBParser().parse(f)
        assert len(r.transactions) == 2
        assert len(r.errors) == 1

    def test_capitec_both_money_fields_empty(self, tmp_path):
        f = tmp_path / "cap_empty.csv"
        f.write_text(
            "Nr,Account,Posting Date,Transaction Date,Description,"
            "Original Description,Parent Category,Category,Money In,Money Out,Fee,Balance\n"
            "1,12345,2026-02-01,2026-02-01,Test Txn,TEST,Income,Salary,,,0.00,5000.00\n"
        )
        r = CapitecParser().parse(f)
        assert r.transactions == []
        assert len(r.errors) == 1
        assert "Money In" in r.errors[0]["reason"] or "Money Out" in r.errors[0]["reason"]

    def test_folder_with_single_file(self, tmp_path):
        from ledgerza.detector import detect_folder
        import shutil
        shutil.copy(FNB_CSV, tmp_path / "fnb.csv")
        scan = detect_folder(tmp_path)
        assert len(scan.matched) == 1
        assert scan.matched[0][1].SOURCE == "fnb"

    def test_folder_not_found(self, tmp_path):
        from ledgerza.detector import detect_folder
        with pytest.raises(FileNotFoundError):
            detect_folder(tmp_path / "nonexistent")

    def test_folder_mixed_files(self, tmp_path):
        from ledgerza.detector import detect_folder
        import shutil
        shutil.copy(FNB_CSV, tmp_path / "fnb.csv")
        shutil.copy(CAP_CSV, tmp_path / "capitec.csv")
        (tmp_path / "notes.txt").write_text("ignore me")
        scan = detect_folder(tmp_path)
        assert len(scan.matched) == 2
        assert len(scan.skipped) == 1
