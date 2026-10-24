import pandas as pd
from src.analytics import pct_change, category_changes
from src.insights import rising_category_insights, new_spending_insights


def make_df(rows):
    df = pd.DataFrame(rows, columns=["date", "category", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_pct_change_basic_cases():
    assert pct_change(1000, 1250) == 25.0
    assert pct_change(1000, 800) == -20.0


def test_pct_change_zero_baseline_is_none():
    assert pct_change(0, 500) is None


def test_category_changes_values():
    df = make_df([
        ("2026-07-10", "Food Delivery", -1000),
        ("2026-08-10", "Food Delivery", -1250),
    ])
    changes = category_changes(df, "2026-07", "2026-08")
    assert changes.loc["Food Delivery", "change_pct"] == 25.0


def test_category_changes_new_spending_has_no_percentage():
    df = make_df([("2026-08-05", "Travel", -4800)])
    changes = category_changes(df, "2026-07", "2026-08")
    assert pd.isna(changes.loc["Travel", "change_pct"])


def test_rising_insight_needs_both_thresholds():
    df = make_df([
        ("2026-07-10", "Food Delivery", -1000),   # +25% but only +250 rupees
        ("2026-08-10", "Food Delivery", -1250),
        ("2026-07-12", "Shopping", -2000),        # +50% and +1000 rupees
        ("2026-08-12", "Shopping", -3000),
    ])
    found = rising_category_insights(df, "2026-07", "2026-08")
    assert len(found) == 1
    assert found[0]["title"] == "Shopping spending increased"


def test_new_spending_insight_respects_minimum():
    df = make_df([
        ("2026-08-05", "Groceries", -500),
        ("2026-09-05", "Groceries", -500),
        ("2026-09-10", "Travel", -4800),          # new and large
        ("2026-09-12", "Healthcare", -900),       # new but below 1000
    ])
    found = new_spending_insights(df, "2026-08", "2026-09")
    assert len(found) == 1
    assert found[0]["title"] == "New spending in Travel"