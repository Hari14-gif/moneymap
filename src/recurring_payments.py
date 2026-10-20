import pandas as pd

RESULT_COLUMNS = ["count", "typical_amount", "interval", "last_seen", "confidence", "reason"]


def _gap_stats(g):
    """Average days between payments, and how much the gaps vary."""
    gaps = g["date"].sort_values().diff().dt.days.dropna()
    mean = gaps.mean()
    return pd.Series({
        "avg_gap_days": mean,
        "gap_wobble": gaps.std() / mean if mean > 0 else float("nan"),
    })


def _interval_label(days):
    if 27 <= days <= 35:
        return "about monthly"
    if 6 <= days <= 8:
        return "about weekly"
    return f"about every {days:.0f} days"


def find_recurring(df, min_count=3, max_amount_wobble=0.1, max_gap_wobble=0.2):
    """Candidate recurring payments, with a confidence level and the reason."""
    spend = df[(df["amount"] < 0) & (df["category"] != "Internal Transfer")]
    if spend.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    amounts = spend.groupby("description")["amount"].agg(["count", "mean", "std"])
    amounts["amount_wobble"] = amounts["std"] / amounts["mean"].abs()
    gaps = spend.groupby("description")[["date"]].apply(_gap_stats)
    last_seen = spend.groupby("description")["date"].max().rename("last_seen")

    stats = amounts.join(gaps).join(last_seen)
    found = stats[
        (stats["count"] >= min_count)
        & (stats["amount_wobble"] <= max_amount_wobble)
        & (stats["gap_wobble"] <= max_gap_wobble)
    ].copy()

    if found.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    found["typical_amount"] = found["mean"].abs()
    found["interval"] = found["avg_gap_days"].apply(_interval_label)
    found["confidence"] = [
        "High" if (a <= 0.01 and g <= 0.1) else "Medium"
        for a, g in zip(found["amount_wobble"], found["gap_wobble"])
    ]
    found["reason"] = [
        f"{int(c)} payments, amount varies {a * 100:.1f}%, {i}"
        for c, a, i in zip(found["count"], found["amount_wobble"], found["interval"])
    ]

    found["count"] = found["count"].astype(int)
    return found[RESULT_COLUMNS].sort_values(
        ["confidence", "typical_amount"], ascending=[True, False]
    )