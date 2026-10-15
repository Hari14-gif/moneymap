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