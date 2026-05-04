from __future__ import annotations

RULES: list[tuple[tuple[str, ...], str]] = [
    # Income
    (("salary", "payroll", "pay ", "payment received", "employer"), "income"),
    (("interest received", "interest earned"), "interest"),
    (("refund", "reversal", "cashback"), "refund"),

    # Banking fees
    (("service fee", "admin fee", "monthly fee", "account fee",
      "transaction fee", "immediate payment fee", "prepaid fee",
      "till cash fee", "cash fee", "bank charge"), "fees"),

    # Food
    (("pnp", "pick n pay", "woolworths", "checkers", "spar",
      "shoprite", "food lover", "whole foods", "groceries",
      "card purchase", "restaurant", "kfc", "mcdonalds",
      "steers", "nandos", "ocean basket"), "groceries"),

    # Transport
    (("bolt", "uber", "lyft", "taxi", "petrol", "fuel", "shell",
      "engen", "caltex", "bp ", "parking", "e-toll", "etoll",
      "traffic fine"), "transport"),

    # Subscriptions & Entertainment
    (("dstv", "netflix", "spotify", "apple", "google play",
      "amazon", "showmax", "youtube", "disney"), "subscriptions"),

    # Utilities
    (("eskom", "city power", "water", "electricity", "rates",
      "municipality", "cape town utility"), "utilities"),

    # Telecoms
    (("prepaid", "airtime", "data bundle", "vodacom", "mtn",
      "telkom", "cellc", "rain "), "cellphone"),

    # Cash
    (("atm", "cash withdrawal", "till cash"), "cash"),

    # Transfers
    (("transfer", "imm payment", "immediate payment", "eft ",
      "send money"), "transfers"),

    # Insurance & Medical
    (("insurance", "assurance", "discovery", "momentum",
      "old mutual", "sanlam"), "insurance"),
    (("pharmacy", "clicks", "dis-chem", "hospital", "medical",
      "doctor", "dentist"), "medical"),

    # Education
    (("school", "university", "tuition", "varsity", "course",
      "udemy", "coursera"), "education"),
]


def categorize(description: str, existing_category: str | None = None) -> str:
    """
    Return a category string for the transaction.
    If `existing_category` is already set and meaningful, it is trusted as-is
    
    Falls back to 'other' if no rule matches.
    """
    if existing_category and existing_category.strip().lower() not in ("", "uncategorized"):
        return existing_category.strip().lower()

    desc_lower = description.lower()
    for keywords, category in RULES:
        if any(kw in desc_lower for kw in keywords):
            return category

    return "other"
