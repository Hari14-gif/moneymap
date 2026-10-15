import streamlit as st

from src.data_loader import load_transactions
from src.data_cleaning import clean_transactions
from src.categorization import add_categories
from src.analytics import calculate_summary

st.title("MoneyMap")

# Load -> clean -> categorize
raw = load_transactions("data/sample_transactions.csv")
clean, rejected, summary = clean_transactions(raw)
clean = add_categories(clean)

# Calculate
result = calculate_summary(clean)

# Show 4 numbers side by side
col1, col2, col3, col4 = st.columns(4)
col1.metric("Income", f"₹{result['income']:,.0f}")
col2.metric("Expenses", f"₹{result['expenses']:,.0f}")
col3.metric("Net cash flow", f"₹{result['net_cash_flow']:,.0f}")
col4.metric("Savings rate", f"{result['savings_rate']:.1f}%")