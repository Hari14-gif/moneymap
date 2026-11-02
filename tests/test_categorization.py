import pandas as pd

from src.categorization import categorize, add_categories, apply_overrides
from src.database import connect, save_override, load_overrides


def test_refund_rule_beats_shopping_rule():
    assert categorize("Amazon Refund - Returned Item") == "Refunds"


def test_unknown_description_is_uncategorized():
    assert categorize("Mystery Shop 123") == "Uncategorized"


def test_matching_ignores_capital_letters():
    assert categorize("SWIGGY ORDER") == "Food Delivery"


def test_add_categories_keeps_original_descriptions():
    df = pd.DataFrame({"description": ["Swiggy Order"], "amount": [-450]})
    out = add_categories(df)
    assert out["description"].iloc[0] == "Swiggy Order"
    assert out["category"].iloc[0] == "Food Delivery"


def test_override_wins_over_automatic_category():
    df = add_categories(pd.DataFrame({"description": ["Udemy Course"], "amount": [-499]}))
    out = apply_overrides(df, {"Udemy Course": "Entertainment"})
    assert out["category"].iloc[0] == "Entertainment"
    assert df["category"].iloc[0] == "Education"      # the original table is untouched


def test_empty_overrides_change_nothing():
    df = add_categories(pd.DataFrame({"description": ["Udemy Course"], "amount": [-499]}))
    out = apply_overrides(df, {})
    assert out["category"].iloc[0] == "Education"


def test_override_for_unknown_description_is_ignored():
    df = add_categories(pd.DataFrame({"description": ["Udemy Course"], "amount": [-499]}))
    out = apply_overrides(df, {"Not In Data": "Shopping"})
    assert out["category"].iloc[0] == "Education"


def test_saving_override_twice_keeps_only_the_latest():
    conn = connect(":memory:")
    save_override(conn, "Udemy Course", "Entertainment")
    save_override(conn, "Udemy Course", "Shopping")
    assert load_overrides(conn) == {"Udemy Course": "Shopping"}
    count = conn.execute("SELECT COUNT(*) FROM category_overrides").fetchone()[0]
    assert count == 1


def test_overrides_survive_closing_and_reopening(tmp_path):
    path = str(tmp_path / "test.db")
    conn = connect(path)
    save_override(conn, "Udemy Course", "Entertainment")
    conn.close()

    reopened = connect(path)
    assert load_overrides(reopened) == {"Udemy Course": "Entertainment"}
    reopened.close()