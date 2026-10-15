import pandas as pd

REQUIRED_COLUMNS = ["date", "description", "amount"]

# Other names people might use -> our standard name
COLUMN_ALIASES = {
    "transaction_date": "date",
    "merchant": "description",
    "transaction_amount": "amount",
}


def load_transactions(file):
    """Read a CSV and return a DataFrame with date, description, amount."""
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        raise ValueError("The file is empty.")

    # Tidy column names: remove spaces, make lowercase
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns=COLUMN_ALIASES)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    if df.empty:
        raise ValueError("The file has headers but no transactions.")

    return df[REQUIRED_COLUMNS].copy()