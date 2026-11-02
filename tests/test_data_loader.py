import io

import pandas as pd
import pytest

from src.data_loader import load_transactions


def load(text):
    """Helper: feed a string (or bytes) to the loader like an uploaded file."""
    data = text.encode() if isinstance(text, str) else text
    return load_transactions(io.BytesIO(data))


def test_empty_file_gives_clear_error():
    with pytest.raises(ValueError) as e:
        load(b"")
    assert "empty" in str(e.value).lower()


def test_headers_only_gives_clear_error():
    with pytest.raises(ValueError) as e:
        load("date,description,amount\n")
    assert "no transactions" in str(e.value)


def test_wrong_columns_lists_what_is_missing():
    with pytest.raises(ValueError) as e:
        load("x,y\n1,2\n")
    assert "Missing columns" in str(e.value)


def test_ragged_rows_give_friendly_error():
    with pytest.raises(ValueError) as e:
        load("date,description,amount\n2026-07-01,A,100\n2026-07-02,B,200,extra,more\n")
    assert "could not be read as a CSV" in str(e.value)


def test_binary_file_gives_friendly_error():
    with pytest.raises(ValueError) as e:
        load(b"\x89PNG\r\n\x1a\n\x00\x00")
    assert "could not be read as a CSV" in str(e.value)


def test_error_does_not_echo_long_file_content():
    secret_header = "x" * 100
    with pytest.raises(ValueError) as e:
        load(f"{secret_header},y\n1,2\n")
    assert "x" * 50 not in str(e.value)


def test_bank_layout_becomes_signed_amount():
    df = load("Date,Narration,Withdrawal,Deposit\n2026-07-01,Swiggy,450,\n2026-07-02,Salary,,45000\n")
    assert list(df.columns) == ["date", "description", "amount"]
    assert df["amount"].tolist() == [-450, 45000]


def test_column_names_are_cleaned():
    df = load(" Date ,NARRATION,Amount\n2026-07-01,Swiggy,-450\n")
    assert list(df.columns) == ["date", "description", "amount"]


def test_garbage_amount_stays_empty_for_cleaning_to_reject():
    df = load("Date,Narration,Withdrawal,Deposit\n2026-07-01,Swiggy,abc,\n")
    assert pd.isna(df["amount"].iloc[0])