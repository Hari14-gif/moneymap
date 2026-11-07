# MoneyMap

A personal finance analytics app built with Python, Pandas, SQLite and Streamlit.
Upload a bank transactions CSV and MoneyMap cleans it, categorizes it, calculates
financial metrics, and explains what changed, with the evidence and caveats for each observation.

All demo data is synthetic. No real financial data is included in this repository.

## Problem statement

Bank statements are long lists of transactions. They do not show where money
comes from, where it goes, how much is kept, or how habits change over time. Many
simple trackers also count your own transfers, credit card bill payments, and
refunds incorrectly, which makes savings figures misleading.

## Objectives

- Turn raw transactions into trustworthy income, expense, cash flow and savings figures.
- Never hide suspicious data: report what was found and what was done.
- Keep every calculation in tested Python functions, separate from the interface.
- Explain every insight with numbers, a period, and a caveat.

## Features

- CSV upload with validation: empty files, wrong columns, bad dates or amounts, duplicates.
- Bank layouts: separate debit/credit columns and common column names (Narration, Withdrawal, Deposit).
- Dates in `YYYY-MM-DD`, `DD/MM/YYYY` and `DD-MM-YYYY` (slash dates are read day-first).
- Data-quality summary (imported, valid, rejected, duplicates removed). Raw data is kept separate from cleaned data.
- Transparent keyword-based categorization with a priority order and an `Uncategorized` fallback.
- Editable categories: corrections override the automatic suggestion and are saved in SQLite.
- Metrics: income, expenses, net cash flow, savings rate, monthly savings-rate trend.
- Month vs month comparison with explicit zero-baseline handling and an incomplete-month warning.
- Spending concentration and top merchants.
- Rule-based insights (rising spending, new spending), each with evidence and a caveat.
- Recurring payment candidates with a confidence level and the reason for the match.
- Refund matching to the original purchase (matched, ambiguous or unmatched).
- Filters (date range, category) applied once, so every number on the page agrees.
- CSV exports: filtered transactions, summary, category report, insights report. Each states the date range, currency and assumptions.
- SQLite storage with safe repeated imports.

## Technology stack

Python, Pandas, NumPy, Streamlit, Plotly, SQLite, Pytest, Git.

## Architecture

```
app.py                    Streamlit interface only
src/
  data_loader.py          read CSV, map column names, bank layouts
  data_cleaning.py        types, bad rows, dates, duplicates, quality summary
  categorization.py       keyword rules, priority order, user corrections
  analytics.py            metrics, comparisons, merchants, filters, refund matching
  insights.py             rule-based insights with evidence and caveats
  recurring_payments.py   recurring payment candidates
  database.py             SQLite schema, safe imports, saved corrections
  reports.py              CSV exports
tests/                    pytest tests for each module
docs/                     methodology, data dictionary, SQL vs pandas
data/sample_transactions.csv   synthetic demo data
```

Data flow: `CSV -> load -> clean -> categorize -> apply corrections -> filter -> calculate -> dashboard`.

## Installation (Windows)

```powershell
git clone https://github.com/Hari14-gif/moneymap.git
cd moneymap
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

The app starts with the sample data. Use the upload box to load your own CSV.
Your files stay on your computer, and the database `data/moneymap.db` is ignored by git.

## Dataset format

Minimum columns: `date`, `description`, `amount`.

- Positive amount = money in, negative amount = money out.
- Alternatively, separate `debit` and `credit` columns: `amount = credit - debit`.
- See [docs/data_dictionary.md](docs/data_dictionary.md).

## Methodology and metric definitions

Full details: [docs/methodology.md](docs/methodology.md).

- **Income** = positive amounts, excluding internal transfers and refunds.
- **Expenses** = negative amounts, excluding internal transfers, minus refunds.
- **Net cash flow** = income - expenses.
- **Savings rate** = (income - expenses) / income x 100, shown as `n/a` when income is 0.
- Internal transfers are not income or spending. Refunds reduce expenses and are never counted as income.
- Credit card payments are counted as expenses in the sample data, because the card purchases are not in the file (see Known limitations).
- Cash flow is a transaction-based estimate, not a verified bank balance.

## Screenshots

## Testing

```powershell
python -m pytest -v
```

63 tests cover cleaning, categorization and overrides, analytics, insights, recurring
detection, refund matching, reports, the database, and loader errors.

## Known limitations

- Categorization is keyword rules only (no machine learning). Merchant-based categories are suggestions.
- Credit card payments are counted as expenses. If a file includes every card purchase, this would double count; a setting for this exists in the analytics function but not yet in the interface.
- Refund matching uses the first word of the refund description and needs the original purchase to be in the data.
- The duplicate rule (same date, description and amount) would treat two identical purchases on the same day as one.
- Recurring detection needs at least 3 similar payments, so short histories can miss real subscriptions and flag habits (like groceries) by chance.
- Slash dates are assumed day-first.
- The currency is shown as INR and is not yet configurable in the interface.
- The dashboard reads the uploaded CSV directly. SQLite stores categories corrections and supports safe imports, but the dashboard does not yet load from the database.
- No PDF reports, and no bank syncing.

## Future improvements

- Configurable currency and credit card treatment in the interface.
- Load the dashboard from the database.
- Budget targets and what-if analysis.
- Excel (.xlsx) uploads.
- PDF report.