import pandas as pd
from src.data_cleaning import parse_dates, clean_transactions


def make_raw(rows):
    return pd.DataFrame(rows, columns=["date", "description", "amount"])


def test_iso_dates_detected():
    parsed, fmt = parse_dates(pd.Series(["2026-07-01", "2026-07-15"]))
    assert fmt == "%Y-%m-%d"


def test_day_first_dates_are_not_swapped():
    parsed, fmt = parse_dates(pd.Series(["05/07/2026", "15/07/2026"]))
    assert fmt == "%d/%m/%Y"
    assert parsed.iloc[0] == pd.Timestamp(2026, 7, 5)   # July 5th, not May 7th


def test_bad_date_is_rejected_and_counted():
    raw = make_raw([("2026-07-01", "A", 100), ("not a date", "B", 50)])
    clean, rejected, summary = clean_transactions(raw)
    assert summary["valid"] == 1
    assert summary["rejected"] == 1
    assert len(rejected) == 1


def test_duplicates_are_removed_and_counted():
    raw = make_raw([("2026-07-01", "Swiggy", -450), ("2026-07-01", "Swiggy", -450)])
    clean, rejected, summary = clean_transactions(raw)
    assert len(clean) == 1
    assert summary["duplicates_removed"] == 1