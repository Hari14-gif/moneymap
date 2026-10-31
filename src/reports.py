import pandas as pd


def transactions_csv(df):
    """The filtered transactions as CSV bytes (original descriptions kept as they are)."""
    cols = ["date", "description", "category", "amount"]
    out = df[cols].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False).encode("utf-8")


def summary_csv(result, start, end, currency="INR"):
    """Key metrics plus the date range, currency and assumptions, as CSV bytes."""
    rate = result["savings_rate"]
    rows = [
        ("Date range", f"{start} to {end}"),
        ("Currency", currency),
        ("Income", result["income"]),
        ("Expenses", result["expenses"]),
        ("Net cash flow", result["net_cash_flow"]),
        ("Savings rate (%)", "n/a" if rate is None else round(rate, 1)),
        ("Assumption", "Internal transfers are excluded from income and expenses"),
        ("Assumption", "Refunds reduce expenses; they are not counted as income"),
        ("Assumption", "Credit card payments are counted as expenses (card purchases are not in the data)"),
        ("Limitation", "Transaction-based estimate, not a verified bank balance"),
    ]
    return pd.DataFrame(rows, columns=["item", "value"]).to_csv(index=False).encode("utf-8")