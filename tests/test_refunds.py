import pandas as pd

from src.analytics import match_refunds, calculate_summary


def make_df(rows):
    df = pd.DataFrame(rows, columns=["date", "description", "category", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_refund_matched_to_single_purchase():
    df = make_df([
        ("2026-07-01", "Amazon Shopping", "Shopping", -500),
        ("2026-07-10", "Amazon Refund", "Refunds", 100),
    ])
    out = match_refunds(df)
    assert out["status"].iloc[0] == "matched"
    assert out["purchase_amount"].iloc[0] == -500


def test_refund_bigger_than_purchase_is_unmatched():
    df = make_df([
        ("2026-07-01", "Amazon Shopping", "Shopping", -50),
        ("2026-07-10", "Amazon Refund", "Refunds", 100),
    ])
    assert match_refunds(df)["status"].iloc[0] == "unmatched"


def test_two_possible_purchases_is_ambiguous_and_links_latest():
    df = make_df([
        ("2026-07-01", "Amazon Shopping", "Shopping", -500),
        ("2026-07-05", "Amazon Shopping", "Shopping", -300),
        ("2026-07-10", "Amazon Refund", "Refunds", 100),
    ])
    out = match_refunds(df)
    assert out["status"].iloc[0] == "ambiguous"
    assert out["purchase_date"].iloc[0] == pd.Timestamp("2026-07-05")


def test_purchase_after_refund_is_not_matched():
    df = make_df([
        ("2026-07-10", "Amazon Refund", "Refunds", 100),
        ("2026-07-15", "Amazon Shopping", "Shopping", -500),
    ])
    assert match_refunds(df)["status"].iloc[0] == "unmatched"


def test_different_merchant_is_not_matched():
    df = make_df([
        ("2026-07-01", "Myntra Shopping", "Shopping", -500),
        ("2026-07-10", "Amazon Refund", "Refunds", 100),
    ])
    assert match_refunds(df)["status"].iloc[0] == "unmatched"


def test_no_refunds_gives_empty_table():
    df = make_df([("2026-07-01", "Amazon Shopping", "Shopping", -500)])
    assert match_refunds(df).empty


def test_refund_reduces_expenses_and_is_not_income():
    df = make_df([
        ("2026-07-01", "Salary", "Salary", 1000),
        ("2026-07-05", "Amazon Shopping", "Shopping", -500),
        ("2026-07-10", "Amazon Refund", "Refunds", 100),
    ])
    result = calculate_summary(df)
    assert result["income"] == 1000        # the refund is NOT income
    assert result["expenses"] == 400       # 500 spent minus 100 refunded
    assert result["savings_rate"] == 60.0