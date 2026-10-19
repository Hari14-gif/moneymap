import streamlit as st
import plotly.express as px
import pandas as pd

from src.data_loader import load_transactions
from src.data_cleaning import clean_transactions
from src.categorization import add_categories
from src.analytics import calculate_summary
from src.analytics import calculate_summary, category_changes, category_shares
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
    