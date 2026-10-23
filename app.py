import streamlit as st
import plotly.express as px
import pandas as pd

from src.data_loader import load_transactions
from src.data_cleaning import clean_transactions
from src.categorization import add_categories
from src.analytics import calculate_summary
from src.analytics import calculate_summary, category_changes, category_shares, monthly_summary
from src.insights import rising_category_insights, new_spending_insights
from src.recurring_payments import find_recurring

st.title("MoneyMap")

# Load -> clean -> categorize
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
clean, rejected, summary = clean_transactions(raw)
clean = add_categories(clean)

# Data quality
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

# Calculate
result = calculate_summary(clean)

# 4 numbers
col1, col2, col3, col4 = st.columns(4)
col1.metric("Income", f"₹{result['income']:,.0f}")
col2.metric("Expenses", f"₹{result['expenses']:,.0f}")
col3.metric("Net cash flow", f"₹{result['net_cash_flow']:,.0f}")
col4.metric("Savings rate", f"{result['savings_rate']:.1f}%")

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
months = sorted(clean["date"].dt.to_period("M").astype(str).unique())

if len(months) < 2:
    st.info("Need at least 2 months of data to compare.")
else:
    c1, c2 = st.columns(2)
    old_m = c1.selectbox("Compare", months, index=len(months) - 2)
    new_m = c2.selectbox("with", months, index=len(months) - 1)

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