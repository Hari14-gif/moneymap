from src.analytics import category_changes


def rising_category_insights(df, old_month, new_month, min_pct=20, min_amount=500):
    """Flag categories that rose by both a percent and a rupee threshold."""
    changes = category_changes(df, old_month, new_month)
    insights = []

    for category, row in changes.iterrows():
        old, new, pct = row[old_month], row[new_month], row["change_pct"]

        # Skip: new spending (no percentage), or changes below either threshold
        if pd_isna(pct) or pct <= min_pct or (new - old) < min_amount:
            continue

        caveat = ""
        if category == "Credit Card Payment":
            caveat = "Card payments stand in for card purchases that are not in the data."

        insights.append({
            "title": f"{category} spending increased",
            "observation": f"{category} rose {pct:.1f}% from {old_month} to {new_month}.",
            "evidence": f"₹{old:,.0f} in {old_month}, ₹{new:,.0f} in {new_month}.",
            "caveat": caveat,
        })
    return insights


def pd_isna(x):
    return x != x   # NaN is the only value not equal to itself