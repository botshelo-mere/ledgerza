import pytest
from ledgerza.cleaner import (
    deduplicate, fill_missing, drop_if_missing,
    filter_by_date, filter_by_amount, filter_by_description,
    filter_by_category, add_month_field, add_abs_amount_field,
    split_debits_credits, merge,
)


def make_txn(**kwargs):
    base = {
        "date": "2026-02-16", "description": "TEST", "amount": -50.0,
        "category": "other", "source": "fnb", "reference": "",
        "service_fee": 0.0, "balance": None,
    }
    return {**base, **kwargs}


class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        txns = [make_txn(), make_txn(), make_txn(amount=-10.0)]
        result, removed = deduplicate(txns)
        assert len(result) == 2
        assert removed == 1

    def test_no_duplicates(self):
        txns = [make_txn(amount=-10.0), make_txn(amount=-20.0)]
        result, removed = deduplicate(txns)
        assert len(result) == 2
        assert removed == 0

    def test_first_occurrence_wins(self):
        a = make_txn(description="FIRST")
        b = make_txn(description="FIRST")
        result, _ = deduplicate([a, b])
        assert result[0] is a


class TestFillMissing:
    def test_fills_none(self):
        txns = [make_txn(balance=None), make_txn(balance=100.0)]
        result = fill_missing(txns, "balance", 0.0)
        assert result[0]["balance"] == 0.0
        assert result[1]["balance"] == 100.0

    def test_fills_empty_string(self):
        txns = [make_txn(reference="")]
        result = fill_missing(txns, "reference", "N/A")
        assert result[0]["reference"] == "N/A"

    def test_does_not_mutate_original(self):
        t = make_txn(balance=None)
        fill_missing([t], "balance", 0.0)
        assert t["balance"] is None


class TestDropIfMissing:
    def test_drops_none(self):
        txns = [make_txn(balance=None), make_txn(balance=100.0)]
        kept, dropped = drop_if_missing(txns, "balance")
        assert len(kept) == 1
        assert dropped == 1

    def test_drops_empty_string(self):
        txns = [make_txn(reference=""), make_txn(reference="REF1")]
        kept, dropped = drop_if_missing(txns, "reference")
        assert len(kept) == 1


class TestFilterByDate:
    def test_from_filter(self):
        txns = [make_txn(date="2026-01-01"), make_txn(date="2026-02-01")]
        assert len(filter_by_date(txns, from_date="2026-02-01")) == 1

    def test_to_filter(self):
        txns = [make_txn(date="2026-01-01"), make_txn(date="2026-02-01")]
        assert len(filter_by_date(txns, to_date="2026-01-31")) == 1

    def test_range_filter(self):
        txns = [
            make_txn(date="2026-01-01"),
            make_txn(date="2026-01-15"),
            make_txn(date="2026-02-01"),
        ]
        result = filter_by_date(txns, from_date="2026-01-10", to_date="2026-01-31")
        assert len(result) == 1

    def test_no_filter(self):
        txns = [make_txn(), make_txn()]
        assert len(filter_by_date(txns)) == 2


class TestFilterByAmount:
    def test_min_amount(self):
        txns = [make_txn(amount=-100.0), make_txn(amount=-10.0), make_txn(amount=50.0)]
        result = filter_by_amount(txns, min_amount=-50.0)
        assert len(result) == 2

    def test_max_amount(self):
        txns = [make_txn(amount=-100.0), make_txn(amount=-10.0), make_txn(amount=50.0)]
        result = filter_by_amount(txns, max_amount=0.0)
        assert len(result) == 2


class TestFilterByDescription:
    def test_keyword_match(self):
        txns = [make_txn(description="WOOLWORTHS"), make_txn(description="BOLT")]
        assert len(filter_by_description(txns, "WOOL")) == 1

    def test_case_insensitive(self):
        txns = [make_txn(description="WOOLWORTHS")]
        assert len(filter_by_description(txns, "wool")) == 1

    def test_no_match(self):
        txns = [make_txn(description="BOLT")]
        assert len(filter_by_description(txns, "WOOL")) == 0


class TestFilterByCategory:
    def test_matches(self):
        txns = [make_txn(category="groceries"), make_txn(category="transport")]
        assert len(filter_by_category(txns, "groceries")) == 1

    def test_case_insensitive(self):
        txns = [make_txn(category="Groceries")]
        assert len(filter_by_category(txns, "groceries")) == 1


class TestTransformations:
    def test_add_month_field(self):
        txns = [make_txn(date="2026-02-16")]
        result = add_month_field(txns)
        assert result[0]["month"] == "2026-02"

    def test_add_abs_amount(self):
        txns = [make_txn(amount=-917.50)]
        result = add_abs_amount_field(txns)
        assert result[0]["abs_amount"] == pytest.approx(917.50)

    def test_split_debits_credits(self):
        txns = [make_txn(amount=-50.0), make_txn(amount=100.0), make_txn(amount=-10.0)]
        debits, credits = split_debits_credits(txns)
        assert len(debits) == 2
        assert len(credits) == 1


class TestMerge:
    def test_basic_merge(self):
        a = [make_txn(date="2026-01-01", amount=-10.0)]
        b = [make_txn(date="2026-02-01", amount=-20.0)]
        result, removed = merge(a, b, dedup=False)
        assert len(result) == 2
        assert removed == 0

    def test_merge_with_dedup(self):
        a = [make_txn(amount=-10.0)]
        b = [make_txn(amount=-10.0)]   # exact duplicate
        result, removed = merge(a, b, dedup=True)
        assert len(result) == 1
        assert removed == 1

    def test_merge_sorts_by_date(self):
        a = [make_txn(date="2026-03-01", amount=-30.0)]
        b = [make_txn(date="2026-01-01", amount=-10.0)]
        result, _ = merge(a, b, dedup=False, sort_by_date=True)
        assert result[0]["date"] == "2026-01-01"
        assert result[1]["date"] == "2026-03-01"
