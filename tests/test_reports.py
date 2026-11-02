import pandas as pd
from src.analytics import filter_transactions
from src.reports import (
    transactions_csv,
    summary_csv,
    category_report_csv,
    insights_report_csv,
)


def make_df(rows):
    df = pd.DataFrame(rows, columns=["date", "description", "category", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


SAMPLE = [
    ("2026-07-01", "Salary", "Salary", 1000),
    ("2026-07-05", "Swiggy", "Food Delivery", -400),
    ("2026-08-05", "Big Shop", "Shopping", -600),
]


def test_filter_by_dates():
    out = filter_transactions(make_df(SAMPLE), "2026-08-01", "2026-08-31")
    assert len(out) == 1
    assert out["description"].iloc[0] == "Big Shop"


def test_filter_by_category():
    out = filter_transactions(make_df(SAMPLE), categories=["Food Delivery"])
    assert len(out) == 1


def test_empty_category_list_means_all():
    out = filter_transactions(make_df(SAMPLE), categories=[])
    assert len(out) == 3


def test_transactions_csv_keeps_original_descriptions():
    text = transactions_csv(make_df(SAMPLE)).decode()
    assert "Big Shop" in text
    assert text.splitlines()[0] == "date,description,category,amount"


def test_summary_report_states_range_currency_and_assumptions():
    result = {"income": 1000, "expenses": 1000, "net_cash_flow": 0, "savings_rate": 0.0}
    text = summary_csv(result, "2026-07-01", "2026-09-30").decode()
    assert "2026-07-01 to 2026-09-30" in text
    assert "INR" in text
    assert "Assumption" in text


def test_summary_report_shows_na_when_no_income():
    result = {"income": 0, "expenses": 500, "net_cash_flow": -500, "savings_rate": None}
    text = summary_csv(result, "2026-07-01", "2026-07-31").decode()
    assert "n/a" in text


def test_category_report_shares_add_up():
    text = category_report_csv(make_df(SAMPLE), "2026-07-01", "2026-08-31").decode()
    assert "Shopping,600,1,60.0" in text
    assert "Food Delivery,400,1,40.0" in text


def test_category_report_with_no_spending_does_not_crash():
    only_income = make_df([("2026-07-01", "Salary", "Salary", 1000)])
    text = category_report_csv(only_income, "2026-07-01", "2026-07-31").decode()
    assert "Category spending report" in text


def test_insights_report_with_no_insights_still_has_header():
    text = insights_report_csv([], "2026-07", "2026-08", "2026-07-01", "2026-08-31").decode()
    assert "Insights report" in text
    assert "title,observation,evidence,caveat" in text