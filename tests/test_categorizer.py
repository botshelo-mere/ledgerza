import pytest
from ledgerza.categorizer import categorize


class TestCategorize:
    @pytest.mark.parametrize("desc,expected", [
        ("PAYMENT RECEIVED",    "income"),
        ("SALARY DEPOSIT",      "income"),
        ("INTEREST RECEIVED",   "interest"),
        ("INTEREST EARNED",     "interest"),
        ("MONTHLY ADMIN FEE",   "fees"),
        ("SERVICE FEE",         "fees"),
        ("IMMEDIATE PAYMENT FEE", "fees"),
        ("CARD PURCHASE",       "groceries"),
        ("PNP STORES",          "groceries"),
        ("WOOLWORTHS FOOD",     "groceries"),
        ("BOLT PAYMENT",        "transport"),
        ("UBER TRIP",           "transport"),
        ("PETROL ENGEN",        "transport"),
        ("DSTV SUBSCRIPTION",   "subscriptions"),
        ("NETFLIX MONTHLY",     "subscriptions"),
        ("PREPAID PURCHASE",    "cellphone"),
        ("MTN AIRTIME",         "cellphone"),
        ("ATM WITHDRAWAL",      "cash"),
        ("TILL CASH WITHDRAWAL","cash"),
        ("TRANSFER TO SAVINGS", "transfers"),
        ("RANDOM DESCRIPTION",  "other"),
    ])
    def test_rule_matching(self, desc, expected):
        assert categorize(desc) == expected

    def test_existing_category_trusted(self):
        """Pre-supplied category (e.g. from Capitec) overrides rule engine."""
        assert categorize("SALARY DEPOSIT", existing_category="salary") == "salary"

    def test_empty_existing_category_falls_through(self):
        assert categorize("SALARY DEPOSIT", existing_category="") == "income"

    def test_uncategorized_falls_through(self):
        assert categorize("SALARY DEPOSIT", existing_category="uncategorized") == "income"

    def test_case_insensitive(self):
        assert categorize("bolt payment") == "transport"
        assert categorize("BOLT PAYMENT") == "transport"

    def test_unknown_returns_other(self):
        assert categorize("XYZZY FOOBAR QWERTY") == "other"
