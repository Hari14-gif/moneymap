import pandas as pd
from src.analytics import monthly_summary, is_incomplete_last_month, top_merchants
from src.recurring_payments import find_recurring


def make_df(rows):
    df = pd.DataFrame(rows, columns=["date", "description", "category", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_monthly_summary_savings_rate_and_change():
    df = make_df([
        ("2026-07-01", "Salary", "Salary", 1000),
        ("2026-07-05", "Shop", "Shopping", -500),    # July: 50% saved
        ("2026-08-01", "Salary", "Salary", 1000),
        ("2026-08-05", "Shop", "Shopping", -800),    # August: 20% saved
    ])
    out = monthly_summary(df)
    assert out["savings_rate"].tolist() == [50.0, 20.0]
    assert out["savings_rate_change_pts"].iloc[1] == -30.0


def test_monthly_summary_empty_does_not_crash():
    empty = make_df([])
    assert monthly_summary(empty).empty


def test_incomplete_month_flagged_when_data_stops_early():
    df = make_df([("2026-09-10", "A", "Shopping", -100)])
    assert is_incomplete_last_month(df) is True


def test_complete_month_not_flagged():
    df = make_df([("2026-09-28", "A", "Shopping", -100)])
    assert is_incomplete_last_month(df) is False


def test_top_merchants_order_and_share():
    df = make_df([
        ("2026-07-01", "Big Shop", "Shopping", -300),
        ("2026-07-02", "Small Shop", "Shopping", -100),
        ("2026-07-03", "Big Shop", "Shopping", -100),
    ])
    top = top_merchants(df, n=1)
    assert top.index[0] == "Big Shop"
    assert top["total"].iloc[0] == 400
    assert top["share_pct"].iloc[0] == 80.0     # share of ALL spending, not just top 1


def test_recurring_found_for_same_amount_every_month():
    df = make_df([
        ("2026-07-03", "Netflix", "Subscriptions", -649),
        ("2026-08-03", "Netflix", "Subscriptions", -649),
        ("2026-09-03", "Netflix", "Subscriptions", -649),
    ])
    found = find_recurring(df)
    assert "Netflix" in found.index
    assert found.loc["Netflix", "confidence"] == "High"


def test_recurring_needs_three_payments():
    df = make_df([
        ("2026-07-03", "Netflix", "Subscriptions", -649),
        ("2026-08-03", "Netflix", "Subscriptions", -649),
    ])
    assert find_recurring(df).empty


def test_irregular_habit_is_not_recurring():
    df = make_df([
        ("2026-07-01", "Swiggy", "Food Delivery", -400),
        ("2026-07-04", "Swiggy", "Food Delivery", -650),
        ("2026-07-20", "Swiggy", "Food Delivery", -300),
    ])
    assert find_recurring(df).empty