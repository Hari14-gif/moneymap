import pandas as pd
def calculate_summary(df, count_card_payments=True):
    """Income, expenses, net cash flow and savings rate."""
    transfers = df["category"] == "Internal Transfer"
    refunds = df["category"] == "Refunds"
    card = df["category"] == "Credit Card Payment"

    # Rows we leave out of income/expense
    skip = transfers | refunds
    if not count_card_payments:
        skip = skip | card
    money = df[~skip]

    income = money.loc[money["amount"] > 0, "amount"].sum()
    expenses = -money.loc[money["amount"] < 0, "amount"].sum()  # shown as positive

    # Refunds reduce expenses
    expenses = expenses - df.loc[refunds, "amount"].sum()

    net = income - expenses

    # Safe: no dividing by zero
    savings_rate = net / income * 100 if income > 0 else None

    return {
        "income": income,
        "expenses": expenses,
        "net_cash_flow": net,
        "savings_rate": savings_rate,
    }
    
    
def pct_change(old, new):
    """Percent change. Returns None when old is 0 (no sensible percentage)."""
    if old == 0:
        return None
    return (new - old) / old * 100


def category_changes(df, old_month, new_month):
    """Spending per category in two months (YYYY-MM), plus percent change."""
    spend = df[(df["amount"] < 0) & (df["category"] != "Internal Transfer")].copy()
    spend["month"] = spend["date"].dt.to_period("M").astype(str)

    table = spend.pivot_table(
        index="category", columns="month", values="amount", aggfunc="sum"
    ).abs()
    table = table.reindex(columns=[old_month, new_month], fill_value=0).fillna(0)

    table["change_pct"] = [
        pct_change(old, new) for old, new in zip(table[old_month], table[new_month])
    ]
    return table

def category_shares(df, top_n=3):
    """Each category's share of total spending, plus the top-N combined share."""
    spend = df[(df["amount"] < 0) & (df["category"] != "Internal Transfer")]
    by_cat = spend.groupby("category")["amount"].sum().abs().sort_values(ascending=False)

    total = by_cat.sum()
    if total == 0:
        return by_cat * 0, None   # no spending, so no shares

    share = by_cat / total * 100
    return share, share.head(top_n).sum()

def monthly_summary(df):
    """Income, expenses, net cash flow and savings rate for each month."""
    columns = ["month", "income", "expenses", "net_cash_flow", "savings_rate"]
    rows = []
    for month, group in df.groupby(df["date"].dt.to_period("M").astype(str)):
        r = calculate_summary(group)
        rows.append({
            "month": month,
            "income": r["income"],
            "expenses": r["expenses"],
            "net_cash_flow": r["net_cash_flow"],
            "savings_rate": r["savings_rate"],
        })

    if not rows:
        return pd.DataFrame(columns=columns + ["savings_rate_change_pts"])

    out = pd.DataFrame(rows, columns=columns)
    out["savings_rate_change_pts"] = out["savings_rate"].diff()
    return out

def is_incomplete_last_month(df, tolerance_days=5):
    """True if the data stops well before the end of its last month."""
    if df.empty:
        return False
    last_date = df["date"].max()
    month_end = last_date + pd.offsets.MonthEnd(0)
    return (month_end - last_date).days > tolerance_days

def top_merchants(df, n=5):
    """Top-N merchants by total spending, with each one's share of all spending."""
    spend = df[(df["amount"] < 0) & (df["category"] != "Internal Transfer")]
    if spend.empty:
        return pd.DataFrame(columns=["total", "payments", "share_pct"])

    top = spend.groupby("description")["amount"].agg(total="sum", payments="count")
    top["total"] = top["total"].abs()
    top["share_pct"] = top["total"] / top["total"].sum() * 100   # share of ALL spending
    return top.sort_values("total", ascending=False).head(n)