# SQL vs Pandas in MoneyMap

## What SQL (SQLite) does
- **Stores** the cleaned transactions between sessions (`import_batches`, `transactions`).
- **Protects the data:** the UNIQUE rule stops the same transaction being saved twice,
  and the foreign key links every transaction to the file it came from.
- **Answers set-based questions** on the stored data:
  monthly totals, spending by category, top merchants,
  month-over-month change (LAG), transactions needing review, recurring candidates.

## What Pandas does
- **Reads and cleans** the uploaded CSV (types, bad rows, dates, duplicates)
  before anything is saved.
- **Applies business rules** that are easier to test in Python:
  categorization, savings rate, insights, confidence levels for recurring payments.
- **Feeds the charts** (Plotly and Streamlit work directly with DataFrames).

## Why both?
Cleaning and rules need to be tested with small tables in Python.
Storage, de-duplication and repeatable reports belong in the database.
The SQL queries are written to match the pandas results (checked by hand on the sample data).

## Known differences
- Recurring detection: pandas uses standard deviation ("wobble"),
  SQLite uses (max - min) / average ("spread"). Thresholds are not identical.
- The duplicate rule (same date, description and amount) would treat two identical
  purchases on the same day as one. Documented trade-off.