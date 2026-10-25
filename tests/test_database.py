import sqlite3

import pandas as pd
import pytest

from src.database import connect, import_transactions


def make_df(rows):
    df = pd.DataFrame(rows, columns=["date", "description", "category", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


SAMPLE = [
    ("2026-07-01", "Salary", "Salary", 1000),
    ("2026-07-05", "Swiggy", "Food Delivery", -400),
    ("2026-08-01", "Mystery Shop", "Uncategorized", -50),
]


def test_import_inserts_rows():
    conn = connect(":memory:")
    result = import_transactions(conn, make_df(SAMPLE), "a.csv")
    assert result["inserted"] == 3
    assert result["skipped"] == 0
    assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 3


def test_importing_same_file_twice_adds_nothing():
    conn = connect(":memory:")
    df = make_df(SAMPLE)
    import_transactions(conn, df, "a.csv")
    second = import_transactions(conn, df, "a.csv")
    assert second["inserted"] == 0
    assert second["skipped"] == 3
    assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 3


def test_database_rejects_duplicate_row():
    conn = connect(":memory:")
    import_transactions(conn, make_df(SAMPLE), "a.csv")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO transactions (batch_id, date, description, amount) "
            "VALUES (1, '2026-07-01', 'Salary', 1000)"
        )


def test_foreign_key_must_point_to_real_batch():
    conn = connect(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO transactions (batch_id, date, description, amount) "
            "VALUES (999, '2026-07-01', 'X', -1)"
        )


def test_monthly_totals_in_sql():
    conn = connect(":memory:")
    import_transactions(conn, make_df(SAMPLE), "a.csv")
    rows = conn.execute(
        "SELECT strftime('%Y-%m', date) AS m, SUM(amount) FROM transactions "
        "GROUP BY m ORDER BY m"
    ).fetchall()
    assert rows == [("2026-07", 600.0), ("2026-08", -50.0)]


def test_review_query_returns_only_uncategorized():
    conn = connect(":memory:")
    import_transactions(conn, make_df(SAMPLE), "a.csv")
    rows = conn.execute(
        "SELECT description FROM transactions WHERE category = 'Uncategorized'"
    ).fetchall()
    assert rows == [("Mystery Shop",)]