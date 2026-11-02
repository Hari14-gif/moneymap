import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES import_batches(id),
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Uncategorized',
    amount REAL NOT NULL,
    UNIQUE (date, description, amount)
);

CREATE TABLE IF NOT EXISTS category_overrides (
    description TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
"""


def connect(path="data/moneymap.db"):
    """Open the database (creating the tables on first use)."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def import_transactions(conn, df, filename):
    """Save cleaned transactions. Repeats are skipped, so importing twice is safe."""
    cur = conn.execute("INSERT INTO import_batches (filename) VALUES (?)", (filename,))
    batch_id = cur.lastrowid

    rows = [
        (batch_id, d.strftime("%Y-%m-%d"), desc, cat, float(amt))
        for d, desc, cat, amt in zip(
            df["date"], df["description"], df["category"], df["amount"]
        )
    ]

    cur = conn.executemany(
        "INSERT OR IGNORE INTO transactions "
        "(batch_id, date, description, category, amount) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()

    inserted = cur.rowcount
    return {"batch_id": batch_id, "inserted": inserted, "skipped": len(rows) - inserted}


def save_override(conn, description, category):
    """Remember a correction. Saving the same description again replaces the old one."""
    conn.execute(
        "INSERT INTO category_overrides (description, category) VALUES (?, ?) "
        "ON CONFLICT(description) DO UPDATE SET "
        "category = excluded.category, updated_at = CURRENT_TIMESTAMP",
        (description, category),
    )
    conn.commit()


def load_overrides(conn):
    """All saved corrections as a {description: category} dictionary."""
    rows = conn.execute("SELECT description, category FROM category_overrides").fetchall()
    return dict(rows)