import pandas as pd

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]


def parse_dates(series):
    """Try each known format and keep the one that parses the most rows."""
    best, best_fmt, best_count = None, "unknown", -1
    for fmt in DATE_FORMATS:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        count = parsed.notna().sum()
        if count > best_count:      # ties keep the earlier format
            best, best_fmt, best_count = parsed, fmt, count
    if best_count == 0:
        best_fmt = "unknown"
    return best, best_fmt


def clean_transactions(raw):
    """Returns (clean, rejected, summary). The raw data is never changed."""
    df = raw.copy()

    # Job 1: fix types. Bad values become NaT / NaN instead of crashing.
    df["description"] = df["description"].astype("string").str.strip()
    df["date"], date_format = parse_dates(df["date"])      # edit 2
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # Job 2: set aside rows with a bad date or amount
    bad_rows = df["date"].isna() | df["amount"].isna()
    rejected = raw[bad_rows].copy()
    clean = df[~bad_rows].copy()

    # Job 3: fill missing descriptions
    no_desc = clean["description"].isna() | (clean["description"] == "")
    clean.loc[no_desc, "description"] = "(no description)"

    # Job 4: remove exact duplicates
    is_dup = clean.duplicated(subset=["date", "description", "amount"])
    clean = clean[~is_dup]

    clean = clean.sort_values("date").reset_index(drop=True)

    summary = {
        "imported": len(raw),
        "valid": len(clean),
        "rejected": len(rejected),
        "duplicates_removed": int(is_dup.sum()),
        "missing_description": int(no_desc.sum()),
        "date_format": date_format,                         # edit 3
    }
    return clean, rejected, summary