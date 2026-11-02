import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loader import load_transactions
from src.data_cleaning import clean_transactions
from src.categorization import add_categories, apply_overrides, RULES
from src.analytics import (
    calculate_summary,
    category_changes,
    category_shares,
    monthly_summary,
    is_incomplete_last_month,
    top_merchants,
    filter_transactions,
    match_refunds,
)
from src.insights import rising_category_insights, new_spending_insights
from src.recurring_payments import find_recurring
from src.reports import (
    transactions_csv,
    summary_csv,
    category_report_csv,
    insights_report_csv,
)
from src.database import connect, save_override, load_overrides

CATEGORY_CHOICES = sorted(set(RULES.values())) + ["Uncategorized"]

st.title("MoneyMap")

# Load (upload or sample)
uploaded = st.file_uploader("Upload your transactions CSV", type="csv")

try:
    if uploaded is not None:
        raw = load_transactions(uploaded)
    else:
        raw = load_transactions("data/sample_transactions.csv")
        st.caption("Showing sample data. Upload a CSV to use your own.")
except ValueError as e:
    st.error(str(e))
    st.stop()

# Clean -> categorize -> apply saved corrections (corrections win)
clean, rejected, summary = clean_transactions(raw)
clean = add_categories(clean)
db = connect()
clean = apply_overrides(clean, load_overrides(db))

# Data quality (always about the whole file, not the filters)
with st.expander("Data quality"):
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Imported rows", summary["imported"])
    q2.metric("Valid rows", summary["valid"])
    q3.metric("Rejected rows", summary["rejected"])
    q4.metric("Duplicates removed", summary["duplicates_removed"])
    st.caption(f"Date format detected: {summary['date_format']}")

    if summary["rejected"] > 0:
        st.warning("These rows were set aside because the date or amount was invalid:")
        st.dataframe(rejected)

if clean.empty:
    st.error("No valid transactions to show.")
    st.stop()

# Review and fix categories
with st.expander("Review and fix categories"):
    st.caption(
        "Categories are suggestions from keyword rules. "
        "A correction here replaces the suggestion and is remembered."
    )
    needs_review = sorted(clean.loc[clean["category"] == "Uncategorized", "description"].unique())
    st.write(f"{len(needs_review)} description(s) are Uncategorized.")

    others = [d for d in sorted(clean["description"].unique()) if d not in needs_review]
    chosen_desc = st.selectbox("Description", needs_review + others)
    current = clean.loc[clean["description"] == chosen_desc, "category"].iloc[0]
    st.caption(f"Current category: {current}")

    default_idx = CATEGORY_CHOICES.index(current) if current in CATEGORY_CHOICES else 0
    new_cat = st.selectbox("Correct category", CATEGORY_CHOICES, index=default_idx)

    if st.button("Save correction"):
        save_override(db, chosen_desc, new_cat)
        st.rerun()

# Filters (applied ONCE, so every number below agrees)
full = clean
st.sidebar.header("Filters")
min_d = full["date"].min().date()
max_d = full["date"].max().date()

picked = st.sidebar.date_input(
    "Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d
)
if not (isinstance(picked, tuple) and len(picked) == 2):
    st.sidebar.info("Pick an end date to finish the range.")
    st.stop()
start, end = picked

chosen = st.sidebar.multiselect(
    "Categories (empty = all)", sorted(full["category"].unique())
)

clean = filter_transactions(full, start, end, chosen).copy()
if clean.empty:
    st.warning("No transactions match these filters.")
    st.stop()

st.caption(f"Showing {start} to {end} · {len(clean)} transactions · Currency: INR")

# Calculate
result = calculate_summary(clean)

# 4 numbers
col1, col2, col3, col4 = st.columns(4)
col1.metric("Income", f"₹{result['income']:,.0f}")
col2.metric("Expenses", f"₹{result['expenses']:,.0f}")
col3.metric("Net cash flow", f"₹{result['net_cash_flow']:,.0f}")
if result["savings_rate"] is not None:
    col4.metric("Savings rate", f"{result['savings_rate']:.1f}%")
else:
    col4.metric("Savings rate", "n/a")

# Downloads
d1, d2, d3 = st.columns(3)
d1.download_button(
    "Transactions (CSV)",
    transactions_csv(clean),
    file_name="moneymap_transactions.csv",
    mime="text/csv",
)
d2.download_button(
    "Summary (CSV)",
    summary_csv(result, start, end),
    file_name="moneymap_summary.csv",
    mime="text/csv",
)
d3.download_button(
    "Category report (CSV)",
    category_report_csv(clean, start, end),
    file_name="moneymap_category_report.csv",
    mime="text/csv",
)

# Spending by category
spend = clean[(clean["amount"] < 0) & (clean["category"] != "Internal Transfer")]
by_cat = spend.groupby("category")["amount"].sum().abs().sort_values(ascending=False)

fig = px.bar(
    by_cat.reset_index(),
    x="amount",
    y="category",
    orientation="h",
    title="Spending by category",
)
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)

