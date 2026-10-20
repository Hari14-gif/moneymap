
import pandas as pd

REQUIRED_COLUMNS = ["date", "description", "amount"]

# Other names banks use -> our standard name
COLUMN_ALIASES = {
    "transaction_date": "date",
    "txn date": "date",
    "merchant": "description",
    "narration": "description",
    "particulars": "description",
    "details": "description",
    "transaction_amount": "amount",
    "withdrawal": "debit",
    "withdrawals": "debit",
    "deposit": "credit",
    "deposits": "credit",
}


def _numbers_or_zero(df, name):
    """Blank cells count as 0. Garbage like 'abc' stays NaN so cleaning can reject it."""
    if name not in df.columns:
        return 0
    numeric = pd.to_numeric(df[name], errors="coerce")
    return numeric.where(~df[name].isna(), 0)


def load_transactions(file):
    """Read a CSV and return a DataFrame with date, description, amount."""
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        raise ValueError("The file is empty.")

    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns=COLUMN_ALIASES)

    # Two-column layout: amount = money in - money out
    if "amount" not in df.columns and ("debit" in df.columns or "credit" in df.columns):
        df["amount"] = _numbers_or_zero(df, "credit") - _numbers_or_zero(df, "debit")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    if df.empty:
        raise ValueError("The file has headers but no transactions.")

    return df[REQUIRED_COLUMNS].copy()