import json
import pytest
from pathlib import Path
from ledgerza.reporter import print_summary, export_json


def make_txn(**kwargs):
    base = {
        "date": "2026-02-16", "description": "TEST TXN", "amount": -50.0,
        "category": "groceries", "source": "fnb", "reference": "",
        "service_fee": 0.0, "balance": 950.0,
    }
    return {**base, **kwargs}


class TestExportJson:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "result.json"
        txns = [make_txn()]
        export_json(txns, out)
        assert out.exists()

    def test_valid_json(self, tmp_path):
        out = tmp_path / "result.json"
        txns = [make_txn()]
        export_json(txns, out)
        data = json.loads(out.read_text())
        assert "transactions" in data
        assert "errors" in data
        assert "meta" in data

    def test_transactions_written(self, tmp_path):
        out = tmp_path / "result.json"
        txns = [make_txn(amount=-100.0), make_txn(amount=50.0)]
        export_json(txns, out)
        data = json.loads(out.read_text())
        assert len(data["transactions"]) == 2

    def test_errors_written(self, tmp_path):
        out = tmp_path / "result.json"
        errors = [{"row": 2, "reason": "Bad date", "raw": {}, "source": "fnb"}]
        export_json([], out, errors=errors)
        data = json.loads(out.read_text())
        assert len(data["errors"]) == 1
        assert data["errors"][0]["reason"] == "Bad date"

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "deep" / "result.json"
        export_json([make_txn()], out)
        assert out.exists()

    def test_meta_written(self, tmp_path):
        out = tmp_path / "result.json"
        meta = {"account_number": "12345", "opening_balance": 1000.0}
        export_json([make_txn()], out, meta=meta)
        data = json.loads(out.read_text())
        assert data["meta"]["account_number"] == "12345"


class TestPrintSummary:
    """Smoke tests — verify it runs without raising, not exact output."""

    def test_runs_with_transactions(self, capsys):
        txns = [make_txn(), make_txn(amount=100.0, category="income")]
        print_summary(txns, [], source_file="test.csv")
        out = capsys.readouterr().out
        assert "test.csv" in out

    def test_runs_with_no_transactions(self, capsys):
        print_summary([], [], source_file="empty.csv")
        out = capsys.readouterr().out
        assert "No valid transactions" in out

    def test_runs_with_errors(self, capsys):
        errors = [{"row": 2, "reason": "Bad date", "raw": {}, "source": "fnb"}]
        print_summary([], errors, source_file="test.csv", show_errors=True)
        out = capsys.readouterr().out
        assert "skipped" in out.lower() or "Bad date" in out

    def test_hide_errors(self, capsys):
        errors = [{"row": 2, "reason": "Bad date", "raw": {}, "source": "fnb"}]
        print_summary([], errors, source_file="test.csv", show_errors=False)
        out = capsys.readouterr().out
        assert "Bad date" not in out

    def test_meta_shown(self, capsys):
        meta = {"account_number": "99999", "opening_balance": 5000.0,
                "closing_balance": 4500.0, "statement_date": "2026-02-16",
                "account_nickname": "Cheque"}
        txns = [make_txn()]
        print_summary(txns, [], source_file="test.csv", meta=meta)
        out = capsys.readouterr().out
        assert "99999" in out