# Monthly income vs expenses
clean["month"] = clean["date"].dt.to_period("M").astype(str)

rows = []
for month, group in clean.groupby("month"):
    r = calculate_summary(group)
    rows.append({"month": month, "income": r["income"], "expenses": r["expenses"]})
monthly = pd.DataFrame(rows)

fig2 = px.bar(
    monthly,
    x="month",
    y=["income", "expenses"],
    barmode="group",
    title="Monthly income vs expenses",
)
st.plotly_chart(fig2, use_container_width=True)

# Concentration
share, top3 = category_shares(clean)
if top3 is not None:
    st.metric("Top 3 categories' share of spending", f"{top3:.1f}%")

# Month vs month
st.subheader("Month vs month")
months = sorted(clean["month"].unique())
last_month_full = full["date"].max().strftime("%Y-%m")

if len(months) < 2:
    st.info("Need at least 2 months in the selected range to compare.")
else:
    c1, c2 = st.columns(2)
    old_m = c1.selectbox("Compare", months, index=len(months) - 2)
    new_m = c2.selectbox("with", months, index=len(months) - 1)

    if new_m == last_month_full and is_incomplete_last_month(full):
        st.warning(
            f"{new_m} may be incomplete: the data ends well before the end of the month. "
            "Changes compared with a full month can look smaller than they really are."
        )

    changes = category_changes(clean, old_m, new_m)

    def label(row):
        if pd.isna(row["change_pct"]):
            return "new" if row[new_m] > 0 else "-"
        return f"{row['change_pct']:+.1f}%"

    changes["change"] = changes.apply(label, axis=1)
    st.dataframe(changes[[old_m, new_m, "change"]])

# Insights
st.subheader("Insights")
if len(months) >= 2:
    found = rising_category_insights(clean, old_m, new_m)
    found += new_spending_insights(clean, old_m, new_m)

    if not found:
        st.write("No notable changes between these months.")
    for item in found:
        st.markdown(f"**{item['title']}**")
        st.write(item["observation"])
        st.caption(f"Evidence: {item['evidence']}")
        if item["caveat"]:
            st.caption(f"Caveat: {item['caveat']}")

    st.download_button(
        "Insights report (CSV)",
        insights_report_csv(found, old_m, new_m, start, end),
        file_name="moneymap_insights.csv",
        mime="text/csv",
    )
else:
    st.write("Select a range with at least 2 months to see insights.")

# Recurring payments
st.subheader("Possible recurring payments")
recurring = find_recurring(clean)
if recurring.empty:
    st.write("No recurring payments found (needs at least 3 similar payments).")
else:
    shown = recurring.copy()
    shown["typical_amount"] = shown["typical_amount"].map(lambda v: f"₹{v:,.0f}")
    shown["last_seen"] = shown["last_seen"].dt.strftime("%Y-%m-%d")
    st.dataframe(shown)
    st.caption(
        "Based on past payments only. This is not a prediction of future payments, "
        "and some habits (like groceries) can look recurring by chance."
    )

# Savings rate trend
st.subheader("Savings rate trend")
trend = monthly_summary(clean)

if len(trend) < 2:
    st.info("Need at least 2 months of data to show a trend.")
else:
    fig3 = px.line(
        trend,
        x="month",
        y="savings_rate",
        markers=True,
        title="Monthly savings rate (%)",
    )
    st.plotly_chart(fig3, use_container_width=True)

    last = trend.iloc[-1]
    if pd.notna(last["savings_rate_change_pts"]):
        st.caption(
            f"Latest month: {last['savings_rate']:.1f}% "
            f"({last['savings_rate_change_pts']:+.1f} percentage points vs the month before). "
            "Based on recorded transactions, not verified bank balances."
        )

# Top merchants
st.subheader("Top merchants by spending")
merchants = top_merchants(clean)

if merchants.empty:
    st.write("No spending to show.")
else:
    fig4 = px.bar(
        merchants.reset_index(),
        x="total",
        y="description",
        orientation="h",
        title="Top 5 merchants",
    )
    fig4.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(
        "Rent and card bill payments are listed as they appear in your data. "
        "Card payments stand in for card purchases that are not recorded."
    )

# Refunds
links = match_refunds(full)
if not links.empty:
    links = links[
        (links["refund_date"] >= pd.Timestamp(start))
        & (links["refund_date"] <= pd.Timestamp(end))
    ]

if not links.empty:
    st.subheader("Refunds")
    shown = links.copy()
    shown["refund_date"] = pd.to_datetime(shown["refund_date"]).dt.strftime("%Y-%m-%d")
    shown["purchase_date"] = pd.to_datetime(shown["purchase_date"]).dt.strftime("%Y-%m-%d").fillna("-")
    st.dataframe(shown)
    st.caption(
        "Refunds reduce expenses; they are not counted as income. "
        "A refund is linked to the latest earlier purchase from the same merchant that is at least as large. "
        "'ambiguous' means several purchases fit, and 'unmatched' means none did, so please review."
    )    