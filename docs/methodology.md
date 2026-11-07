# Methodology

How MoneyMap turns raw transactions into numbers, and the assumptions behind them.

## 1. Sign convention

- Positive amount = money in. Negative amount = money out.
- For files with separate `debit` and `credit` columns: `amount = credit - debit`.
  A blank debit or credit cell counts as 0. A non-numeric value (like "abc") is NOT
  turned into 0; it stays empty so the cleaning step rejects it and reports it.

## 2. Data-cleaning rules

Applied in this order. The original upload is never changed; cleaning works on a copy.

1. Descriptions are trimmed. Dates are parsed with exact formats (`YYYY-MM-DD`,
   `DD/MM/YYYY`, `DD-MM-YYYY`); the format that parses the most rows is used and
   reported. Slash dates are read day-first. Amounts are converted to numbers.
2. Rows with an invalid date or amount are rejected. They are kept in a separate
   table and shown to the user, never silently dropped.
3. A missing description is replaced with "(no description)"; the row is kept.
4. Exact duplicates (same date, description and amount) are removed. The first copy
   is kept and the number removed is reported.
5. Rows are sorted by date.

The data-quality summary reports: imported, valid, rejected, duplicates removed,
missing descriptions, and the detected date format.

Not implemented yet: flagging unusually large transactions, and detecting
inconsistent signs.

## 3. Categorization

- A description is lowercased and checked against keyword rules in a fixed order.
  The first matching rule wins, so specific rules (like "refund") come before
  general ones (like "amazon"). No match gives `Uncategorized`.
- This is a keyword rule engine, not machine learning. Categories are suggestions.
- A user correction is stored per exact description and overrides the suggestion.
  A correction applies to every transaction with that description. Original
  descriptions are never changed.
- Keywords match anywhere inside the text, so a short keyword can match an
  unrelated word. Review `Uncategorized` and surprising categories.

## 4. Transfers, refunds and credit card payments

- **Internal transfers** are excluded from both income and expenses. Moving money
  between your own accounts is not earning or spending.
- **Refunds** are never counted as income. They reduce expenses instead.
- **Refund matching:** a refund is linked to the latest earlier purchase from the
  same merchant (first word of the refund description) that is at least as large
  as the refund. One candidate = `matched`. Several = `ambiguous` (latest linked,
  flagged for review). None = `unmatched`.
- **Credit card payments** are counted as expenses by default, because in the
  sample data the card purchases are not in the file and the payment is the only
  record of that spending. If a file contains every card purchase, counting the
  payments as well would double count. The analytics function has a setting
  (`count_card_payments`) for this; it is not yet in the interface.

## 5. Metric definitions

```
Income        = sum of positive amounts, excluding internal transfers and refunds
Expenses      = sum of negative amounts (as a positive number), excluding internal
                transfers, minus refunds
Net cash flow = Income - Expenses
Savings rate  = (Income - Expenses) / Income x 100
```

- The savings rate is shown as `n/a` when income is 0 (no division by zero).
- It can be negative when expenses exceed income.
- Changes in a rate are reported in percentage points, not relative percent.
- Everything is a transaction-based estimate. It is not a verified bank balance.

## 6. Period comparisons

- Category spending is compared between two months chosen by the user.
- `change % = (new - old) / old x 100`. When `old` is 0 there is no percentage;
  the app shows "new" instead of infinity.
- The category comparison table does not net refunds. Refunds appear in the
  summary expenses figure.
- Incomplete month warning: if the last transaction in the data is more than 5 days
  before the end of its month, that month is flagged as possibly incomplete. The
  warning appears only when comparing against that latest month. The 5 days is a
  judgment call, not a rule.

## 7. Insights

- **Rising spending:** a category rose by more than 20% AND by at least 500 rupees.
- **New spending:** a category had no spending in the earlier month and at least
  1,000 rupees in the later one.
- Thresholds are function settings (not yet in the interface).
- Each insight has a title, an observation, numeric evidence, and a caveat.
  Credit card payments carry a caveat that they stand in for unseen purchases;
  new spending carries a caveat that it may be a one-off.

Limitations: insights describe what changed, not why. They use only two months at a
time, can miss slow trends, and thresholds are judgment calls. A percentage rise on
a small amount is filtered out by the rupee threshold on purpose.

## 8. Recurring payment detection

Looks at expenses (internal transfers excluded), grouped by exact description. A
description is a candidate when ALL of these hold:

- at least 3 payments,
- amount wobble (standard deviation / average amount) of 10% or less,
- gap wobble (variation of the days between payments / average gap) of 20% or less.

Confidence is **High** when the amount wobble is 1% or less and the gap wobble is
10% or less (a fixed amount on regular dates, like a subscription or rent),
otherwise **Medium**. Each candidate shows its reason.

Limitations: it shows what happened in the past, not a prediction. With only a few
months of data, regular habits (groceries, petrol) can look recurring. It matches
exact descriptions, so a merchant whose description changes each month is missed.

## 9. Database (SQLite)

- Tables: `import_batches`, `transactions`, `category_overrides`.
- `UNIQUE (date, description, amount)` makes repeated imports safe: importing the
  same file twice inserts nothing. Two identical purchases on the same day count as
  one (a documented trade-off).
- SQL and pandas split of responsibilities: see `docs/sql_vs_pandas.md`.