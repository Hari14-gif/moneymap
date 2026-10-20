from src.analytics import category_changes


def _is_nan(x):
    return x != x   # NaN is the only value not equal to itself


def rising_category_insights(df, old_month, new_month, min_pct=20, min_amount=500):
    """Flag categories that rose by both a percent and a rupee threshold."""
    changes = category_changes(df, old_month, new_month)
    insights = []

    for category, row in changes.iterrows():
        old, new, pct = row[old_month], row[new_month], row["change_pct"]

        # Skip: new spending (no percentage), or changes below either threshold
        if _is_nan(pct) or pct <= min_pct or (new - old) < min_amount:
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


def new_spending_insights(df, old_month, new_month, min_amount=1000):
    """Flag categories with no spending in the old month and a meaningful amount in the new one."""
    changes = category_changes(df, old_month, new_month)
    insights = []

    for category, row in changes.iterrows():
        old, new = row[old_month], row[new_month]

        if old == 0 and new >= min_amount:
            insights.append({
                "title": f"New spending in {category}",
                "observation": f"{category} had no spending in {old_month} but appears in {new_month}.",
                "evidence": f"₹0 in {old_month}, ₹{new:,.0f} in {new_month}.",
                "caveat": "This may be a one-off purchase, not a new habit.",
            })
    return insights