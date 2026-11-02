# Rules are checked in order. The first match wins,
# so more specific rules go at the top.
RULES = {
    "refund": "Refunds",
    "credit card payment": "Credit Card Payment",
    "own savings": "Internal Transfer",
    "salary": "Salary",
    "freelance": "Freelance Income",
    "rent": "Housing",
    "swiggy": "Food Delivery",
    "zomato": "Food Delivery",
    "netflix": "Subscriptions",
    "spotify": "Subscriptions",
    "groceries": "Groceries",
    "uber": "Transportation",
    "petrol": "Fuel",
    "electricity": "Utilities",
    "amazon": "Shopping",
    "myntra": "Shopping",
    "udemy": "Education",
    "pvr": "Entertainment",
    "pharmacy": "Healthcare",
    "clinic": "Healthcare",
    "indigo": "Travel",
}


def categorize(description):
    """Suggest a category from keywords. Falls back to Uncategorized."""
    text = str(description).lower()
    for keyword, category in RULES.items():
        if keyword in text:
            return category
    return "Uncategorized"


def add_categories(df):
    """Return a copy of df with a 'category' column."""
    out = df.copy()
    out["category"] = out["description"].apply(categorize)
    return out

def apply_overrides(df, overrides):
    """Corrections win over the automatic categories. Descriptions stay untouched."""
    out = df.copy()
    if overrides:
        corrected = out["description"].map(overrides)
        out["category"] = corrected.fillna(out["category"])
    return out