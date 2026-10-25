import pandas as pd
from src.analytics import calculate_summary


def make_df(rows):
    return pd.DataFrame(rows, columns=["amount", "category"])


def test_basic_income_and_expenses():
    df = make_df([(1000, "Salary"), (-400, "Groceries")])
    result = calculate_summary(df)
    assert result["income"] == 1000
    assert result["expenses"] == 400
    assert result["net_cash_flow"] == 600
    assert result["savings_rate"] == 60


def test_internal_transfer_is_ignored():
    df = make_df([(1000, "Salary"), (-500, "Internal Transfer")])
    result = calculate_summary(df)
    assert result["expenses"] == 0


def test_refund_reduces_expenses():
    df = make_df([(1000, "Salary"), (-400, "Shopping"), (100, "Refunds")])
    result = calculate_summary(df)
    assert result["expenses"] == 300

def test_zero_income_gives_no_savings_rate():
    df = make_df([(-400, "Groceries")])
    result = calculate_summary(df)
    assert result["savings_rate"] is None