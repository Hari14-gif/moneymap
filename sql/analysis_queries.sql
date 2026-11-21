-- MoneyMap analytical queries (SQLite)
-- Table: transactions(date, description, category, amount)
-- Expenses are negative amounts; internal transfers are excluded everywhere.

-- 1. Spending by category
SELECT category, -SUM(amount) AS total, COUNT(*) AS payments
FROM transactions
WHERE amount < 0 AND category != 'Internal Transfer'
GROUP BY category
ORDER BY total DESC;

-- 2. Monthly income and expenses (refunds reduce expenses, never count as income)
SELECT
    strftime('%Y-%m', date) AS month,
    SUM(CASE WHEN amount > 0 AND category NOT IN ('Internal Transfer', 'Refunds')
             THEN amount ELSE 0 END) AS income,
    -SUM(CASE WHEN amount < 0 AND category != 'Internal Transfer'
              THEN amount ELSE 0 END)
    - SUM(CASE WHEN category = 'Refunds' THEN amount ELSE 0 END) AS expenses
FROM transactions
GROUP BY month
ORDER BY month;

-- 3. Month-over-month change in expenses (LAG looks at the previous month)
WITH monthly AS (
    SELECT
        strftime('%Y-%m', date) AS month,
        -SUM(CASE WHEN amount < 0 AND category != 'Internal Transfer' THEN amount ELSE 0 END)
        - SUM(CASE WHEN category = 'Refunds' THEN amount ELSE 0 END) AS expenses
    FROM transactions
    GROUP BY month
)
SELECT
    month,
    expenses,
    LAG(expenses) OVER (ORDER BY month) AS prev_expenses,
    ROUND(
        (expenses - LAG(expenses) OVER (ORDER BY month)) * 100.0
        / NULLIF(LAG(expenses) OVER (ORDER BY month), 0),
    1) AS change_pct
FROM monthly;

-- 4. Top merchants (share is out of ALL spending, not just the top 5)
SELECT
    description,
    -SUM(amount) AS total,
    COUNT(*) AS payments,
    ROUND(-SUM(amount) * 100.0 /
        (SELECT -SUM(amount) FROM transactions
         WHERE amount < 0 AND category != 'Internal Transfer'), 1) AS share_pct
FROM transactions
WHERE amount < 0 AND category != 'Internal Transfer'
GROUP BY description
HAVING COUNT(*) >= 2
ORDER BY total DESC
LIMIT 5;

-- 5. Transactions that need review
SELECT date, description, amount
FROM transactions
WHERE category = 'Uncategorized';

-- 6. Recurring payment candidates (3+ payments, similar amounts, regular gaps)
WITH spend AS (
    SELECT
        description, date, ABS(amount) AS amt,
        julianday(date) - julianday(
            LAG(date) OVER (PARTITION BY description ORDER BY date)
        ) AS gap
    FROM transactions
    WHERE amount < 0 AND category != 'Internal Transfer'
)
SELECT
    description,
    COUNT(*) AS payments,
    ROUND(AVG(amt)) AS typical_amount,
    ROUND((MAX(amt) - MIN(amt)) * 100.0 / AVG(amt), 1) AS amount_spread_pct,
    ROUND(AVG(gap), 1) AS avg_gap_days,
    MAX(date) AS last_seen
FROM spend
GROUP BY description
HAVING COUNT(*) >= 3
   AND (MAX(amt) - MIN(amt)) / AVG(amt) <= 0.15
   AND MAX(gap) - MIN(gap) <= 7
ORDER BY amount_spread_pct, typical_amount DESC;