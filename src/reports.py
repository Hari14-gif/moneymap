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

def category_report_csv(df, start, end, currency="INR"):
    """Spending by category (with each share of total) plus a header explaining the report."""
    spend = df[(df["amount"] < 0) & (df["category"] != "Internal Transfer")]

    table = spend.groupby("category")["amount"].agg(total="sum", payments="count")
    table["total"] = table["total"].abs()
    total = table["total"].sum()
    table["share_pct"] = (table["total"] / total * 100).round(1) if total > 0 else 0
    table = table.sort_values("total", ascending=False).reset_index()

    header = (
        "Category spending report\n"
        f"Date range,{start} to {end}\n"
        f"Currency,{currency}\n"
        "Note,Internal transfers are excluded\n"
        "Note,Refunds are not netted in this table (they reduce total expenses in the summary report)\n"
        "Note,Categories are suggestions from keyword rules\n"
        "\n"
    )
    return (header + table.to_csv(index=False)).encode("utf-8")

def insights_report_csv(insights, old_month, new_month, start, end, currency="INR"):
    """The insights shown on screen, with a header that explains what they are."""
    header = (
        "Insights report\n"
        f"Date range,{start} to {end}\n"
        f"Compared months,{old_month} vs {new_month}\n"
        f"Currency,{currency}\n"
        "Note,Insights are rule-based observations from your recorded transactions\n"
        "Note,They show what changed, not why it changed\n"
        "Note,Transaction-based estimate, not a verified bank balance\n"
        "\n"
    )
    columns = ["title", "observation", "evidence", "caveat"]
    table = pd.DataFrame(insights, columns=columns)
    return (header + table.to_csv(index=False)).encode("utf-8")