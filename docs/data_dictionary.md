# Data dictionary

## Input CSV

| Column | Meaning | Notes |
|---|---|---|
| `date` | Transaction date | `YYYY-MM-DD`, `DD/MM/YYYY` or `DD-MM-YYYY` |
| `description` | Merchant or narration | Kept exactly as uploaded (only spaces trimmed) |
| `amount` | Signed amount | Positive = in, negative = out |
| `debit` / `credit` | Alternative to `amount` | `amount = credit - debit` |

Accepted alternative column names: `transaction_date`, `txn date` (date);
`merchant`, `narration`, `particulars`, `details` (description);
`transaction_amount` (amount); `withdrawal(s)` (debit); `deposit(s)` (credit).
Names are matched ignoring capital letters and extra spaces.

## Cleaned dataset (inside the app)

| Column | Type | Meaning |
|---|---|---|
| `date` | date | Parsed transaction date |
| `description` | text | Original description |
| `amount` | number | Signed amount |
| `category` | text | Suggested category, or the user's correction |
| `month` | text | `YYYY-MM`, added for grouping |

## Categories

Refunds, Credit Card Payment, Internal Transfer, Salary, Freelance Income, Housing,
Food Delivery, Subscriptions, Groceries, Transportation, Fuel, Utilities, Shopping,
Education, Entertainment, Healthcare, Travel, Uncategorized.

## Data-quality summary

| Key | Meaning |
|---|---|
| `imported` | Rows in the uploaded file |
| `valid` | Rows kept after cleaning |
| `rejected` | Rows set aside (invalid date or amount) |
| `duplicates_removed` | Exact repeats removed |
| `missing_description` | Rows given "(no description)" |
| `date_format` | The date format that was detected |

## Metrics summary

| Key | Meaning |
|---|---|
| `income` | See methodology, section 5 |
| `expenses` | See methodology, section 5 |
| `net_cash_flow` | Income - expenses |
| `savings_rate` | Percent, or empty when income is 0 |

## Database tables

**import_batches:** `id`, `filename`, `imported_at`.

**transactions:** `id`, `batch_id` (links to import_batches), `date` (text,
`YYYY-MM-DD`), `description`, `category`, `amount`. Unique on
(date, description, amount).

**category_overrides:** `description` (primary key), `category`, `updated_at`.

## Exports (CSV)

- Transactions: `date, description, category, amount` (filtered rows).
- Summary: key metrics plus date range, currency, assumptions and limitations.
- Category report: header notes, then `category, total, payments, share_pct`.
- Insights report: header notes, then `title, observation, evidence, caveat`.